# PawPal+

PawPal+ is a Streamlit-based pet care planning assistant. It helps a pet owner organize daily care tasks across multiple pets, prioritize what matters most, and spot schedule conflicts early.

## Features

- Multi-pet management: Create an owner profile and add multiple pets, each with its own task list.
- Task management: Add care tasks with duration, priority, description, required flag, and optional preferred time (`HH:MM`).
- Priority-based daily planning: `Scheduler.build_daily_plan()` uses task scoring to rank incomplete tasks.
- Scoring algorithm: `Scheduler.score_task()` increases score for high priority tasks, required tasks, and tasks that fit the owner's available minutes.
- Sorting by time: `Scheduler.sort_by_time()` orders tasks chronologically using valid `HH:MM` values and pushes invalid/empty times to the end.
- Filtering views: `Scheduler.filter_tasks()` filters tasks by completion status and optional pet name.
- Conflict warnings: `Scheduler.detect_time_conflicts()` flags exact same-time collisions (same pet or across pets).
- Daily/weekly recurrence: Completing recurring tasks through `Scheduler.mark_task_complete()` creates the next task instance via `Task.create_next_instance()`.
- Plan explanation: `Scheduler.explain_plan()` returns a readable summary with order, duration, and total planned minutes.
- Professional UI feedback: Streamlit status components (`st.success`, `st.warning`, `st.info`) and `st.table` are used for clear visual output.

## Project Structure

- [app.py](app.py): Streamlit UI and interactive task/schedule workflow.
- [pawpal_system.py](pawpal_system.py): Core domain models and scheduler logic.
- [tests/test_pawpal.py](tests/test_pawpal.py): Unit tests for scheduling behaviors.
- [main.py](main.py): CLI demonstration script for scheduler behavior.
- [uml_final.mmd](uml_final.mmd): Final Mermaid UML source.
- [uml_final.png](uml_final.png): Exported UML diagram image.

## Getting Started

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

### 3. Run tests

```bash
python -m pytest -q
```

## How Scheduling Works

1. Owner and pet data are collected from the UI.
2. Incomplete tasks are gathered across pets.
3. Tasks are ranked by a score based on priority, required status, and time-fit.
4. The generated plan is displayed in table form and explained in text.
5. Additional views allow filtering and time-based sorting.
6. Conflict detection highlights exact same-time tasks so owners can adjust timing.

## Testing Coverage

Current tests verify:

- Task completion and reset behavior.
- Adding/removing tasks from pets.
- Chronological sorting and invalid time handling.
- Recurrence for daily and weekly tasks.
- Conflict detection for same-pet and cross-pet collisions.

## 📸 Demo

![PawPal App](assets/screenshots/pawpal_app_screenshot.png)

## UML

Final UML files:

![Mermaid Source](assets/diagrams/uml_final.mmd)
![System UML](assets/diagrams/uml_final.png)
