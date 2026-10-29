
import streamlit as st
from datetime import date
from pathlib import Path

from src.planner import create_study_plan
from src.database import (
    save_plan,
    get_plans,
    get_tasks,
    mark_task_completed,
    get_progress
)

from rag.document_loader import load_pdf
from rag.text_splitter import split_documents
from rag.vector_store import build_vector_store
from rag.retriever import answer_question


# --------------------------------------------------
# 1. Application configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI-Powered Study Planner",
    page_icon="📚",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Session state
# --------------------------------------------------

if "active_plan_id" not in st.session_state:
    st.session_state.active_plan_id = None

if "rag_ready" not in st.session_state:
    st.session_state.rag_ready = False


# --------------------------------------------------
# 3. Sidebar navigation
# --------------------------------------------------

st.sidebar.title("📚 Study Planner")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Generate Study Plan",
        "My Progress",
        "Study Assistant"
    ]
)

st.sidebar.divider()
st.sidebar.caption(
    "Powered by Python, Streamlit, Gemini and RAG"
)


# --------------------------------------------------
# 4. Home page
# --------------------------------------------------

if page == "Home":

    st.title("📚 AI-Powered Study Planner")

    st.write(
        "Plan your learning, organize your subjects, "
        "ask questions from your notes, and track progress."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("AI Planning", "Enabled")
    col2.metric("RAG Assistant", "Enabled")
    col3.metric("Progress Tracking", "Enabled")

    st.divider()

    st.subheader("What can you do?")

    st.markdown("""
    - **Generate Study Plan:** Create a personalized timetable.
    - **My Progress:** Track completed and pending tasks.
    - **Study Assistant:** Upload PDF notes and ask questions.
    """)

    st.info(
        "Start by opening Generate Study Plan from the sidebar."
    )


# --------------------------------------------------
# 5. Generate study plan
# --------------------------------------------------

elif page == "Generate Study Plan":

    st.title("🗓️ Generate Your Study Plan")

    with st.form("study_planner_form"):

        goal = st.text_input(
            "What is your study goal?",
            placeholder="Example: Prepare for software placements"
        )

        subjects = st.multiselect(
            "Select your subjects",
            [
                "Python",
                "DSA",
                "DBMS",
                "SQL",
                "Operating Systems",
                "Computer Networks",
                "Machine Learning"
            ]
        )

        exam_date = st.date_input(
            "Exam or target date",
            value=date.today(),
            min_value=date.today()
        )

        study_hours = st.slider(
            "Available study hours per day",
            min_value=1,
            max_value=12,
            value=4
        )

        current_level = st.selectbox(
            "Current knowledge level",
            [
                "Beginner",
                "Intermediate",
                "Advanced"
            ]
        )

        submitted = st.form_submit_button(
            "Generate Study Plan",
            type="primary"
        )

    if submitted:

        if not goal.strip():
            st.error("Please enter your study goal.")

        elif not subjects:
            st.error("Please select at least one subject.")

        elif exam_date <= date.today():
            st.error("Please select a future target date.")

        else:

            profile = {
                "goal": goal.strip(),
                "subjects": subjects,
                "exam_date": exam_date.isoformat(),
                "study_hours": study_hours,
                "current_level": current_level
            }

            try:
                with st.spinner(
                    "Gemini is generating your study plan..."
                ):

                    plan = create_study_plan(profile)
                    plan_id = save_plan(plan)

                st.session_state.active_plan_id = plan_id

                st.success(
                    "Your study plan has been generated and saved!"
                )

            except Exception as error:
                st.error(f"Could not generate the plan: {error}")


    # Display the generated or selected plan.

    active_id = st.session_state.active_plan_id

    if active_id is not None:

        saved_plans = get_plans()

        selected_plan = next(
            (
                item for item in saved_plans
                if item["id"] == active_id
            ),
            None
        )

        if selected_plan:

            plan = selected_plan["plan"]

            st.divider()
            st.subheader("Your Personalized Timetable")
            st.write(plan.get("summary", ""))

            progress = get_progress(active_id)

            col1, col2, col3 = st.columns(3)

            col1.metric("Total tasks", progress["total"])
            col2.metric("Completed", progress["completed"])
            col3.metric(
                "Completion",
                f"{progress['percentage']}%"
            )

            st.progress(progress["percentage"] / 100)

            tasks = get_tasks(active_id)

            for task in tasks:

                with st.container(border=True):

                    completed = st.checkbox(
                        (
                            f"{task['task_date']} | "
                            f"{task['subject']} — {task['topic']} "
                            f"({task['duration_minutes']} min)"
                        ),
                        value=bool(task["completed"]),
                        key=f"plan_task_{task['id']}"
                    )

                    st.caption(task["activity"])

                    if completed != bool(task["completed"]):
                        mark_task_completed(
                            task["id"],
                            completed
                        )
                        st.rerun()


# --------------------------------------------------
# 6. My progress
# --------------------------------------------------

elif page == "My Progress":

    st.title("📊 My Study Progress")

    saved_plans = get_plans()

    if not saved_plans:

        st.info(
            "You haven't created a study plan yet. "
            "Generate one first."
        )

    else:

        selected_id = st.selectbox(
            "Choose a study plan",
            options=[item["id"] for item in saved_plans],
            format_func=lambda plan_id: next(
                item["goal"]
                for item in saved_plans
                if item["id"] == plan_id
            )
        )

        progress = get_progress(selected_id)

        col1, col2, col3 = st.columns(3)

        col1.metric("Total tasks", progress["total"])
        col2.metric("Completed", progress["completed"])
        col3.metric("Remaining", progress["remaining"])

        st.progress(progress["percentage"] / 100)

        st.write(
            f"**Completion rate:** {progress['percentage']}%"
        )

        st.subheader("Tasks")

        for task in get_tasks(selected_id):

            with st.container(border=True):

                st.write(
                    f"**{task['task_date']} — "
                    f"{task['subject']}: {task['topic']}**"
                )

                st.caption(
                    f"{task['duration_minutes']} minutes · "
                    f"{task['activity']}"
                )

                completed = st.checkbox(
                    "Completed",
                    value=bool(task["completed"]),
                    key=f"progress_task_{task['id']}"
                )

                if completed != bool(task["completed"]):
                    mark_task_completed(
                        task["id"],
                        completed
                    )
                    st.rerun()


# --------------------------------------------------
# 7. RAG Study Assistant
# --------------------------------------------------

elif page == "Study Assistant":

    st.title("📖 AI Study Assistant")

    st.write(
        "Upload your study notes and ask questions "
        "using Retrieval-Augmented Generation."
    )

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key="study_pdf"
    )

    if uploaded_file is not None:

        if st.button(
            "Process and Index PDF",
            type="primary"
        ):

            try:
                with st.spinner(
                    "Extracting text and building vector index..."
                ):

                    filename = Path(uploaded_file.name).name
                    file_path = UPLOAD_DIR / filename

                    file_path.write_bytes(
                        uploaded_file.getvalue()
                    )

                    documents = load_pdf(file_path)

                    chunks = split_documents(
                        documents,
                        chunk_size=800,
                        chunk_overlap=150
                    )

                    count = build_vector_store(chunks)

                    st.session_state.rag_ready = True

                    st.success(
                        f"Successfully indexed {count} chunks "
                        f"from {filename}."
                    )

            except Exception as error:

                st.session_state.rag_ready = False
                st.error(f"Could not process the PDF: {error}")


    st.divider()
    st.subheader("Ask a question")

    question = st.text_input(
        "Enter your question",
        placeholder="Example: Explain DBMS normalization"
    )

    if st.button("Ask AI"):

        if not question.strip():

            st.warning("Please enter a question.")

        elif not st.session_state.rag_ready:

            st.warning(
                "Upload and index a PDF before asking questions."
            )

        else:

            try:
                with st.spinner(
                    "Searching your notes and generating an answer..."
                ):

                    result = answer_question(question)

                st.subheader("Answer")
                st.markdown(result["answer"])

                st.subheader("Sources")

                if not result["sources"]:

                    st.info("No relevant sources were retrieved.")

                for source in result["sources"]:

                    with st.expander(
                        f"{source['reference']}: "
                        f"{source['source']} — Page {source['page']}"
                    ):

                        st.write(source["text"])

                        st.caption(
                            "Similarity score: "
                            f"{source['similarity']}"
                        )

            except Exception as error:

                st.error(f"Could not answer the question: {error}")


# --------------------------------------------------
# 8. Footer
# --------------------------------------------------

st.sidebar.divider()
st.sidebar.caption("AI Study Planner | Python + RAG")
