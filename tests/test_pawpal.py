import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


class TestTaskCompletion:
    """Test that task completion tracking works correctly."""
    
    def test_mark_complete_changes_status(self):
        """Verify that calling mark_complete() changes the task's completed status."""
        task = Task(
            title="Feed the dog",
            duration_minutes=15,
            priority="high",
            description="Morning meal"
        )
        
        # Initially, the task should be incomplete
        assert task.completed is False, "Task should start as incomplete"
        
        # Mark it complete
        task.mark_complete()
        
        # Now it should be marked complete
        assert task.completed is True, "Task should be marked as complete after calling mark_complete()"
    
    def test_reset_completion_clears_status(self):
        """Verify that reset_completion() clears the completed status."""
        task = Task(
            title="Walk the dog",
            duration_minutes=30,
            priority="high"
        )
        
        # Mark complete, then reset
        task.mark_complete()
        assert task.completed is True
        
        task.reset_completion()
        
        # Should now be incomplete again
        assert task.completed is False, "Task should be incomplete after reset_completion()"


class TestTaskAddition:
    """Test that adding and managing tasks on pets works correctly."""
    
    def test_adding_task_increases_pet_task_count(self):
        """Verify that adding a task to a Pet increases that pet's task count."""
        pet = Pet(name="Buddy", species="dog", age=5)
        
        # Initially, the pet should have no tasks
        assert len(pet.get_tasks()) == 0, "Pet should start with no tasks"
        
        # Add a task
        task = Task(
            title="Feed the dog",
            duration_minutes=15,
            priority="high",
            required=True
        )
        pet.add_task(task)
        
        # Now the pet should have one task
        assert len(pet.get_tasks()) == 1, "Pet should have 1 task after adding one"
        
        # Add another task
        task2 = Task(
            title="Walk the dog",
            duration_minutes=30,
            priority="high"
        )
        pet.add_task(task2)
        
        # Now the pet should have two tasks
        assert len(pet.get_tasks()) == 2, "Pet should have 2 tasks after adding two"
    
    def test_removing_task_decreases_pet_task_count(self):
        """Verify that removing a task decreases the task count."""
        pet = Pet(name="Whiskers", species="cat", age=3)
        
        # Add two tasks
        task1 = Task(title="Feed the cat", duration_minutes=10, priority="high", required=True)
        task2 = Task(title="Play with the cat", duration_minutes=20, priority="medium")
        
        pet.add_task(task1)
        pet.add_task(task2)
        
        assert len(pet.get_tasks()) == 2
        
        # Remove the first task
        pet.remove_task("Feed the cat")
        
        # Should now have only one task
        assert len(pet.get_tasks()) == 1, "Pet should have 1 task after removing one"
        
        # The remaining task should be the second one
        assert pet.get_tasks()[0].title == "Play with the cat"


class TestRecurringTaskCompletion:
    """Test recurring task generation after completion."""

    def test_daily_task_creates_next_day_instance(self):
        scheduler = Scheduler()
        dog = Pet(name="Buddy", species="dog", age=5)
        today = date(2026, 3, 29)

        daily_task = Task(
            title="Feed Buddy",
            duration_minutes=15,
            priority="high",
            frequency="daily",
            due_date=today,
        )
        dog.add_task(daily_task)

        next_task = scheduler.mark_task_complete(dog, daily_task)

        assert daily_task.completed is True
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False
        assert len(dog.get_tasks()) == 2

    def test_weekly_task_creates_next_week_instance(self):
        scheduler = Scheduler()
        cat = Pet(name="Whiskers", species="cat", age=3)
        today = date(2026, 3, 29)

        weekly_task = Task(
            title="Deep clean litter box",
            duration_minutes=20,
            priority="medium",
            frequency="weekly",
            due_date=today,
        )
        cat.add_task(weekly_task)

        next_task = scheduler.mark_task_complete(cat, weekly_task)

        assert weekly_task.completed is True
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)
        assert next_task.completed is False
        assert len(cat.get_tasks()) == 2

    def test_non_recurring_task_does_not_create_next_instance(self):
        scheduler = Scheduler()
        dog = Pet(name="Buddy", species="dog", age=5)

        one_time_task = Task(
            title="Vet appointment",
            duration_minutes=45,
            priority="high",
            frequency="once",
        )
        dog.add_task(one_time_task)

        next_task = scheduler.mark_task_complete(dog, one_time_task)

        assert one_time_task.completed is True
        assert next_task is None
        assert len(dog.get_tasks()) == 1


