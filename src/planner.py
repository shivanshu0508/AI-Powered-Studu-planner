
from datetime import date, timedelta

from src.gemini_service import generate_study_plan
from src.scheduler import schedule_tasks


def create_study_plan(profile):
    """Generate and schedule a personalized study plan."""

    today = date.today()

    try:
        target_date = date.fromisoformat(str(profile["exam_date"]))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Please provide a valid target date.") from error

    if target_date <= today:
        raise ValueError("The target date must be in the future.")

    goal = str(profile.get("goal", "")).strip()

    if not goal:
        raise ValueError("A study goal is required.")

    subjects = profile.get("subjects", [])

    if not isinstance(subjects, list) or not subjects:
        raise ValueError("Select at least one subject.")

    try:
        study_hours = float(profile["study_hours"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Enter valid daily study hours.") from error

    if not 1 <= study_hours <= 12:
        raise ValueError("Daily study hours must be between 1 and 12.")

    # Calculate available time.
    # The exam date itself is reserved for the exam.
    available_days = (target_date - today).days
    daily_minutes = int(study_hours * 60)
    total_available_minutes = available_days * daily_minutes

    # Generate tasks using Gemini.
    ai_plan = generate_study_plan(profile)

    if not isinstance(ai_plan.get("daily_plans"), list):
        raise ValueError("The AI did not return a valid study plan.")

    tasks = []

    for day in ai_plan["daily_plans"]:
        if not isinstance(day, dict):
            continue

        day_tasks = day.get("tasks", [])

        if not isinstance(day_tasks, list):
            continue

        for task in day_tasks:
            if not isinstance(task, dict):
                continue

            subject = str(task.get("subject", "General")).strip()
            topic = str(task.get("topic", "Study session")).strip()
            activity = str(
                task.get("activity", "Study and practice")
            ).strip()

            try:
                duration = int(task.get("duration_minutes", 60))
            except (TypeError, ValueError):
                continue

            if duration <= 0:
                continue

            tasks.append({
                "subject": subject or "General",
                "topic": topic or "Study session",
                "duration_minutes": duration,
                "activity": activity or "Study and practice",
            })

    if not tasks:
        raise ValueError(
            "No valid tasks were generated. Please try again."
        )

    # Keep only as much work as can fit before the exam.
    # The final task may be shortened to fit the remaining time.
    fitted_tasks = []
    remaining_minutes = total_available_minutes

    for task in tasks:
        if remaining_minutes <= 0:
            break

        fitted_duration = min(
            task["duration_minutes"],
            remaining_minutes
        )

        fitted_task = task.copy()
        fitted_task["duration_minutes"] = fitted_duration
        fitted_tasks.append(fitted_task)

        remaining_minutes -= fitted_duration

    if not fitted_tasks:
        raise ValueError(
            "There is not enough available time to create a study plan."
        )

    # Distribute tasks across available days.
    scheduled_days = schedule_tasks(
        tasks=fitted_tasks,
        start_date=today,
        end_date=target_date - timedelta(days=1),
        daily_hours=study_hours,
    )

    return {
        "summary": str(
            ai_plan.get("summary", "Your personalized study plan")
        ),
        "goal": goal,
        "subjects": subjects,
        "exam_date": profile["exam_date"],
        "study_hours": study_hours,
        "current_level": profile.get("current_level", "Beginner"),
        "daily_plans": scheduled_days,
    }
