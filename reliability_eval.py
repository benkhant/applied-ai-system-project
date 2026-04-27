import random
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def _build_owner_with_tasks(shuffle_seed: int) -> Owner:
    owner = Owner(name="Reliability User", available_minutes=120)

    dog = Pet(name="Buddy", species="dog", age=6)
    cat = Pet(name="Mochi", species="cat", age=4)

    tasks = [
        (dog, Task(title="Morning medication", duration_minutes=5, priority="low", required=True, description="Give pill with food", preferred_time="07:30", due_date=date.today())),
        (dog, Task(title="Walk", duration_minutes=30, priority="medium", description="30-minute neighborhood walk", preferred_time="08:00", due_date=date.today())),
        (cat, Task(title="Clean litter box", duration_minutes=15, priority="medium", description="Deep clean litter", preferred_time="09:00", due_date=date.today())),
        (cat, Task(title="Feed breakfast", duration_minutes=10, priority="high", required=True, description="Wet food meal", preferred_time="07:45", due_date=date.today())),
        (dog, Task(title="Brush coat", duration_minutes=10, priority="low", description="Quick grooming session", preferred_time="", due_date=date.today())),
    ]

    rng = random.Random(shuffle_seed)
    rng.shuffle(tasks)

    for pet, task in tasks:
        pet.add_task(task)

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


def run_reliability_trials(trials: int = 20) -> None:
    scheduler = Scheduler()

    signatures = []
    guardrail_failures = 0
    fallback_count = 0

    for trial in range(trials):
        owner = _build_owner_with_tasks(shuffle_seed=trial)
        plan = scheduler.build_ai_daily_plan(owner)
        metadata = scheduler.get_last_plan_metadata()

        signatures.append(tuple(task.title for task in plan))

        if not metadata.get("guardrail_ok", False):
            guardrail_failures += 1
        if metadata.get("fallback_used", False):
            fallback_count += 1

    most_common_signature = max(set(signatures), key=signatures.count)
    consistency_rate = signatures.count(most_common_signature) / trials

    print("AI-Assisted Planner Reliability Report")
    print("=" * 50)
    print(f"Trials: {trials}")
    print(f"Unique plan orderings: {len(set(signatures))}")
    print(f"Consistency rate: {consistency_rate:.2%}")
    print(f"Guardrail failure rate: {guardrail_failures / trials:.2%}")
    print(f"Fallback usage rate: {fallback_count / trials:.2%}")


if __name__ == "__main__":
    run_reliability_trials(trials=20)
