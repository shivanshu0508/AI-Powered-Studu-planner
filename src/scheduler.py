
from datetime import date, timedelta


def schedule_tasks(tasks, start_date, end_date, daily_hours):
    """
    Distribute tasks across the available dates.

    Args:
        tasks: List of task dictionaries.
        start_date: datetime.date.
        end_date: datetime.date.
        daily_hours: Maximum available study hours per day.

    Returns:
        A list of daily plans.
    """

    if start_date > end_date:
        raise ValueError("Start date must not be after end date.")

    if daily_hours <= 0:
        raise ValueError("Daily study hours must be positive.")

    daily_limit = daily_hours * 60
    daily_plans = []
    current_date = start_date
    day_tasks = []
    used_minutes = 0

    for task in tasks:
        duration = int(task.get("duration_minutes", 60))

        if duration <= 0:
            raise ValueError("Task duration must be positive.")

        # Split long tasks into sessions if needed.
        remaining = duration

        while remaining > 0:
            if current_date > end_date:
                raise ValueError(
                    "Tasks cannot fit before the target date. "
                    "Reduce tasks or increase available study time."
                )

            available_minutes = daily_limit - used_minutes

            if available_minutes == 0:
                daily_plans.append({
                    "date": current_date.isoformat(),
                    "tasks": day_tasks
                })

                current_date += timedelta(days=1)
                day_tasks = []
                used_minutes = 0
                available_minutes = daily_limit

            session_minutes = min(
                remaining,
                available_minutes
            )

            day_tasks.append({
                "subject": task.get("subject", "General"),
                "topic": task.get("topic", "Study session"),
                "duration_minutes": session_minutes,
                "activity": task.get(
                    "activity",
                    "Study and practice"
                )
            })

            remaining -= session_minutes
            used_minutes += session_minutes

    if day_tasks:
        daily_plans.append({
            "date": current_date.isoformat(),
            "tasks": day_tasks
        })

    return daily_plans
