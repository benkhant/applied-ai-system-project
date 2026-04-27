import streamlit as st
import logging
from pathlib import Path
from pawpal_system import Owner, Pet, Task, Scheduler


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "pawpal.log",
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner Setup")

# Persist Owner object across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

scheduler = st.session_state.scheduler

owner_col1, owner_col2 = st.columns(2)
with owner_col1:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
with owner_col2:
    available_minutes = st.number_input(
        "Available minutes today", min_value=0, max_value=1440, value=st.session_state.owner.available_minutes
    )

if owner_name != st.session_state.owner.name:
    st.session_state.owner.name = owner_name
if int(available_minutes) != st.session_state.owner.available_minutes:
    st.session_state.owner.update_available_minutes(int(available_minutes))

st.markdown("### Add Pet")
with st.form("add_pet_form"):
    pet_col1, pet_col2, pet_col3 = st.columns(3)
    with pet_col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with pet_col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with pet_col3:
        age = st.number_input("Age", min_value=0, max_value=50, value=3)

    add_pet_submitted = st.form_submit_button("Add pet")
    if add_pet_submitted:
        existing_names = [pet.name for pet in st.session_state.owner.get_pets()]
        if not pet_name.strip():
            st.warning("Pet name is required.")
        elif pet_name in existing_names:
            st.warning("A pet with that name already exists.")
        else:
            new_pet = Pet(name=pet_name.strip(), species=species, age=int(age))
            st.session_state.owner.add_pet(new_pet)
            st.success(f"Added pet: {new_pet.name}")

st.markdown("### Schedule a Task")
pets = st.session_state.owner.get_pets()
if not pets:
    st.info("Add at least one pet before scheduling tasks.")
else:
    selected_pet_name = st.selectbox("Choose pet", [pet.name for pet in pets])
    selected_pet = next(p for p in pets if p.name == selected_pet_name)

    with st.form("add_task_form"):
        task_col1, task_col2, task_col3, task_col4 = st.columns(4)
        with task_col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with task_col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with task_col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with task_col4:
            preferred_time = st.text_input("Preferred time (HH:MM)", value="")

        task_description = st.text_input("Description", value="")
        task_required = st.checkbox("Required task", value=False)

        add_task_submitted = st.form_submit_button("Add task")
        if add_task_submitted:
            if not task_title.strip():
                st.warning("Task title is required.")
            else:
                new_task = Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    description=task_description.strip(),
                    preferred_time=preferred_time.strip(),
                    required=task_required,
                )
                selected_pet.add_task(new_task)
                st.success(f"Added task '{new_task.title}' to {selected_pet.name}")

    st.write(f"**{selected_pet.name}'s Tasks**")
    status_filter_label = st.selectbox(
        "Task status",
        ["All", "Pending", "Completed"],
        index=0,
    )

    completed_filter = None
    if status_filter_label == "Pending":
        completed_filter = False
    elif status_filter_label == "Completed":
        completed_filter = True

    filtered_tasks = scheduler.filter_tasks(
        st.session_state.owner,
        completed=completed_filter,
        pet_name=selected_pet.name,
    )
    sorted_tasks = scheduler.sort_by_time(filtered_tasks)

    if sorted_tasks:
        table_rows = []
        for task in sorted_tasks:
            table_rows.append(
                {
                    "Preferred Time": task.preferred_time or "Any time",
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority.title(),
                    "Required": "Yes" if task.required else "No",
                    "Status": "Completed" if task.completed else "Pending",
                }
            )

        st.table(table_rows)
    else:
        st.info("No tasks match this filter yet.")

    conflict_warnings = scheduler.detect_time_conflicts(st.session_state.owner)
    st.markdown("### Conflict Check")
    if conflict_warnings:
        st.warning(
            "Potential time conflicts detected. These tasks are booked at the same time and may be hard to complete."
        )
        for warning_message in conflict_warnings:
            st.warning(warning_message)
        st.info("Tip: adjust one conflicting task's preferred time so care steps do not overlap.")
    else:
        st.success("No time conflicts detected for pending tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a prioritized daily plan across all pets based on available time and task priorities.")

planner_mode = st.radio(
    "Planner mode",
    ["Rule-based", "AI-assisted (retrieval + guardrails)"],
    horizontal=True,
)

if st.button("Generate schedule"):
    if planner_mode == "AI-assisted (retrieval + guardrails)":
        schedule = scheduler.build_ai_daily_plan(st.session_state.owner)
        plan_text = scheduler.explain_ai_plan(schedule)
    else:
        schedule = scheduler.build_daily_plan(st.session_state.owner)
        plan_text = scheduler.explain_plan(schedule)

    metadata = scheduler.get_last_plan_metadata()

    if schedule:
        st.success("Schedule generated!")
        schedule_rows = []
        for task in schedule:
            schedule_rows.append(
                {
                    "Task": task.title,
                    "Preferred Time": task.preferred_time or "Any time",
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority.title(),
                    "Required": "Yes" if task.required else "No",
                }
            )
        st.table(schedule_rows)
        st.text(plan_text)

        if planner_mode == "AI-assisted (retrieval + guardrails)":
            st.markdown("### AI Guardrail Status")
            if metadata.get("guardrail_ok", False):
                st.success("Guardrails passed. AI plan was accepted.")
            else:
                st.warning("Guardrails failed. The system safely fell back to rule-based scheduling.")
                for issue in metadata.get("guardrail_issues", []):
                    st.warning(issue)
    else:
        st.warning("No incomplete tasks to schedule. Add pets and tasks above first.")
