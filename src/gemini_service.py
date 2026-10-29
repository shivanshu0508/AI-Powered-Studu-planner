
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load .env from the project root directory.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)


def get_gemini_client():
    """Create a Gemini client using the project's .env file."""

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            f"GEMINI_API_KEY is missing. Add it to {ENV_PATH}"
        )

    return genai.Client(api_key=api_key)


def generate_study_plan(profile):
    """Generate a structured study plan from a student profile."""

    required_fields = [
        "goal",
        "subjects",
        "exam_date",
        "study_hours",
        "current_level",
    ]

    for field in required_fields:
        if field not in profile:
            raise ValueError(f"Missing profile field: {field}")

    if not profile["subjects"]:
        raise ValueError("Please provide at least one subject.")

    client = get_gemini_client()

    prompt = f"""
You are an expert study planning assistant.

Create a realistic, personalized study plan.

Student information:
Goal: {profile['goal']}
Subjects: {', '.join(profile['subjects'])}
Target date: {profile['exam_date']}
Available study hours per day: {profile['study_hours']}
Current level: {profile['current_level']}

Rules:
1. Prioritize subjects according to the student's goal.
2. Respect the available daily study hours.
3. Create practical tasks with clear learning outcomes.
4. Include practice and revision sessions.
5. Do not schedule dates after the target date.
6. Use ISO dates in YYYY-MM-DD format.
7. Keep the plan appropriate for the student's level.
8. Return valid JSON only.
9. Keep the response concise for long study periods.

Return exactly this JSON structure:
{{
  "summary": "Short plan overview",
  "daily_plans": [
    {{
      "date": "YYYY-MM-DD",
      "tasks": [
        {{
          "subject": "Python",
          "topic": "Functions",
          "duration_minutes": 60,
          "activity": "Learn and solve exercises"
        }}
      ]
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    # Parse Gemini's JSON response.
    try:
        plan = json.loads(response.text)
    except json.JSONDecodeError:
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.text.strip(),
            flags=re.IGNORECASE,
        )

        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Gemini returned invalid JSON. Please try again."
            ) from error

    if not isinstance(plan, dict):
        raise ValueError("The generated plan must be a JSON object.")

    if not isinstance(plan.get("daily_plans"), list):
        raise ValueError(
            "Gemini returned an invalid daily_plans field."
        )

    # Check that each day contains a list of tasks.
    for day in plan["daily_plans"]:
        if not isinstance(day, dict):
            raise ValueError("A daily plan entry is invalid.")

        if not isinstance(day.get("tasks"), list):
            raise ValueError("A daily plan has an invalid tasks field.")

    return plan
