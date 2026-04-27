from __future__ import annotations

from datetime import date, timedelta
from dataclasses import dataclass, field
import json
import logging
import re
from typing import Dict, List, Optional, Tuple


logger = logging.getLogger("pawpal.scheduler")


@dataclass
class KnowledgeItem:
    species: str
    keywords: List[str]
    guidance: str
    urgency_boost: int


class CareKnowledgeBase:
    """Small retrieval corpus used to augment plan ranking decisions."""

    def __init__(self) -> None:
        self.items: List[KnowledgeItem] = [
            KnowledgeItem(
                species="dog",
                keywords=["medication", "pill", "dose", "medicine"],
                guidance="Medication timing should be consistent and not skipped.",
                urgency_boost=70,
            ),
            KnowledgeItem(
                species="cat",
                keywords=["litter", "box", "clean"],
                guidance="Litter maintenance helps prevent stress and hygiene issues.",
                urgency_boost=25,
            ),
            KnowledgeItem(
                species="all",
                keywords=["feed", "meal", "food", "breakfast", "dinner"],
                guidance="Feeding tasks are routine anchors and should happen on time.",
                urgency_boost=30,
            ),
            KnowledgeItem(
                species="all",
                keywords=["walk", "exercise", "play"],
                guidance="Exercise tasks support behavior and long-term health.",
                urgency_boost=15,
            ),
            KnowledgeItem(
                species="all",
                keywords=["groom", "brush", "bath", "nail"],
                guidance="Grooming reduces discomfort and catches early warning signs.",
                urgency_boost=10,
            ),
        ]

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def retrieve(self, task: Task, species: str, top_k: int = 2) -> List[KnowledgeItem]:
        """Return the most relevant knowledge items for this task and species."""
        query_tokens = set(
            self._tokenize(
                f"{task.title} {task.description} {task.priority} {task.preferred_time}"
            )
        )
        if not query_tokens:
            return []

        scored_matches: List[Tuple[KnowledgeItem, int]] = []
        for item in self.items:
            if item.species not in ("all", species.lower()):
                continue

            overlap = len(query_tokens.intersection(set(item.keywords)))
            if overlap == 0:
                continue

            scored_matches.append((item, overlap))

        scored_matches.sort(key=lambda pair: pair[1], reverse=True)
        return [item for item, _score in scored_matches[:top_k]]


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    description: str = ""
    preferred_time: str = ""
    frequency: str = "daily"
    required: bool = False
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def is_high_priority(self) -> bool:
        """Return True when the task priority is high."""
        return self.priority.lower() == "high"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reset_completion(self) -> None:
        """Reset completion status."""
        self.completed = False

    def is_recurring(self) -> bool:
        """Return True when task frequency is a supported recurring type."""
        return self.frequency.lower() in ("daily", "weekly")

    def create_next_instance(self) -> Optional[Task]:
        """Create the next due task when frequency is daily or weekly.

        Returns None for non-recurring tasks.
        """
        normalized_frequency = self.frequency.lower()
        if normalized_frequency == "daily":
            next_due_date = self.due_date + timedelta(days=1)
        elif normalized_frequency == "weekly":
            next_due_date = self.due_date + timedelta(weeks=1)
        else:
            return None

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            description=self.description,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            required=self.required,
            completed=False,
            due_date=next_due_date,
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> None:
        """Remove a task by title from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.title != task_title]

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_incomplete_tasks(self) -> List[Task]:
        """Return only incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_preference(self, pref: str) -> None:
        """Add a planning preference for this owner."""
        if pref not in self.preferences:
            self.preferences.append(pref)

    def update_available_minutes(self, minutes: int) -> None:
        """Update daily available minutes for planning."""
        self.available_minutes = max(0, minutes)

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet profile to this owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet profile by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_incomplete_tasks(self) -> List[Task]:
        """Retrieve all incomplete tasks from all pets owned by this owner."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_incomplete_tasks())
        return all_tasks

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from all pets owned by this owner."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def get_pets(self) -> List[Pet]:
        """Return list of all pets owned by this owner."""
        return self.pets


class Scheduler:
    def __init__(self, knowledge_base: Optional[CareKnowledgeBase] = None) -> None:
        self.knowledge_base = knowledge_base or CareKnowledgeBase()
        self._last_plan_metadata: Dict[str, object] = {}

    def get_all_tasks_for_owner(self, owner: Owner) -> List[Task]:
        """Helper: query owner for all tasks across all owned pets."""
        return owner.get_all_incomplete_tasks()

    def build_daily_plan(self, owner: Owner, pet: Pet = None) -> List[Task]:
        """Build an ordered daily plan ranked by priority and owner constraints."""
        if pet:
            tasks = pet.get_incomplete_tasks()
        else:
            tasks = self.get_all_tasks_for_owner(owner)

        # Rank tasks and return ordered plan
        plan = self.rank_tasks(tasks, owner)
        self._last_plan_metadata = {
            "mode": "rule_based",
            "guardrail_ok": True,
            "guardrail_issues": [],
            "fallback_used": False,
            "rationale": {},
        }
        return plan

    def build_ai_daily_plan(self, owner: Owner, pet: Pet = None) -> List[Task]:
        """Build a plan using retrieval-augmented scoring plus guardrails."""
        if pet:
            tasks = pet.get_incomplete_tasks()
            task_species = {id(task): pet.species for task in tasks}
        else:
            tasks = self.get_all_tasks_for_owner(owner)
            task_species = {}
            for owner_pet in owner.get_pets():
                for task in owner_pet.get_incomplete_tasks():
                    task_species[id(task)] = owner_pet.species

        if not tasks:
            self._last_plan_metadata = {
                "mode": "ai_assisted",
                "guardrail_ok": True,
                "guardrail_issues": [],
                "fallback_used": False,
                "rationale": {},
            }
            return []

        scored_tasks: List[Tuple[Task, int, List[KnowledgeItem]]] = []
        rationale: Dict[str, List[str]] = {}
        for task in tasks:
            species = task_species.get(id(task), "all")
            retrieved = self.knowledge_base.retrieve(task, species)
            retrieval_boost = sum(item.urgency_boost for item in retrieved)
            total_score = self.score_task(task, owner) + retrieval_boost

            rationale[task.title] = [item.guidance for item in retrieved]
            scored_tasks.append((task, total_score, retrieved))

        scored_tasks.sort(key=lambda row: row[1], reverse=True)
        ai_ranked_plan = [task for task, _score, _retrieved in scored_tasks]

        guardrail_ok, guardrail_issues = self.validate_plan(ai_ranked_plan, tasks)
        fallback_used = False
        final_plan = ai_ranked_plan
        if not guardrail_ok:
            fallback_used = True
            final_plan = self.rank_tasks(tasks, owner)

        self._last_plan_metadata = {
            "mode": "ai_assisted",
            "guardrail_ok": guardrail_ok,
            "guardrail_issues": guardrail_issues,
            "fallback_used": fallback_used,
            "rationale": rationale,
        }

        logger.info(
            json.dumps(
                {
                    "event": "plan_generated",
                    "mode": "ai_assisted",
                    "task_count": len(tasks),
                    "owner_available_minutes": owner.available_minutes,
                    "guardrail_ok": guardrail_ok,
                    "fallback_used": fallback_used,
                    "guardrail_issues": guardrail_issues,
                }
            )
        )

        return final_plan

    def validate_plan(self, plan: List[Task], source_tasks: List[Task]) -> Tuple[bool, List[str]]:
        """Validate plan output and return guardrail status and issue list."""
        issues: List[str] = []
        allowed_priorities = {"low", "medium", "high"}

        seen_task_ids = set()
        for task in plan:
            task_id = id(task)
            if task_id in seen_task_ids:
                issues.append(f"Duplicate task detected in plan: {task.title}")
            seen_task_ids.add(task_id)

            if task.duration_minutes <= 0:
                issues.append(f"Non-positive duration for task: {task.title}")

            if task.priority.lower() not in allowed_priorities:
                issues.append(f"Invalid priority for task: {task.title}")

            if task.preferred_time and self._time_sort_key(task.preferred_time)[0] == 1:
                issues.append(f"Invalid preferred time for task: {task.title}")

        source_required_ids = {
            id(task) for task in source_tasks if task.required and not task.completed
        }
        planned_ids = {id(task) for task in plan}
        if not source_required_ids.issubset(planned_ids):
            issues.append("One or more required tasks are missing from the plan.")

        return (len(issues) == 0, issues)

    def get_last_plan_metadata(self) -> Dict[str, object]:
        """Expose plan metadata for UI display and reliability tests."""
        return self._last_plan_metadata

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """Mark a task complete and attach the next recurring instance to a pet.

        Returns the newly created task when recurrence applies, otherwise None.
        """
        if task.completed:
            return None

        task.mark_complete()
        next_task = task.create_next_instance()

        if next_task:
            pet.add_task(next_task)

        return next_task

    def _time_sort_key(self, time_str: str) -> Tuple[int, int, int]:
        """Return sortable tuple for HH:MM. Invalid or empty times are sorted last."""
        if not time_str:
            return (1, 99, 99)

        parts = time_str.split(":")
        if len(parts) != 2:
            return (1, 99, 99)

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError:
            return (1, 99, 99)

        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return (1, 99, 99)

        return (0, hour, minute)

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by HH:MM preferred_time using a lambda key helper.

        Tasks without valid times are placed at the end.
        """
        return sorted(tasks, key=lambda task: self._time_sort_key(task.preferred_time))

    def detect_time_conflicts(
        self,
        owner: Owner,
        include_completed: bool = False,
    ) -> List[str]:
        """Return warning messages for exact same-time task conflicts.

        This is a lightweight checker that compares preferred_time equality
        and does not calculate overlapping durations.
        """
        tasks_by_time: Dict[str, List[Tuple[str, str]]] = {}

        for pet in owner.get_pets():
            for task in pet.get_tasks():
                if not include_completed and task.completed:
                    continue

                if self._time_sort_key(task.preferred_time)[0] == 1:
                    continue

                tasks_by_time.setdefault(task.preferred_time, []).append((pet.name, task.title))

        warnings: List[str] = []
        for preferred_time in sorted(tasks_by_time.keys()):
            scheduled_items = tasks_by_time[preferred_time]
            if len(scheduled_items) < 2:
                continue

            for i in range(len(scheduled_items)):
                for j in range(i + 1, len(scheduled_items)):
                    pet_a, task_a = scheduled_items[i]
                    pet_b, task_b = scheduled_items[j]
                    conflict_scope = "same pet" if pet_a == pet_b else "different pets"
                    warnings.append(
                        f"Warning: Conflict at {preferred_time} ({conflict_scope}) between "
                        f"{pet_a} - {task_a} and {pet_b} - {task_b}."
                    )

        return warnings

    def filter_tasks(
        self,
        owner: Owner,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by completion status and/or case-insensitive pet name."""
        filtered_tasks: List[Task] = []
        requested_pet = pet_name.lower() if pet_name else None

        for pet in owner.get_pets():
            if requested_pet and pet.name.lower() != requested_pet:
                continue

            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                filtered_tasks.append(task)

        return filtered_tasks

    def rank_tasks(self, tasks: List[Task], owner: Owner) -> List[Task]:
        """Return tasks ordered by score so scoring/sorting is centralized."""
        if not tasks:
            return []
        
        # Score each task and sort by score descending
        scored_tasks = [(task, self.score_task(task, owner)) for task in tasks]
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        return [task for task, score in scored_tasks]

    def score_task(self, task: Task, owner: Owner) -> int:
        """Calculate a ranking score based on priority, required status, and available time."""
        score = 0
        
        # Priority-based scoring
        if task.is_high_priority():
            score += 100
        elif task.priority.lower() == "medium":
            score += 50
        else:
            score += 10
        
        # Required tasks get a bonus
        if task.required:
            score += 50
        
        # Prefer tasks that fit available time
        if task.duration_minutes <= owner.available_minutes:
            score += 20
        
        return score

    def explain_plan(self, plan: List[Task]) -> str:
        """Return a human-readable explanation for the generated plan."""
        if not plan:
            return "No tasks scheduled for today."
        
        explanation = "Today's Plan:\n" + "-" * 40 + "\n"
        total_minutes = 0
        
        for i, task in enumerate(plan, 1):
            priority_str = task.priority.upper() if task.priority else "NORMAL"
            explanation += f"{i}. {task.title}\n"
            explanation += f"   Duration: {task.duration_minutes} min | Priority: {priority_str}\n"
            if task.description:
                explanation += f"   {task.description}\n"
            total_minutes += task.duration_minutes
        
        explanation += "-" * 40 + "\n"
        explanation += f"Total Time: {total_minutes} minutes\n"
        return explanation

    def explain_ai_plan(self, plan: List[Task]) -> str:
        """Return a readable explanation that includes retrieved knowledge rationale."""
        if not plan:
            return "No tasks scheduled for today."

        metadata = self.get_last_plan_metadata()
        rationale = metadata.get("rationale", {}) if isinstance(metadata, dict) else {}
        explanation = "AI-Assisted Plan:\n" + "-" * 40 + "\n"
        total_minutes = 0

        for i, task in enumerate(plan, 1):
            explanation += f"{i}. {task.title} ({task.duration_minutes} min)\n"
            notes = rationale.get(task.title, []) if isinstance(rationale, dict) else []
            if notes:
                explanation += f"   Why now: {notes[0]}\n"
            total_minutes += task.duration_minutes

        explanation += "-" * 40 + "\n"
        explanation += f"Total Time: {total_minutes} minutes\n"
        return explanation
