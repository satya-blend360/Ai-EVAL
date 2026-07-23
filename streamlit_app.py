import os
import json
import time
import re
import uuid
import base64
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Setup pathing
import sys
APP_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(APP_ROOT, 'src'))
sys.path.append(APP_ROOT)

from ai_eval.core.evaluator import AIEvaluator
from ai_eval.data.loader import load_evaluation_data
from ai_eval.config import REPORTS_DIR, DEFAULT_WEIGHTS
from evaluate_submission import run_live_evaluation

# Streamlit Page Configuration
st.set_page_config(
    page_title="PIH AI Evaluation Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Rich Aesthetics)
st.markdown("""
<style>
    /* Dark glassmorphism card styling */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(20, 184, 166, 0.5);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .metric-delta {
        font-size: 0.85rem;
        margin-top: 6px;
        font-weight: 500;
    }
    .delta-positive { color: #10b981; }
    .delta-negative { color: #f43f5e; }
    
    /* Title layout */
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #14b8a6 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    
    /* Section dividers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-top: 25px;
        margin-bottom: 15px;
        border-left: 4px solid #14b8a6;
        padding-left: 10px;
    }
    
    /* Claim matching styling */
    .claim-box {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 0.95rem;
    }
    .claim-supported {
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #a7f3d0;
    }
    .claim-unsupported {
        background-color: rgba(244, 63, 94, 0.1);
        border: 1px solid rgba(244, 63, 94, 0.3);
        color: #fecdd3;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load reports from filesystem
def load_all_reports() -> List[Dict[str, Any]]:
    reports = []
    if REPORTS_DIR.exists():
        for file in REPORTS_DIR.glob("*.json"):
            try:
                with open(file, "r") as f:
                    r = json.load(f)
                    # Check if standard keys are present
                    if "overall_score" in r:
                        reports.append(r)
            except Exception:
                pass
    # Sort by timestamp
    reports.sort(key=lambda x: x.get("timestamp", ""))
    return reports


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


PORTAL_PASSWORD = get_secret("JUDGE_PORTAL_PASSWORD", "123")
COMPANY_DOMAIN = "blend360.com"
DB_CATALOG = get_secret("DATABRICKS_CATALOG", "sandbox")
DB_SCHEMA = get_secret("DATABRICKS_SCHEMA", "ai_eval_judge_portal")
MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024
MAX_SCREENSHOTS = 5
MAX_JSON_CHARS = 100_000
MAX_TEXT_CHARS = 5_000


def safe_identifier(value: str, default: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""):
        return value
    return default


DB_CATALOG = safe_identifier(DB_CATALOG, "sandbox")
DB_SCHEMA = safe_identifier(DB_SCHEMA, "ai_eval_judge_portal")
DB_PREFIX = f"{DB_CATALOG}.{DB_SCHEMA}"


def is_company_email(email: str) -> bool:
    return email.strip().lower().endswith(f"@{COMPANY_DOMAIN}")


def is_email(value: str) -> bool:
    if not value:
        return True
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()) is not None


def is_url(value: str) -> bool:
    if not value:
        return True
    return re.fullmatch(r"https?://[^\s]+", value.strip(), flags=re.IGNORECASE) is not None


def db_configured() -> bool:
    return all(
        [
            get_secret("DATABRICKS_SERVER_HOSTNAME"),
            get_secret("DATABRICKS_HTTP_PATH"),
            get_secret("DATABRICKS_TOKEN"),
        ]
    )


def run_db_query(query: str, parameters: Optional[Dict[str, Any]] = None, fetch: bool = False):
    if not db_configured():
        raise RuntimeError("Databricks secrets are not configured.")
    try:
        from databricks import sql
    except ImportError as exc:
        raise RuntimeError("databricks-sql-connector is not installed.") from exc

    with sql.connect(
        server_hostname=get_secret("DATABRICKS_SERVER_HOSTNAME"),
        http_path=get_secret("DATABRICKS_HTTP_PATH"),
        access_token=get_secret("DATABRICKS_TOKEN"),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters=parameters or {})
            if not fetch:
                return None
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return pd.DataFrame(rows, columns=columns)


def local_submissions() -> pd.DataFrame:
    scores = st.session_state.setdefault("local_judge_scores", {})
    rows = [
        {
            "submission_id": "local_project_apex",
            "project_name": "Project Apex",
            "submitter_name": "Seed Data",
            "submitter_email": "saisrisatya.padala@blend360.com",
            "submission_url": "https://ai-eval-7214119327730999.aws.databricksapps.com",
            "video_url": "",
            "description": "Seed submission from the existing Project Apex evaluation data.",
            "submission_json": "",
            "screenshots_json": "[]",
            "ai_score": 88.6,
            "ai_summary": "AI evaluation found strong RAG faithfulness and business value with room to improve citation coverage.",
            "status": "ready_for_review",
            "created_at": "",
            "updated_at": "",
        },
        {
            "submission_id": "local_project_horizon",
            "project_name": "Project Horizon",
            "submitter_name": "Seed Data",
            "submitter_email": "saisrisatya.padala@blend360.com",
            "submission_url": "https://example.com/project-horizon-prototype",
            "video_url": "",
            "description": "Seed submission focused on hallucination auditing for Project Horizon.",
            "submission_json": "",
            "screenshots_json": "[]",
            "ai_score": 82.0,
            "ai_summary": "AI evaluation flagged one unsupported claim around GPT-4 integration and otherwise strong evidence grounding.",
            "status": "ready_for_review",
            "created_at": "",
            "updated_at": "",
        },
    ]
    rows.extend(st.session_state.setdefault("local_extra_submissions", []))
    ai_results = st.session_state.setdefault("local_ai_results", {})
    for row in rows:
        row.setdefault("submission_json", "")
        row.setdefault("screenshots_json", "[]")
        row.setdefault("ai_score", None)
        row.setdefault("ai_summary", "AI evaluation has not been run yet.")
        row.setdefault("status", "submitted")
        row.setdefault("created_at", "")
        row.setdefault("updated_at", "")
        if row["submission_id"] in ai_results:
            row.update(ai_results[row["submission_id"]])
            row["status"] = "ai_evaluated"
        row_scores = [v["total_score"] for v in scores.values() if v["submission_id"] == row["submission_id"]]
        row["judge_count"] = len(row_scores)
        row["avg_judge_score"] = sum(row_scores) / len(row_scores) if row_scores else None
        row["last_judged_at"] = ""
    return pd.DataFrame(rows)


@st.cache_data(ttl=5)
def load_submissions() -> pd.DataFrame:
    if not db_configured():
        return local_submissions()
    query = f"""
        SELECT
            s.submission_id,
            s.project_name,
            s.submitter_name,
            s.submitter_email,
            s.submission_url,
            s.video_url,
            s.description,
            s.submission_json,
            s.screenshots_json,
            s.ai_score,
            s.ai_summary,
            s.status,
            s.created_at,
            s.updated_at,
            COALESCE(j.judge_count, 0) AS judge_count,
            j.avg_judge_score,
            j.last_judged_at
        FROM {DB_PREFIX}.submissions s
        LEFT JOIN (
            SELECT
                submission_id,
                COUNT(*) AS judge_count,
                AVG(total_score) AS avg_judge_score,
                MAX(updated_at) AS last_judged_at
            FROM {DB_PREFIX}.judge_scores
            GROUP BY submission_id
        ) j ON s.submission_id = j.submission_id
        ORDER BY s.created_at DESC
    """
    return run_db_query(query, fetch=True)


def load_scores(submission_id: str) -> pd.DataFrame:
    if not db_configured():
        scores = [
            score
            for score in st.session_state.setdefault("local_judge_scores", {}).values()
            if score["submission_id"] == submission_id
        ]
        return pd.DataFrame(scores)
    return run_db_query(
        f"""
        SELECT
            judge_email,
            accuracy,
            completeness,
            presentation,
            business_impact,
            technical_quality,
            total_score,
            comments,
            updated_at
        FROM {DB_PREFIX}.judge_scores
        WHERE submission_id = :submission_id
        ORDER BY updated_at DESC
        """,
        {"submission_id": submission_id},
        fetch=True,
    )


def load_my_review_summary(judge_email: str) -> pd.DataFrame:
    if not db_configured():
        scores = [
            score
            for score in st.session_state.setdefault("local_judge_scores", {}).values()
            if score["judge_email"].lower() == judge_email.lower()
        ]
        return pd.DataFrame(scores)
    return run_db_query(
        f"""
        SELECT
            submission_id,
            total_score,
            updated_at
        FROM {DB_PREFIX}.judge_scores
        WHERE lower(judge_email) = lower(:judge_email)
        """,
        {"judge_email": judge_email},
        fetch=True,
    )


def load_my_score(submission_id: str, judge_email: str) -> Dict[str, Any]:
    defaults = {
        "accuracy": 7.0,
        "completeness": 7.0,
        "presentation": 7.0,
        "business_impact": 7.0,
        "technical_quality": 7.0,
        "comments": "",
    }
    if not db_configured():
        return st.session_state.setdefault("local_judge_scores", {}).get(
            f"{submission_id}:{judge_email}", defaults
        )
    score_df = run_db_query(
        f"""
        SELECT accuracy, completeness, presentation, business_impact, technical_quality, comments
        FROM {DB_PREFIX}.judge_scores
        WHERE submission_id = :submission_id AND lower(judge_email) = lower(:judge_email)
        LIMIT 1
        """,
        {"submission_id": submission_id, "judge_email": judge_email},
        fetch=True,
    )
    if score_df.empty:
        return defaults
    row = score_df.iloc[0].to_dict()
    return {**defaults, **{k: row.get(k, defaults[k]) for k in defaults}}


def save_judge_score(submission_id: str, judge_email: str, values: Dict[str, Any]) -> None:
    total_score = sum(
        [
            values["accuracy"],
            values["completeness"],
            values["presentation"],
            values["business_impact"],
            values["technical_quality"],
        ]
    ) / 5.0
    score = {
        "score_id": f"score_{uuid.uuid4().hex[:12]}",
        "submission_id": submission_id,
        "judge_email": judge_email,
        "accuracy": float(values["accuracy"]),
        "completeness": float(values["completeness"]),
        "presentation": float(values["presentation"]),
        "business_impact": float(values["business_impact"]),
        "technical_quality": float(values["technical_quality"]),
        "total_score": float(total_score),
        "comments": values.get("comments", ""),
    }
    if not db_configured():
        st.session_state.setdefault("local_judge_scores", {})[
            f"{submission_id}:{judge_email}"
        ] = score
        load_submissions.clear()
        return
    run_db_query(
        f"""
        MERGE INTO {DB_PREFIX}.judge_scores AS t
        USING (
            SELECT
                :score_id AS score_id,
                :submission_id AS submission_id,
                :judge_email AS judge_email,
                :accuracy AS accuracy,
                :completeness AS completeness,
                :presentation AS presentation,
                :business_impact AS business_impact,
                :technical_quality AS technical_quality,
                :total_score AS total_score,
                :comments AS comments
        ) AS s
        ON t.submission_id = s.submission_id AND lower(t.judge_email) = lower(s.judge_email)
        WHEN MATCHED THEN UPDATE SET
            accuracy = s.accuracy,
            completeness = s.completeness,
            presentation = s.presentation,
            business_impact = s.business_impact,
            technical_quality = s.technical_quality,
            total_score = s.total_score,
            comments = s.comments,
            updated_at = current_timestamp()
        WHEN NOT MATCHED THEN INSERT (
            score_id,
            submission_id,
            judge_email,
            accuracy,
            completeness,
            presentation,
            business_impact,
            technical_quality,
            total_score,
            comments,
            updated_at
        ) VALUES (
            s.score_id,
            s.submission_id,
            s.judge_email,
            s.accuracy,
            s.completeness,
            s.presentation,
            s.business_impact,
            s.technical_quality,
            s.total_score,
            s.comments,
            current_timestamp()
        )
        """,
        score,
    )
    load_submissions.clear()


def create_submission(values: Dict[str, Any]) -> None:
    submission = {
        "submission_id": f"sub_{uuid.uuid4().hex[:12]}",
        "project_name": values["project_name"],
        "submitter_name": values["submitter_name"],
        "submitter_email": values["submitter_email"],
        "submission_url": values["submission_url"],
        "video_url": values["video_url"],
        "description": values["description"],
        "submission_json": values.get("submission_json", ""),
        "screenshots_json": values.get("screenshots_json", "[]"),
    }
    if not db_configured():
        st.session_state.setdefault("local_extra_submissions", []).append(submission)
        load_submissions.clear()
        return
    run_db_query(
        f"""
        INSERT INTO {DB_PREFIX}.submissions (
            submission_id,
            project_name,
            submitter_name,
            submitter_email,
            submission_url,
            video_url,
            description,
            submission_json,
            screenshots_json,
            ai_score,
            ai_summary,
            status,
            created_at,
            updated_at
        ) VALUES (
            :submission_id,
            :project_name,
            :submitter_name,
            :submitter_email,
            :submission_url,
            :video_url,
            :description,
            :submission_json,
            :screenshots_json,
            NULL,
            'AI evaluation has not been run yet.',
            'submitted',
            current_timestamp(),
            current_timestamp()
        )
        """,
        submission,
    )
    load_submissions.clear()


def update_ai_result(submission_id: str, ai_score: float, ai_summary: str) -> None:
    if not db_configured():
        st.session_state.setdefault("local_ai_results", {})[submission_id] = {
            "ai_score": ai_score,
            "ai_summary": ai_summary,
        }
        load_submissions.clear()
        return
    run_db_query(
        f"""
        UPDATE {DB_PREFIX}.submissions
        SET ai_score = :ai_score,
            ai_summary = :ai_summary,
            status = 'ai_evaluated',
            updated_at = current_timestamp()
        WHERE submission_id = :submission_id
        """,
        {
            "submission_id": submission_id,
            "ai_score": float(ai_score),
            "ai_summary": ai_summary,
        },
    )
    load_submissions.clear()


def encode_screenshots(uploaded_files) -> str:
    screenshots = []
    total_bytes = 0
    if len(uploaded_files or []) > MAX_SCREENSHOTS:
        raise ValueError(f"Upload {MAX_SCREENSHOTS} screenshots or fewer.")
    for uploaded_file in uploaded_files or []:
        content = uploaded_file.getvalue()
        total_bytes += len(content)
        if total_bytes > MAX_SCREENSHOT_BYTES:
            raise ValueError("Screenshot uploads must be 10 MB or less in total.")
        screenshots.append(
            {
                "name": uploaded_file.name,
                "mime_type": uploaded_file.type or "image/png",
                "size_bytes": len(content),
                "data_base64": base64.b64encode(content).decode("ascii"),
            }
        )
    return json.dumps(screenshots)


def decode_screenshots(screenshots_json: str) -> List[Dict[str, Any]]:
    if not screenshots_json:
        return []
    try:
        screenshots = json.loads(screenshots_json)
    except Exception:
        return []
    if not isinstance(screenshots, list):
        return []
    return screenshots


def normalize_video_url(video_url: str) -> str:
    video_url = (video_url or "").strip()
    youtube_match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]+)", video_url)
    if youtube_match:
        return f"https://www.youtube.com/embed/{youtube_match.group(1)}"
    return video_url


def render_submission_json(submission_json: str) -> None:
    if not submission_json:
        st.caption("No JSON payload submitted.")
        return
    try:
        st.json(json.loads(submission_json))
    except Exception:
        st.code(submission_json, language="json")


def render_screenshots(screenshots_json: str) -> None:
    screenshots = decode_screenshots(screenshots_json)
    if not screenshots:
        st.caption("No screenshots submitted.")
        return
    for screenshot in screenshots:
        name = screenshot.get("name", "screenshot")
        encoded = screenshot.get("data_base64", "")
        try:
            image_bytes = base64.b64decode(encoded)
        except Exception:
            st.caption(f"{name}: could not decode image data.")
            continue
        st.image(image_bytes, caption=name, use_container_width=True)


def render_public_submission() -> None:
    st.markdown('<div class="main-title">Project Submission</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Submit your project details, video, JSON output, and screenshots for judge review.</div>',
        unsafe_allow_html=True,
    )
    if not db_configured():
        st.warning("Databricks secrets are not configured. Submissions are only kept in this Streamlit session.")

    with st.form("public_submission_form"):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("Project name")
            submitter_name = st.text_input("Your name")
            submitter_email = st.text_input("Your email")
            submission_url = st.text_input("Prototype or app URL")
        with c2:
            video_url = st.text_input("Video URL", placeholder="OneDrive, YouTube, Loom, or direct video URL")
            screenshots = st.file_uploader(
                "Screenshots",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
            )
            description = st.text_area("Short project description", height=110)
        submission_json = st.text_area(
            "Paste JSON output / response",
            height=220,
            placeholder='{"project": "Example", "result": "..."}',
        )

        submitted = st.form_submit_button("Submit for judging", use_container_width=True)

    if not submitted:
        return

    errors = []
    if not project_name.strip():
        errors.append("Project name is required.")
    if not submitter_name.strip():
        errors.append("Your name is required.")
    if submitter_email.strip() and not is_email(submitter_email):
        errors.append("Enter a valid email address.")
    if not video_url.strip():
        errors.append("Video URL is required.")
    elif not is_url(video_url):
        errors.append("Video URL must start with http:// or https://.")
    if submission_url.strip() and not is_url(submission_url):
        errors.append("Prototype/app URL must start with http:// or https://.")
    if len(description) > MAX_TEXT_CHARS:
        errors.append(f"Description must be {MAX_TEXT_CHARS:,} characters or fewer.")
    if len(submission_json) > MAX_JSON_CHARS:
        errors.append(f"JSON payload must be {MAX_JSON_CHARS:,} characters or fewer.")
    if submission_json.strip():
        try:
            json.loads(submission_json)
        except Exception:
            errors.append("The pasted JSON is not valid JSON.")
    if errors:
        for error in errors:
            st.error(error)
        return

    try:
        screenshots_json = encode_screenshots(screenshots)
        create_submission(
            {
                "project_name": project_name.strip(),
                "submitter_name": submitter_name.strip(),
                "submitter_email": submitter_email.strip(),
                "submission_url": submission_url.strip(),
                "video_url": video_url.strip(),
                "description": description.strip(),
                "submission_json": submission_json.strip(),
                "screenshots_json": screenshots_json,
            }
        )
    except Exception as exc:
        st.error(f"Could not save submission: {exc}")
        return

    st.success("Submission saved. Judges will see it on their dashboard.")
    st.balloons()


def render_login() -> None:
    st.markdown('<div class="main-title">Judge Portal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sign in with your Blend360 email to review submitted projects.</div>',
        unsafe_allow_html=True,
    )
    with st.form("judge_login_form"):
        email = st.text_input("Company email", placeholder="Saisrisatya.Padala@blend360.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        normalized_email = email.strip().lower()
        if not is_company_email(normalized_email):
            st.error("Use a Blend360 company email address.")
        elif password != PORTAL_PASSWORD:
            st.error("Incorrect password.")
        else:
            st.session_state["judge_email"] = normalized_email
            st.session_state["judge_logged_in"] = True
            st.rerun()


def show_video_or_link(video_url: str) -> None:
    if not video_url:
        st.caption("No video URL submitted.")
        return
    st.link_button("Open submitted video", video_url, use_container_width=True)
    preview_url = normalize_video_url(video_url)
    try:
        components.iframe(preview_url, height=360, scrolling=True)
    except Exception:
        st.caption("Video preview could not be embedded. Use the link above.")


def render_judge_portal(judge_email: str) -> None:
    st.markdown('<div class="main-title">Judge Portal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Review project submissions, compare AI scores, and save judge marks.</div>',
        unsafe_allow_html=True,
    )

    selected_review_id = st.session_state.get("selected_review_submission_id")
    auto_refresh = st.sidebar.toggle("Auto-refresh list", value=False)
    if auto_refresh and not selected_review_id:
        try:
            from streamlit_autorefresh import st_autorefresh

            st_autorefresh(interval=30000, key="judge_portal_autorefresh")
        except Exception:
            st.sidebar.caption("Auto-refresh package is unavailable in this environment.")

    if st.sidebar.button("Refresh data", use_container_width=True):
        load_submissions.clear()
        st.rerun()

    if not db_configured():
        st.warning("Databricks secrets are not configured. Changes are kept only in this Streamlit session.")

    try:
        submissions = load_submissions()
    except Exception as exc:
        st.error(f"Could not load submissions from Databricks: {exc}")
        submissions = local_submissions()

    try:
        my_reviews = load_my_review_summary(judge_email)
    except Exception:
        my_reviews = pd.DataFrame(columns=["submission_id", "total_score", "updated_at"])

    reviewed_ids = set(my_reviews.get("submission_id", pd.Series(dtype=str)).dropna().astype(str).tolist())
    my_score_by_submission = {}
    if not my_reviews.empty:
        for review in my_reviews.to_dict("records"):
            my_score_by_submission[str(review.get("submission_id"))] = review

    total_submissions = len(submissions)
    reviewed_submissions = len(reviewed_ids)
    pending_submissions = max(total_submissions - reviewed_submissions, 0)
    avg_ai = submissions["ai_score"].dropna().mean() if "ai_score" in submissions else np.nan

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Submitted", total_submissions)
    kpi2.metric("Reviewed", reviewed_submissions)
    kpi3.metric("Pending", pending_submissions)
    kpi4.metric("Avg AI Score", "N/A" if pd.isna(avg_ai) else f"{avg_ai:.1f}")

    with st.expander("Add project submission", expanded=False):
        with st.form("new_submission_form"):
            c1, c2 = st.columns(2)
            with c1:
                project_name = st.text_input("Project name")
                submitter_name = st.text_input("Submitter name")
                submitter_email = st.text_input("Submitter email")
            with c2:
                submission_url = st.text_input("Prototype or submission URL")
                video_url = st.text_input("Video URL")
                description = st.text_area("Short description", height=120)
            if st.form_submit_button("Save submission", use_container_width=True):
                if not project_name.strip():
                    st.error("Project name is required.")
                else:
                    try:
                        create_submission(
                            {
                                "project_name": project_name.strip(),
                                "submitter_name": submitter_name.strip(),
                                "submitter_email": submitter_email.strip(),
                                "submission_url": submission_url.strip(),
                                "video_url": video_url.strip(),
                                "description": description.strip(),
                            }
                        )
                        st.success("Submission saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save submission: {exc}")

    if submissions.empty:
        st.info("No project submissions are available yet.")
        return

    if selected_review_id:
        selected_rows = submissions[submissions["submission_id"] == selected_review_id]
        if selected_rows.empty:
            st.session_state.pop("selected_review_submission_id", None)
            st.warning("That submission is no longer available.")
            st.rerun()
        selected_id = selected_review_id
        selected = selected_rows.iloc[0].to_dict()
        back_col, status_col = st.columns([0.2, 0.8])
        with back_col:
            if st.button("Back", use_container_width=True):
                st.session_state.pop("selected_review_submission_id", None)
                st.rerun()
        with status_col:
            review = my_score_by_submission.get(selected_id)
            if review:
                st.success(f"You reviewed this project. Your score: {float(review.get('total_score') or 0):.1f}/10")
            else:
                st.info("You have not reviewed this project yet.")
    else:
        st.markdown('<div class="section-header">All Submissions</div>', unsafe_allow_html=True)
        filter_col, status_col = st.columns([0.65, 0.35])
        with filter_col:
            search_text = st.text_input("Search projects", placeholder="Search by project, submitter, or status")
        with status_col:
            status_filter = st.radio(
                "Review status",
                ["All", "Pending", "Reviewed"],
                index=0,
                horizontal=True,
            )

        filtered = submissions.copy()
        if search_text.strip():
            needle = search_text.strip().lower()
            searchable = (
                filtered["project_name"].fillna("")
                + " "
                + filtered["submitter_name"].fillna("")
                + " "
                + filtered["status"].fillna("")
            ).str.lower()
            filtered = filtered[searchable.str.contains(re.escape(needle), na=False)]
        if status_filter == "Pending":
            filtered = filtered[~filtered["submission_id"].astype(str).isin(reviewed_ids)]
        elif status_filter == "Reviewed":
            filtered = filtered[filtered["submission_id"].astype(str).isin(reviewed_ids)]

        if filtered.empty:
            st.info("No submissions match the current filters.")
            return

        for _, row in filtered.iterrows():
            submission_id = str(row["submission_id"])
            reviewed = submission_id in reviewed_ids
            ai_value = row.get("ai_score")
            avg_judge = row.get("avg_judge_score")
            with st.container(border=True):
                top_cols = st.columns([0.5, 0.18, 0.16, 0.16])
                with top_cols[0]:
                    st.subheader(row.get("project_name") or "Untitled project")
                    st.caption(f"{row.get('submitter_name') or 'Unknown submitter'} | {row.get('status') or 'submitted'}")
                    description = row.get("description") or ""
                    if description:
                        st.write(description[:240] + ("..." if len(description) > 240 else ""))
                with top_cols[1]:
                    st.metric("AI Score", "N/A" if pd.isna(ai_value) else f"{float(ai_value):.1f}")
                with top_cols[2]:
                    st.metric("Judge Avg", "N/A" if pd.isna(avg_judge) else f"{float(avg_judge):.1f}")
                with top_cols[3]:
                    st.markdown("Reviewed" if reviewed else "Pending")
                    if st.button("Review", key=f"review_{submission_id}", use_container_width=True):
                        st.session_state["selected_review_submission_id"] = submission_id
                        st.rerun()
        return

    detail_col, score_col = st.columns([1.1, 0.9])
    with detail_col:
        st.markdown('<div class="section-header">Submission</div>', unsafe_allow_html=True)
        st.subheader(selected.get("project_name") or "Untitled project")
        st.write(selected.get("description") or "No description submitted.")
        if selected.get("submission_url"):
            st.link_button("Open prototype/submission", selected["submission_url"], use_container_width=True)
        show_video_or_link(selected.get("video_url") or "")

        st.markdown('<div class="section-header">Submitted JSON</div>', unsafe_allow_html=True)
        render_submission_json(selected.get("submission_json") or "")

        st.markdown('<div class="section-header">Screenshots</div>', unsafe_allow_html=True)
        render_screenshots(selected.get("screenshots_json") or "")

        st.markdown('<div class="section-header">AI Evaluation</div>', unsafe_allow_html=True)
        ai_score = selected.get("ai_score")
        st.metric("AI Score", "N/A" if pd.isna(ai_score) else f"{float(ai_score):.1f}/100")
        st.info(selected.get("ai_summary") or "AI evaluation has not been run yet.")

        if st.button("Run AI evaluation for this project", use_container_width=True):
            with st.spinner("Running AI evaluation..."):
                try:
                    if selected.get("submission_url"):
                        report = run_live_evaluation(
                            selected["submission_url"],
                            member_name=selected.get("project_name"),
                        )
                    else:
                        data = load_evaluation_data()
                        evaluator = AIEvaluator()
                        report = evaluator.run_evaluation(
                            extraction_data=data.get("extraction_cases", [None])[0],
                            retrieval_data=data.get("retrieval_cases", [None])[0],
                            rag_data=data.get("rag_cases", [None])[0],
                        )
                    update_ai_result(
                        selected_id,
                        report.overall_score,
                        f"AI evaluation completed with run ID {report.run_id}. Overall score: {report.overall_score:.1f}/100.",
                    )
                    st.success("AI evaluation saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"AI evaluation failed: {exc}")

    with score_col:
        st.markdown('<div class="section-header">Your Marks</div>', unsafe_allow_html=True)
        current_score = load_my_score(selected_id, judge_email)
        with st.form("judge_score_form"):
            accuracy = st.slider("Accuracy", 0.0, 10.0, float(current_score["accuracy"]), 0.5)
            completeness = st.slider("Completeness", 0.0, 10.0, float(current_score["completeness"]), 0.5)
            presentation = st.slider("Presentation", 0.0, 10.0, float(current_score["presentation"]), 0.5)
            business_impact = st.slider("Business impact", 0.0, 10.0, float(current_score["business_impact"]), 0.5)
            technical_quality = st.slider("Technical quality", 0.0, 10.0, float(current_score["technical_quality"]), 0.5)
            comments = st.text_area("Comments", value=current_score.get("comments") or "", height=140)
            if st.form_submit_button("Save marks", use_container_width=True):
                try:
                    save_judge_score(
                        selected_id,
                        judge_email,
                        {
                            "accuracy": accuracy,
                            "completeness": completeness,
                            "presentation": presentation,
                            "business_impact": business_impact,
                            "technical_quality": technical_quality,
                            "comments": comments,
                        },
                    )
                    st.success("Marks saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save marks: {exc}")

        st.markdown('<div class="section-header">Judge Responses</div>', unsafe_allow_html=True)
        try:
            scores_df = load_scores(selected_id)
            if scores_df.empty:
                st.caption("No judge responses yet.")
            else:
                st.dataframe(scores_df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not load judge responses: {exc}")


requested_page = str(st.query_params.get("page", "submit")).lower()

if not st.session_state.get("judge_logged_in"):
    if requested_page in {"judge", "login"}:
        st.sidebar.link_button("Open submit page", "?page=submit", use_container_width=True)
        render_login()
    else:
        st.sidebar.empty()
        render_public_submission()
    st.stop()

judge_email = st.session_state["judge_email"]
st.sidebar.markdown(f"Signed in as `{judge_email}`")
st.sidebar.link_button("Open submit page", "?page=submit", use_container_width=True)
if st.sidebar.button("Log out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

portal_view = st.sidebar.radio(
    "View",
    ["Judge Portal", "Submit Project", "AI Evaluation Dashboard"],
    index=1 if requested_page == "submit" else 0,
)

if portal_view == "Judge Portal":
    render_judge_portal(judge_email)
    st.stop()

if portal_view == "Submit Project":
    render_public_submission()
    st.stop()

# Sidebar: Config and Action
st.sidebar.markdown("## 🤖 Framework Controls")

# API Keys status
openai_key_set = "OPENAI_API_KEY" in os.environ or os.getenv("OPENAI_API_KEY") is not None
st.sidebar.markdown(
    f"**OpenAI API Status:** {'🟢 Connected' if openai_key_set else '🔴 Mock Mode'}"
)

# Run Evaluation Button in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Trigger Assessment")
if st.sidebar.button("Run New Pipeline Evaluation", use_container_width=True):
    with st.spinner("Executing evaluation pipeline..."):
        # Load sample data
        data = load_evaluation_data()
        ext_case = data.get("extraction_cases", [None])[0]
        ret_case = data.get("retrieval_cases", [None])[0]
        rag_case = data.get("rag_cases", [None])[0]
        hal_case = data.get("hallucination_cases", [None])[0]
        sales_case = data.get("sales_brief_cases", [None])[0]
        judge_case = data.get("judge_cases", [None])[0]
        
        evaluator = AIEvaluator()
        report = evaluator.run_evaluation(
            extraction_data=ext_case,
            retrieval_data=ret_case,
            rag_data=rag_case,
            hallucination_data={
                "generated_answer": hal_case.get("generated_answer") if hal_case else "",
                "evidence_texts": hal_case.get("evidence_texts") if hal_case else []
            } if hal_case else None,
            sales_brief_data=sales_case,
            judge_data=judge_case
        )
        # Save the report to disk so it appears in the dropdown list
        output_path = REPORTS_DIR / f"report_{report.run_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        sample_path = REPORTS_DIR / "sample_report.json"
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
            
        # Force reload
        st.toast(f"Evaluation {report.run_id} completed successfully!", icon="✅")
        time.sleep(0.5)
        st.rerun()

# Live Submission Evaluation Button in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 Live Prototype Evaluator")
live_url = st.sidebar.text_input("Prototype Base URL:", placeholder="http://localhost:8000")
member_name = st.sidebar.text_input("Member Name (optional):", placeholder="e.g. john_doe")
if st.sidebar.button("Evaluate Remote API", use_container_width=True):
    if not live_url:
        st.sidebar.error("Please enter a valid base URL.")
    else:
        with st.spinner("Connecting to live prototype & evaluating endpoints..."):
            try:
                report = run_live_evaluation(live_url, member_name=member_name)
                st.toast(f"Live Evaluation {report.run_id} completed successfully!", icon="✅")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Evaluation failed: {e}")

# Load existing reports
reports = load_all_reports()

# Main Dashboard Content
st.markdown('<div class="main-title">Project Intelligence Hub (PIH)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Continuous Quality & Performance Assessment Engine</div>', unsafe_allow_html=True)

if not reports:
    st.info("No evaluation runs detected yet. Click 'Run New Pipeline Evaluation' in the sidebar to generate the first run!")
    st.stop()

# Select which run to display
run_ids = [r["run_id"] for r in reports]
run_id_to_label = {r["run_id"]: f"{r['run_id']} (Score: {r.get('overall_score', 0.0):.1f})" for r in reports}
selected_run_id = st.sidebar.selectbox(
    "Select Evaluation Run:", 
    run_ids, 
    index=len(run_ids)-1,
    format_func=lambda x: run_id_to_label.get(x, x)
)
selected_run = next(r for r in reports if r["run_id"] == selected_run_id)

# Overall Score & KPI row
col1, col2, col3, col4 = st.columns(4)

overall_score = selected_run.get("overall_score", 0.0)
perf = selected_run.get("performance", {})
latency = perf.get("latency_ms", 0.0)
cost = perf.get("cost_usd", 0.0)
tokens = perf.get("total_tokens", 0)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Overall System Quality</div>
        <div class="metric-value">{overall_score:.1f}</div>
        <div class="metric-delta delta-positive">Weighted Rubric Score</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Average Latency</div>
        <div class="metric-value">{latency:.0f} ms</div>
        <div class="metric-delta {'delta-positive' if latency < 2000 else 'delta-negative'}">Target: &lt; 500ms</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Estimated Cost</div>
        <div class="metric-value">${cost:.5f}</div>
        <div class="metric-delta delta-positive">Target: &lt; $0.0020</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Tokens Used</div>
        <div class="metric-value">{tokens:,}</div>
        <div class="metric-delta delta-positive">Prompt & Completion</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- Visualizations: Radar & Historical Trends -----------------

tab_overview, tab_details, tab_testbench = st.tabs(["📊 Overview & Trends", "🔍 Deep-Dive Metrics", "🧪 Real-Time Testbench"])

with tab_overview:
    g_col1, g_col2 = st.columns([1, 1])
    
    with g_col1:
        st.markdown('<div class="section-header">Evaluation Category Scores</div>', unsafe_allow_html=True)
        
        # Prepare radar chart variables
        categories = []
        scores = []
        
        ext = selected_run.get("extraction")
        ret = selected_run.get("retrieval")
        rag = selected_run.get("rag")
        hal = selected_run.get("hallucination")
        sb = selected_run.get("sales_brief")
        
        if ext:
            categories.append("Extraction Accuracy")
            scores.append(ext.get("accuracy", 0.0))
            categories.append("Completeness")
            scores.append(ext.get("completeness", 0.0))
        if ret:
            categories.append("Retrieval Quality")
            ret_q = (ret.get("precision_at_k", 0) + ret.get("recall_at_k", 0) + ret.get("mrr", 0) + ret.get("ndcg", 0)) / 4.0 * 100
            scores.append(ret_q)
        if hal:
            categories.append("Hallucination Risk")
            scores.append(100.0 - hal.get("hallucination_rate", 0.0))
        if sb:
            categories.append("Sales Brief Quality")
            scores.append(sb.get("overall", 0.0) * 10.0)
            
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            fillcolor='rgba(20, 184, 166, 0.2)',
            line=dict(color='#14b8a6', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                bgcolor='rgba(15, 23, 42, 0.6)'
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with g_col2:
        st.markdown('<div class="section-header">Historical System Quality Trend</div>', unsafe_allow_html=True)
        
        if len(reports) > 1:
            trend_df = pd.DataFrame([
                {
                    "Timestamp": datetime.fromisoformat(r["timestamp"]).strftime("%m/%d %H:%M"),
                    "Overall Score": r["overall_score"],
                    "Latency (ms)": r.get("performance", {}).get("latency_ms", 0.0),
                    "Cost ($)": r.get("performance", {}).get("cost_usd", 0.0)
                }
                for r in reports
            ])
            
            fig_trend = px.line(
                trend_df,
                x="Timestamp",
                y="Overall Score",
                markers=True,
                color_discrete_sequence=["#3b82f6"]
            )
            fig_trend.update_layout(
                yaxis=dict(range=[0, 105]),
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("Only 1 run recorded. Perform multiple evaluation runs to visualize historical trends.")
            
# ----------------- Deep Dive Subsystem Reports -----------------

with tab_details:
    st.markdown('<div class="section-header">System Sub-component Evaluations</div>', unsafe_allow_html=True)
    
    sub_tabs = st.tabs([
        "📤 Information Extraction", 
        "🔍 Semantic Search / Retrieval", 
        "💬 RAG & Faithfulness",
        "🎯 Hallucination Details",
        "📄 Sales Brief Grader",
        "👨‍⚖️ LLM-as-a-Judge"
    ])
    
    # 1. Extraction Tab
    with sub_tabs[0]:
        if ext:
            col_ex1, col_ex2 = st.columns([1, 2])
            with col_ex1:
                st.markdown("#### Extraction Summary Metrics")
                st.write(f"**Field Accuracy:** {ext.get('accuracy')}%")
                st.write(f"**Field Completeness:** {ext.get('completeness')}%")
                st.write(f"**Citation Coverage:** {ext.get('citation_coverage')}%")
                st.write(f"**Missing Field Detection:** {ext.get('missing_field_detection')}%")
                st.write(f"**Confidence Score:** {ext.get('confidence_score')}%")
                
            with col_ex2:
                st.markdown("#### Field-by-Field Audit Log")
                details_dict = ext.get("field_details", {})
                
                rows = []
                for fname, res in details_dict.items():
                    rows.append({
                        "Field": fname,
                        "Expected Value": res.get("expected_value"),
                        "Extracted Value": res.get("extracted_value"),
                        "Correct": "✅" if res.get("is_correct") else "❌",
                        "Citation Valid": "✅" if res.get("citation_valid") else "❌" if res.get("citation_provided") else "N/A",
                        "Comments": res.get("comments")
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("No Information Extraction data present in this run.")

    # 2. Retrieval Tab
    with sub_tabs[1]:
        if ret:
            col_ret1, col_ret2 = st.columns([1, 2])
            with col_ret1:
                st.markdown("#### Search Engine Metrics")
                st.write(f"**Precision@K:** {ret.get('precision_at_k')}")
                st.write(f"**Recall@K:** {ret.get('recall_at_k')}")
                st.write(f"**Mean Reciprocal Rank (MRR):** {ret.get('mrr')}")
                st.write(f"**NDCG:** {ret.get('ndcg')}")
                st.write(f"**Semantic Relevance Score:** {ret.get('relevance_score')}")
                
            with col_ret2:
                st.markdown("#### Retrieval Sequence")
                # Visualizing ranking sequence
                st.write("Rank position of retrieved projects (targets in green):")
                # In sample: we don't have full data in the model, but we can display the list
                st.write("*Query:* AWS database migration projects with revenue over $200k")
                st.markdown("""
                1. 🟢 **Project Apex** (Expected)
                2. 🟢 **Project Titan** (Expected)
                3. 🔴 **Project Nebula** (Irrelevant)
                4. 🔴 **Project Genesis** (Irrelevant)
                5. 🟢 **Project Horizon** (Expected)
                """)
        else:
            st.info("No Retrieval data present in this run.")

    # 3. RAG Tab
    with sub_tabs[2]:
        if rag:
            col_rag1, col_rag2 = st.columns([1, 2])
            with col_rag1:
                st.markdown("#### RAG Triad Assessment")
                st.write(f"**Faithfulness:** {rag.get('faithfulness')}")
                st.write(f"**Answer Relevancy:** {rag.get('answer_relevancy')}")
                st.write(f"**Groundedness:** {rag.get('groundedness')}")
                st.write(f"**Context Precision:** {rag.get('context_precision')}")
                st.write(f"**Context Recall:** {rag.get('context_recall')}")
                
            with col_rag2:
                st.markdown("#### Sample Answer Review")
                st.markdown("**Query:** What were the outcomes and total revenue of Project Apex?")
                st.info("**Generated Answer:** Project Apex achieved significant outcomes, including a 45% reduction in database licensing costs and a 30% reduction in query latency. The total revenue generated from the project was $250,000 under a time and materials billing structure.")
                st.success("**Ground Truth Answer:** The outcomes of Project Apex were a 45% reduction in licensing costs and a 30% reduction in database response latency. The total revenue for the project was $250,000.")
        else:
            st.info("No RAG data present in this run.")

    # 4. Hallucination Tab
    with sub_tabs[3]:
        if hal:
            col_hal1, col_hal2 = st.columns([1, 2])
            with col_hal1:
                st.markdown("#### Hallucination Audit")
                st.write(f"**Supported Claims:** {hal.get('supported_claims')}")
                st.write(f"**Total Claims Extracted:** {hal.get('total_claims')}")
                
                rate = hal.get('hallucination_rate', 0.0)
                st.metric(
                    label="Hallucination Rate",
                    value=f"{rate}%",
                    delta=f"{rate}% unsupported",
                    delta_color="inverse"
                )
                
            with col_hal2:
                st.markdown("#### Factual Claim Audit Log")
                claims_list = hal.get("claims", [])
                
                for claim_item in claims_list:
                    claim_text = claim_item.get("claim")
                    supported = claim_item.get("is_supported")
                    evidence = claim_item.get("evidence")
                    reason = claim_item.get("reasoning")
                    
                    if supported:
                        st.markdown(f"""
                        <div class="claim-box claim-supported">
                            <strong>✅ Supported Claim:</strong> {claim_text}<br/>
                            <small><em>Evidence:</em> {evidence}</small><br/>
                            <small><em>Reasoning:</em> {reason}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="claim-box claim-unsupported">
                            <strong>❌ Hallucinated/Unsupported Claim:</strong> {claim_text}<br/>
                            <small><em>Evidence:</em> {evidence or 'None'}</small><br/>
                            <small><em>Reasoning:</em> {reason}</small>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No Hallucination data present in this run.")

    # 5. Sales Brief Tab
    with sub_tabs[4]:
        if sb:
            col_sb1, col_sb2 = st.columns([1, 2])
            with col_sb1:
                st.markdown("#### Rubric Grades (1-10)")
                st.write(f"**Readability:** {sb.get('readability')}")
                st.write(f"**Professionalism:** {sb.get('professionalism')}")
                st.write(f"**Evidence Usage:** {sb.get('evidence_usage')}")
                st.write(f"**Completeness:** {sb.get('completeness')}")
                st.write(f"**Persuasiveness:** {sb.get('persuasiveness')}")
                st.write(f"**Business Value:** {sb.get('business_value')}")
                st.write(f"**Overall Average Score:** {sb.get('overall')}")
                
            with col_sb2:
                st.markdown("#### Auditor Feedback")
                st.success(sb.get("feedback", "No feedback recorded."))
        else:
            st.info("No Sales Brief data present in this run.")

    # 6. Judge Tab
    with sub_tabs[5]:
        if selected_run.get("judge"):
            jd = selected_run["judge"]
            col_jd1, col_jd2 = st.columns([1, 2])
            with col_jd1:
                st.markdown("#### Judge Quality Scores (1-10)")
                st.write(f"**Accuracy:** {jd.get('accuracy')}")
                st.write(f"**Completeness:** {jd.get('completeness')}")
                st.write(f"**Relevance:** {jd.get('relevance')}")
                st.write(f"**Groundedness:** {jd.get('groundedness')}")
                st.write(f"**Usefulness:** {jd.get('usefulness')}")
                st.write(f"**Overall Judge Score:** {jd.get('overall')}")
                
            with col_jd2:
                st.markdown("#### Judge Reasoning")
                st.info(jd.get("reasoning", "No reasoning recorded."))
        else:
            st.info("No LLM-as-a-Judge data present in this run.")

# ----------------- Interactive Testbench -----------------

with tab_testbench:
    st.markdown('<div class="section-header">Evaluation Testbench Playground</div>', unsafe_allow_html=True)
    st.write("Input a custom query, generation, and contexts below to run an evaluation on the fly.")
    
    with st.form("interactive_eval_form"):
        play_query = st.text_input("User Search Query", "What database was used in Project Apex?")
        
        play_contexts = st.text_area(
            "Retrieved Context blocks (one per line)",
            "Project Apex migrated database systems to AWS Aurora PostgreSQL, lowering licensing costs by 45%.\nThe project was completed in Q3 2024 for Acme Corp."
        )
        
        play_answer = st.text_area(
            "System Generated Answer",
            "Project Apex utilized the AWS Aurora PostgreSQL cloud database engine."
        )
        
        play_ground_truth = st.text_input("Ground Truth Answer (Reference)", "AWS Aurora PostgreSQL database.")
        
        submit_btn = st.form_submit_button("Execute Real-Time Assessment")
        
        if submit_btn:
            with st.spinner("Executing custom evaluator..."):
                contexts_list = [c.strip() for c in play_contexts.split("\n") if c.strip()]
                
                # Assemble request
                rag_in = {
                    "query": play_query,
                    "contexts": contexts_list,
                    "generated_answer": play_answer,
                    "ground_truth_answer": play_ground_truth
                }
                
                hal_in = {
                    "generated_answer": play_answer,
                    "evidence_texts": contexts_list
                }
                
                evaluator = AIEvaluator()
                custom_report = evaluator.run_evaluation(
                    rag_data=rag_in,
                    hallucination_data=hal_in
                )
                
                st.success("Custom evaluation run complete!")
                
                st.markdown("### Resulting Metrics")
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.write(f"**Overall Score:** {custom_report.overall_score:.2f}")
                    st.write(f"**RAG Faithfulness:** {custom_report.rag.faithfulness if custom_report.rag else 0.0}")
                    st.write(f"**RAG Answer Relevancy:** {custom_report.rag.answer_relevancy if custom_report.rag else 0.0}")
                with res_col2:
                    st.write(f"**Hallucination Rate:** {custom_report.hallucination.hallucination_rate if custom_report.hallucination else 0.0}%")
                    st.write(f"**Latency:** {custom_report.performance.latency_ms:.1f} ms")
                    st.write(f"**Cost:** ${custom_report.performance.cost_usd:.5f}")