class TestSorting:
    """Test chronological task sorting behavior."""

    def test_sorting_returns_tasks_in_chronological_order(self):
        scheduler = Scheduler()

        tasks = [
            Task(title="Evening walk", duration_minutes=30, priority="medium", preferred_time="18:00"),
            Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="07:00"),
            Task(title="Medication", duration_minutes=5, priority="high", preferred_time="08:30"),
        ]

        sorted_tasks = scheduler.sort_by_time(tasks)

        assert [task.title for task in sorted_tasks] == ["Breakfast", "Medication", "Evening walk"]

    def test_sorting_puts_invalid_or_empty_times_last(self):
        scheduler = Scheduler()

        tasks = [
            Task(title="No time", duration_minutes=10, priority="low", preferred_time=""),
            Task(title="Bad format", duration_minutes=10, priority="low", preferred_time="7-30"),
            Task(title="Valid early", duration_minutes=10, priority="high", preferred_time="06:45"),
            Task(title="Valid later", duration_minutes=10, priority="medium", preferred_time="09:00"),
        ]

        sorted_tasks = scheduler.sort_by_time(tasks)

        assert [task.title for task in sorted_tasks[:2]] == ["Valid early", "Valid later"]
        assert set(task.title for task in sorted_tasks[2:]) == {"No time", "Bad format"}


class TestConflictDetection:
    """Test lightweight time conflict warning behavior."""

    def test_detects_same_pet_conflict(self):
        scheduler = Scheduler()
        owner = Owner(name="Alice", available_minutes=120)
        dog = Pet(name="Buddy", species="dog", age=5)

        dog.add_task(Task(title="Walk", duration_minutes=20, priority="high", preferred_time="07:00"))
        dog.add_task(Task(title="Brush", duration_minutes=10, priority="low", preferred_time="07:00"))
        owner.add_pet(dog)

        warnings = scheduler.detect_time_conflicts(owner)

        assert len(warnings) == 1
        assert "same pet" in warnings[0]
        assert "07:00" in warnings[0]

    def test_detects_different_pet_conflict(self):
        scheduler = Scheduler()
        owner = Owner(name="Alice", available_minutes=120)
        dog = Pet(name="Buddy", species="dog", age=5)
        cat = Pet(name="Whiskers", species="cat", age=3)

        dog.add_task(Task(title="Feed dog", duration_minutes=15, priority="high", preferred_time="08:30"))
        cat.add_task(Task(title="Clean litter", duration_minutes=10, priority="medium", preferred_time="08:30"))
        owner.add_pet(dog)
        owner.add_pet(cat)

        warnings = scheduler.detect_time_conflicts(owner)

        assert len(warnings) == 1
        assert "different pets" in warnings[0]
        assert "08:30" in warnings[0]

    def test_no_conflict_when_times_are_unique(self):
        scheduler = Scheduler()
        owner = Owner(name="Alice", available_minutes=120)
        dog = Pet(name="Buddy", species="dog", age=5)

        dog.add_task(Task(title="Walk", duration_minutes=20, priority="high", preferred_time="07:00"))
        dog.add_task(Task(title="Feed", duration_minutes=10, priority="high", preferred_time="08:00"))
        owner.add_pet(dog)

        warnings = scheduler.detect_time_conflicts(owner)

        assert warnings == []


class TestAIAssistedPlanning:
    """Test AI-assisted retrieval ranking and guardrail fallback behavior."""

    def test_ai_planning_boosts_medication_task_priority(self):
        scheduler = Scheduler()
        owner = Owner(name="Ava", available_minutes=60)
        dog = Pet(name="Milo", species="dog", age=4)

        dog.add_task(
            Task(
                title="Evening play",
                duration_minutes=20,
                priority="medium",
                description="Play fetch in the yard",
            )
        )
        dog.add_task(
            Task(
                title="Give medication",
                duration_minutes=5,
                priority="low",
                description="Administer pill with snack",
            )
        )
        owner.add_pet(dog)

        plan = scheduler.build_ai_daily_plan(owner)

        assert plan[0].title == "Give medication"

    def test_ai_planning_falls_back_when_guardrails_fail(self):
        scheduler = Scheduler()
        owner = Owner(name="Ava", available_minutes=60)
        cat = Pet(name="Luna", species="cat", age=2)

        cat.add_task(
            Task(
                title="Feed Luna",
                duration_minutes=10,
                priority="urgent",
                preferred_time="25:99",
                required=True,
            )
        )
        owner.add_pet(cat)

        scheduler.build_ai_daily_plan(owner)
        metadata = scheduler.get_last_plan_metadata()

        assert metadata["fallback_used"] is True
        assert metadata["guardrail_ok"] is False
        assert any("Invalid priority" in issue for issue in metadata["guardrail_issues"])
