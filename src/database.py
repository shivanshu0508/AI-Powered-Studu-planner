
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "study_planner.db"


def get_connection():
    """Create a database connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the database tables if they don't exist."""

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                plan_json TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                activity TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (plan_id)
                    REFERENCES study_plans(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_plan
            ON study_tasks(plan_id)
        """)


def save_plan(plan):
    """Save a study plan and its tasks. Return the plan ID."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO study_plans (goal, exam_date, plan_json)
            VALUES (?, ?, ?)
            """,
            (
                plan["goal"],
                plan["exam_date"],
                json.dumps(plan)
            )
        )

        plan_id = cursor.lastrowid

        for day in plan["daily_plans"]:
            for task in day["tasks"]:
                connection.execute(
                    """
                    INSERT INTO study_tasks (
                        plan_id,
                        task_date,
                        subject,
                        topic,
                        duration_minutes,
                        activity
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_id,
                        day["date"],
                        task["subject"],
                        task["topic"],
                        task["duration_minutes"],
                        task["activity"]
                    )
                )

        return plan_id


def get_plans():
    """Return saved plans, newest first."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, goal, exam_date, created_at, plan_json
            FROM study_plans
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "goal": row["goal"],
            "exam_date": row["exam_date"],
            "created_at": row["created_at"],
            "plan": json.loads(row["plan_json"])
        }
        for row in rows
    ]


def get_tasks(plan_id):
    """Return tasks belonging to a particular plan."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM study_tasks
            WHERE plan_id = ?
            ORDER BY task_date, id
            """,
            (plan_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def mark_task_completed(task_id, completed=True):
    """Update the completion status of a task."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE study_tasks
            SET completed = ?
            WHERE id = ?
            """,
            (int(completed), task_id)
        )

        return cursor.rowcount > 0


def get_progress(plan_id):
    """Calculate task completion statistics."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(completed), 0) AS completed
            FROM study_tasks
            WHERE plan_id = ?
            """,
            (plan_id,)
        ).fetchone()

    total = row["total"]
    completed = row["completed"]

    percentage = round(completed / total * 100) if total else 0

    return {
        "total": total,
        "completed": completed,
        "remaining": total - completed,
        "percentage": percentage
    }


# Initialize the database when this module is imported.
init_db()
