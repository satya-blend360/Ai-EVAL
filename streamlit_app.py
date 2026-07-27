import os
import json
import time
import re
import uuid
import base64
from urllib import error, request
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
SRC_ROOT = os.path.join(APP_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

REPORTS_DIR = Path(APP_ROOT) / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def reset_ai_eval_import_cache() -> None:
    import importlib

    importlib.invalidate_caches()
    for module_name in list(sys.modules):
        if module_name == "ai_eval" or module_name.startswith("ai_eval."):
            sys.modules.pop(module_name, None)


def create_ai_evaluator():
    reset_ai_eval_import_cache()
    from ai_eval.core.evaluator import AIEvaluator

    return AIEvaluator()


def load_evaluation_dataset():
    reset_ai_eval_import_cache()
    from ai_eval.data.loader import load_evaluation_data

    return load_evaluation_data()


def run_live_prototype_evaluation(base_url: str, member_name: Optional[str] = None):
    reset_ai_eval_import_cache()
    sys.modules.pop("evaluate_submission", None)
    from evaluate_submission import run_live_evaluation

    return run_live_evaluation(base_url, member_name=member_name)


def show_optional_evaluator_error(exc: Exception) -> None:
    st.error(
        "The optional AI evaluation module could not load in this environment. "
        "The submission and judge portal pages are still available."
    )
    st.caption(f"Evaluator error: {type(exc).__name__}: {exc}")

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

    /* Judge review status badges */
    .review-status-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 10px;
        border: 1px solid transparent;
    }
    .review-status-reviewed {
        background-color: rgba(16, 185, 129, 0.14);
        border-color: rgba(16, 185, 129, 0.42);
        color: #a7f3d0;
    }
    .review-status-pending {
        background-color: rgba(245, 158, 11, 0.14);
        border-color: rgba(245, 158, 11, 0.46);
        color: #fde68a;
    }

</style>
""", unsafe_allow_html=True)

# Helper function to load reports from filesystem
def hide_public_submission_sidebar() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            [data-testid="collapsedControl"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
MAX_SCREENSHOTS = 5
MAX_JSON_CHARS = 100_000
MAX_TEXT_CHARS = 5_000
DATABRICKS_PARAMETER_LIMIT_CHARS = 1_048_576
SUBMISSION_PARAMETER_LIMIT_CHARS = 900_000
MAX_COMBINED_UPLOAD_BYTES = 600 * 1024
MAX_SINGLE_SCREENSHOT_BYTES = 150 * 1024
MAX_SCREENSHOT_BYTES = MAX_COMBINED_UPLOAD_BYTES
MAX_SALES_BRIEF_BYTES = 450 * 1024


def safe_identifier(value: str, default: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""):
        return value
    return default


DB_CATALOG = safe_identifier(DB_CATALOG, "sandbox")
DB_SCHEMA = safe_identifier(DB_SCHEMA, "ai_eval_judge_portal")
DB_PREFIX = f"{DB_CATALOG}.{DB_SCHEMA}"
JUDGE_READY_QUESTIONS_PATH = Path(APP_ROOT) / "judge_ready_evaluation_questions.md"
PIH_HACKATHON_DOC_PATH = Path(APP_ROOT) / "pih_hackathon_design_qa_extracted.md"

PIH_SCORE_FIELDS = [
    {
        "storage_key": "accuracy",
        "display": "Creativity, insight & relevance",
        "short": "Creativity",
        "help": "1: loosely tied to the project-knowledge problem. 2: straightforward but familiar. 3: clear solution with useful creative features. 4: highly original, thoughtful, and grounded in real user need.",
    },
    {
        "storage_key": "completeness",
        "display": "Answering from existing materials",
        "short": "Grounded answers",
        "help": "1: answers absent, wrong, or ungrounded. 2: some answers but weak coverage or sourcing. 3: reliable answers grounded in files with visible sources. 4: accurate held-out answers and works beyond the test phrasing.",
    },
    {
        "storage_key": "presentation",
        "display": "Gap-flagging & knowledge capture",
        "short": "Gap capture",
        "help": "1: gaps are not handled. 2: gaps are flagged but guidance or persistence is weak. 3: flags gaps, suggests who/how to close them, and captures answers. 4: smooth flag-guide-capture-persist loop.",
    },
    {
        "storage_key": "business_impact",
        "display": "Usable experience (MVP)",
        "short": "Usability",
        "help": "1: mostly concept; hard to use. 2: works but rough. 3: usable core workflow in chat, Cowork, agent, skill, or UI. 4: smooth, complete end-to-end experience.",
    },
    {
        "storage_key": "technical_quality",
        "display": "Impact & potential",
        "short": "Impact",
        "help": "1: limited practical value. 2: some potential but unclear audience or scale. 3: clear real-world value. 4: strong path to a scalable Blend tool.",
    },
]
PIH_SCORE_MAX = len(PIH_SCORE_FIELDS) * 4


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


def format_file_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / 1024:.0f} KB"


def uploaded_file_size(uploaded_file: Any) -> int:
    if uploaded_file is None:
        return 0
    size = getattr(uploaded_file, "size", None)
    if isinstance(size, int):
        return size
    return len(uploaded_file.getvalue())


def total_uploaded_file_size(screenshot_files: Any, sales_brief_file: Any) -> int:
    return sum(uploaded_file_size(file) for file in screenshot_files or []) + uploaded_file_size(sales_brief_file)


def combine_description_with_source_link(description: str, source_code_url: str) -> str:
    description = (description or "").strip()
    source_code_url = (source_code_url or "").strip()
    if not source_code_url:
        return description
    parts = [part for part in [description, f"Source code URL: {source_code_url}"] if part]
    return "\n\n".join(parts)


def db_configured() -> bool:
    return all(
        [
            get_secret("DATABRICKS_SERVER_HOSTNAME"),
            get_secret("DATABRICKS_HTTP_PATH"),
            get_secret("DATABRICKS_TOKEN"),
        ]
    )


def databricks_host_url() -> str:
    hostname = get_secret("DATABRICKS_SERVER_HOSTNAME").strip()
    if not hostname:
        return ""
    if not re.match(r"^https?://", hostname, flags=re.IGNORECASE):
        hostname = f"https://{hostname}"
    return hostname.rstrip("/")


def databricks_warehouse_id() -> str:
    configured_id = get_secret("DATABRICKS_WAREHOUSE_ID").strip()
    if configured_id:
        return configured_id

    match = re.search(r"/warehouses/([^/?#]+)", get_secret("DATABRICKS_HTTP_PATH"))
    return match.group(1) if match else ""


def warehouse_http_path_from_id(warehouse_id: str) -> str:
    return f"/sql/1.0/warehouses/{warehouse_id.strip()}" if warehouse_id.strip() else ""


def backup_databricks_warehouse_id() -> str:
    return (
        get_secret("DATABRICKS_BACKUP_WAREHOUSE_ID").strip()
        or get_secret("DATABRICKS_FALLBACK_WAREHOUSE_ID").strip()
    )


def backup_databricks_http_path() -> str:
    configured_path = (
        get_secret("DATABRICKS_BACKUP_HTTP_PATH").strip()
        or get_secret("DATABRICKS_FALLBACK_HTTP_PATH").strip()
    )
    if configured_path:
        return configured_path
    return warehouse_http_path_from_id(backup_databricks_warehouse_id())


def databricks_warehouse_targets() -> List[Dict[str, str]]:
    backup_path = backup_databricks_http_path()
    backup_id = backup_databricks_warehouse_id()
    if backup_path and not backup_id:
        match = re.search(r"/warehouses/([^/?#]+)", backup_path)
        backup_id = match.group(1) if match else ""

    targets = [
        {
            "role": "Primary",
            "name": "Starter Warehouse",
            "warehouse_id": databricks_warehouse_id(),
            "http_path": get_secret("DATABRICKS_HTTP_PATH").strip(),
        }
    ]
    if backup_path and backup_path != targets[0]["http_path"]:
        targets.append(
            {
                "role": "Backup",
                "name": "forPIH_Hackathon",
                "warehouse_id": backup_id,
                "http_path": backup_path,
            }
        )
    return [target for target in targets if target["http_path"] and target["warehouse_id"]]


def databricks_query_warehouse_targets() -> List[Dict[str, str]]:
    targets = databricks_warehouse_targets()
    if len(targets) < 2:
        return targets

    primary = targets[0]
    try:
        primary_status = load_warehouse_status(primary["warehouse_id"])
        primary_state = str(primary_status.get("state", "")).upper()
    except Exception:
        return targets

    if primary_state == "RUNNING":
        return targets
    return targets[1:] + [primary]


def warehouse_api_configured() -> bool:
    return all(
        [
            databricks_host_url(),
            get_secret("DATABRICKS_TOKEN"),
            databricks_warehouse_id(),
        ]
    )


def run_databricks_api(
    path: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not warehouse_api_configured():
        raise RuntimeError("Databricks warehouse API configuration is incomplete.")

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    api_request = request.Request(
        f"{databricks_host_url()}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {get_secret('DATABRICKS_TOKEN')}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(api_request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Databricks API returned {exc.code}: {details or exc.reason}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach Databricks API: {exc.reason}") from exc

    return json.loads(response_body) if response_body else {}


@st.cache_data(ttl=20)
def load_warehouse_status(warehouse_id: str = "") -> Dict[str, Any]:
    warehouse_id = warehouse_id or databricks_warehouse_id()
    if not warehouse_id:
        raise RuntimeError("No Databricks warehouse id was found.")
    return run_databricks_api(f"/api/2.0/sql/warehouses/{warehouse_id}")


def start_warehouse(warehouse_id: str = "") -> None:
    warehouse_id = warehouse_id or databricks_warehouse_id()
    if not warehouse_id:
        raise RuntimeError("No Databricks warehouse id was found.")
    run_databricks_api(f"/api/2.0/sql/warehouses/{warehouse_id}/start", method="POST", payload={})
    load_warehouse_status.clear()


def render_starter_warehouse_sidebar() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Starter Warehouse")

    if not warehouse_api_configured():
        st.sidebar.caption("Warehouse status unavailable. Configure `DATABRICKS_WAREHOUSE_ID` or a warehouse `DATABRICKS_HTTP_PATH`.")
        return

    for target in databricks_query_warehouse_targets():
        try:
            warehouse = load_warehouse_status(target["warehouse_id"])
            state = str(warehouse.get("state", "UNKNOWN")).upper()
            name = warehouse.get("name") or target["name"]
            active = state == "RUNNING"
            status_icon = "🟢" if active else "🟡" if state in {"STARTING", "RESIZING"} else "🔴"

            st.sidebar.markdown(f"**{target['role']} - {name}:** {status_icon} {state.title()}")
            if not active and target["role"] == "Primary":
                starting = state in {"STARTING", "RESIZING"}
                if st.sidebar.button(
                    "Start Starter Warehouse",
                    use_container_width=True,
                    disabled=starting,
                ):
                    try:
                        start_warehouse(target["warehouse_id"])
                        st.sidebar.success("Start requested.")
                        st.rerun()
                    except Exception as exc:
                        st.sidebar.error(f"Could not start warehouse: {exc}")
        except Exception as exc:
            st.sidebar.error(f"Could not load {target['role'].lower()} warehouse status: {exc}")

    active_target = st.session_state.get("active_warehouse_role")
    if active_target:
        st.sidebar.caption(f"Last DB connection used: {active_target}")

def run_db_query(query: str, parameters: Optional[Dict[str, Any]] = None, fetch: bool = False):
    if not db_configured():
        raise RuntimeError("Databricks secrets are not configured.")
    try:
        from databricks import sql
    except ImportError as exc:
        raise RuntimeError("databricks-sql-connector is not installed.") from exc

    errors = []
    for target in databricks_warehouse_targets():
        try:
            with sql.connect(
                server_hostname=get_secret("DATABRICKS_SERVER_HOSTNAME"),
                http_path=target["http_path"],
                access_token=get_secret("DATABRICKS_TOKEN"),
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, parameters=parameters or {})
                    st.session_state["active_warehouse_role"] = (
                        f"{target['role']} - {target['name']}"
                    )
                    if not fetch:
                        return None
                    rows = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    return pd.DataFrame(rows, columns=columns)
        except Exception as exc:
            errors.append(f"{target['role']} {target['name']}: {exc}")
            continue

    raise RuntimeError("All configured Databricks warehouses failed. " + " | ".join(errors))


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text.strip().lower())


def load_correct_answer_key() -> List[Dict[str, Any]]:
    if not JUDGE_READY_QUESTIONS_PATH.exists():
        return []
    content = JUDGE_READY_QUESTIONS_PATH.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^## Question\s+(\d+)\s*$", content)
    questions = []
    for index in range(1, len(blocks), 2):
        question_number = int(blocks[index])
        body = blocks[index + 1]
        item = {"question_number": question_number}
        for field in ["question", "answer", "question_type", "match_keywords"]:
            match = re.search(
                rf"(?ms)^{field}:\s*\n(.*?)(?=\n(?:file_name|question|answer|answer_source|question_type|match_keywords):|\n## Question|\Z)",
                body,
            )
            item[field] = match.group(1).strip() if match else ""

        source_match = re.search(
            r"(?ms)^answer_source:\s*\n(.*?)(?=\n(?:file_name|question|answer|answer_source|question_type|match_keywords):|\n## Question|\Z)",
            body,
        )
        sources = []
        if source_match:
            sources = [
                line[2:].strip()
                for line in source_match.group(1).splitlines()
                if line.strip().startswith("- ")
            ]
        item["answer_source"] = sources
        item["match_keywords_list"] = [
            keyword.strip()
            for keyword in item.get("match_keywords", "").split(";")
            if keyword.strip()
        ]
        questions.append(item)
    return questions


def correct_answer_key_json() -> str:
    return json.dumps(load_correct_answer_key(), ensure_ascii=False)


def coerce_pih_score(value: Any) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 3
    if numeric > 4:
        numeric = numeric / 10.0 * 4.0
    return int(min(4, max(1, round(numeric))))


def pih_total_score(values: Dict[str, Any]) -> float:
    return float(sum(coerce_pih_score(values[field["storage_key"]]) for field in PIH_SCORE_FIELDS))


def render_hackathon_scoring_guide() -> None:
    if st.sidebar.button("Open scoring guide", use_container_width=True):
        st.session_state["show_scorecard_dialog"] = True
    if st.session_state.get("show_scorecard_dialog"):
        render_scorecard_dialog()


def format_judge_scores_for_display(scores_df: pd.DataFrame) -> pd.DataFrame:
    if scores_df.empty:
        return scores_df
    formatted = scores_df.copy()
    score_columns = [field["storage_key"] for field in PIH_SCORE_FIELDS]
    for column in score_columns:
        if column in formatted.columns:
            formatted[column] = formatted[column].apply(coerce_pih_score)
    if all(column in formatted.columns for column in score_columns):
        formatted["total_score"] = formatted[score_columns].sum(axis=1)
    rename_map = {
        "accuracy": "Creativity",
        "completeness": "Grounded Answers",
        "presentation": "Gap Capture",
        "business_impact": "Usability",
        "technical_quality": "Impact",
        "total_score": "Total / 20",
        "judge_email": "Judge",
        "comments": "Comments",
        "updated_at": "Updated",
    }
    return formatted.rename(columns=rename_map)


def render_scorecard_content() -> None:
    st.markdown("**Total:** 20 points. Score each criterion from 1 to 4, then sum all five criteria.")
    scale_cols = st.columns(4)
    scale_cols[0].metric("1", "Underachieving")
    scale_cols[1].metric("2", "Average")
    scale_cols[2].metric("3", "Proficient")
    scale_cols[3].metric("4", "Exceptional")

    for field in PIH_SCORE_FIELDS:
        with st.container(border=True):
            st.markdown(f"#### {field['display']}")
            st.write(field["help"])

    st.markdown("#### What Judges Should Look For")
    st.write("Grounded answers with the source visible, a quick accuracy tally, and a flag-guide-capture-persist loop for unanswered questions.")
    st.markdown("#### Required Submission Artifacts")
    st.write("Demo video, test-set answers, and one generated project one-pager / sales brief.")
    st.caption("Source: pih_hackathon_design_qa_extracted.md")


@st.dialog("PIH Hackathon Scorecard", width="large")
def render_scorecard_dialog() -> None:
    render_scorecard_content()
    if st.button("Close scoring guide", use_container_width=True):
        st.session_state["show_scorecard_dialog"] = False
        st.rerun()


def find_nested_answer_container(payload: Any) -> Any:
    if isinstance(payload, dict):
        for key in ["answers", "responses", "results", "questions", "items", "data"]:
            if isinstance(payload.get(key), list):
                return payload[key]
        return payload
    return payload


def extract_submitted_answers(submission_json: str) -> Dict[int, str]:
    if not submission_json:
        return {}
    try:
        payload = json.loads(submission_json)
    except Exception:
        return {}
    payload = find_nested_answer_container(payload)
    answers: Dict[int, str] = {}

    if isinstance(payload, list):
        for position, item in enumerate(payload, start=1):
            if isinstance(item, dict):
                raw_id = (
                    item.get("question_number")
                    or item.get("question_id")
                    or item.get("id")
                    or item.get("number")
                    or item.get("q")
                    or position
                )
                answer = (
                    item.get("answer")
                    or item.get("submitted_answer")
                    or item.get("response")
                    or item.get("output")
                    or item.get("value")
                    or ""
                )
            else:
                raw_id = position
                answer = item
            question_number = parse_question_number(raw_id, position)
            answers[question_number] = str(answer)
        return answers

    if isinstance(payload, dict):
        for position, (key, value) in enumerate(payload.items(), start=1):
            question_number = parse_question_number(key, position)
            if isinstance(value, dict):
                answer = (
                    value.get("answer")
                    or value.get("submitted_answer")
                    or value.get("response")
                    or value.get("output")
                    or value.get("value")
                    or ""
                )
            else:
                answer = value
            answers[question_number] = str(answer)
    return answers


def parse_question_number(raw_id: Any, fallback: int) -> int:
    if isinstance(raw_id, (int, float)):
        return int(raw_id)
    match = re.search(r"\d+", str(raw_id or ""))
    return int(match.group(0)) if match else fallback


def score_submission_against_key(submission_json: str) -> Dict[str, Any]:
    key = load_correct_answer_key()
    submitted_answers = extract_submitted_answers(submission_json)
    details = []
    if not key:
        return {
            "score": None,
            "summary": "No correct answer key is available.",
            "details": details,
            "correct_answers": key,
        }

    for expected in key:
        question_number = expected["question_number"]
        submitted_answer = submitted_answers.get(question_number, "")
        submitted_text = normalize_text(submitted_answer)
        keywords = expected.get("match_keywords_list", [])
        matched_keywords = [
            keyword for keyword in keywords if normalize_text(keyword) and normalize_text(keyword) in submitted_text
        ]
        keyword_score = len(matched_keywords) / len(keywords) if keywords else 0.0
        expected_answer_text = normalize_text(expected.get("answer"))
        exactish_score = 1.0 if expected_answer_text and expected_answer_text in submitted_text else 0.0
        score = max(keyword_score, exactish_score)
        details.append(
            {
                "question_number": question_number,
                "question": expected.get("question", ""),
                "submitted_answer": submitted_answer,
                "correct_answer": expected.get("answer", ""),
                "matched_keywords": matched_keywords,
                "missing_keywords": [keyword for keyword in keywords if keyword not in matched_keywords],
                "score": round(score * 100, 2),
                "answer_source": expected.get("answer_source", []),
            }
        )

    answered = sum(1 for detail in details if detail["submitted_answer"].strip())
    score = round(sum(detail["score"] for detail in details) / len(details), 2) if details else None
    summary = f"Matched {answered}/{len(details)} questions. Automatic keyword score: {score:.1f}/100."
    return {
        "score": score,
        "summary": summary,
        "details": details,
        "correct_answers": key,
    }


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
            "correct_answers_json": correct_answer_key_json(),
            "correctness_score": None,
            "correctness_summary": "No submitted answers for this seed row.",
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
            "correct_answers_json": correct_answer_key_json(),
            "correctness_score": None,
            "correctness_summary": "No submitted answers for this seed row.",
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
        row.setdefault("correct_answers_json", correct_answer_key_json())
        row.setdefault("correctness_score", None)
        row.setdefault("correctness_summary", "Automatic correctness score has not been calculated.")
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
            s.correct_answers_json,
            s.correctness_score,
            s.correctness_summary,
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
        "accuracy": 3,
        "completeness": 3,
        "presentation": 3,
        "business_impact": 3,
        "technical_quality": 3,
        "comments": "",
    }
    if not db_configured():
        score = st.session_state.setdefault("local_judge_scores", {}).get(
            f"{submission_id}:{judge_email}", defaults
        )
        score = {**defaults, **score}
        for field in PIH_SCORE_FIELDS:
            score[field["storage_key"]] = coerce_pih_score(score.get(field["storage_key"]))
        return score
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
    score = {**defaults, **{k: row.get(k, defaults[k]) for k in defaults}}
    for field in PIH_SCORE_FIELDS:
        score[field["storage_key"]] = coerce_pih_score(score.get(field["storage_key"]))
    return score


def save_judge_score(submission_id: str, judge_email: str, values: Dict[str, Any]) -> None:
    total_score = pih_total_score(values)
    score = {
        "score_id": f"score_{uuid.uuid4().hex[:12]}",
        "submission_id": submission_id,
        "judge_email": judge_email,
        "accuracy": coerce_pih_score(values["accuracy"]),
        "completeness": coerce_pih_score(values["completeness"]),
        "presentation": coerce_pih_score(values["presentation"]),
        "business_impact": coerce_pih_score(values["business_impact"]),
        "technical_quality": coerce_pih_score(values["technical_quality"]),
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
    correctness = score_submission_against_key(values.get("submission_json", ""))
    submission = {
        "submission_id": f"sub_{uuid.uuid4().hex[:12]}",
        "project_name": values["project_name"],
        "submitter_name": values["submitter_name"],
        "submitter_email": values["submitter_email"],
        "submission_url": values["submission_url"],
        "video_url": values["video_url"],
        "description": values["description"],
        "submission_json": values.get("submission_json", ""),
        "correct_answers_json": correct_answer_key_json(),
        "correctness_score": correctness["score"],
        "correctness_summary": correctness["summary"],
        "screenshots_json": values.get("screenshots_json", "[]"),
    }
    if not db_configured():
        st.session_state.setdefault("local_extra_submissions", []).append(submission)
        load_submissions.clear()
        return
    parameter_chars = estimate_databricks_parameter_chars(submission)
    if parameter_chars > SUBMISSION_PARAMETER_LIMIT_CHARS:
        raise ValueError(
            f"Submission payload is too large for Databricks SQL ({parameter_chars:,} characters). "
            f"Keep the saved payload under {SUBMISSION_PARAMETER_LIMIT_CHARS:,} characters. "
            "Please compress screenshots/sales brief, upload fewer files, or share large artifacts as links."
        )
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
            correct_answers_json,
            correctness_score,
            correctness_summary,
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
            :correct_answers_json,
            :correctness_score,
            :correctness_summary,
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


def run_standard_submission_evaluation(selected: Dict[str, Any]):
    data = load_evaluation_dataset()
    evaluator = create_ai_evaluator()
    project_name = normalize_text(selected.get("project_name"))

    if "horizon" in project_name:
        hallucination_case = data.get("hallucination_cases", [None])[0]
        return evaluator.run_evaluation(
            hallucination_data={
                "generated_answer": hallucination_case.get("generated_answer") if hallucination_case else "",
                "evidence_texts": hallucination_case.get("evidence_texts") if hallucination_case else [],
            }
            if hallucination_case
            else None
        )

    extraction_case = data.get("extraction_cases", [None])[0]
    retrieval_case = data.get("retrieval_cases", [None])[0]
    rag_case = data.get("rag_cases", [None])[0]
    sales_case = data.get("sales_brief_cases", [None])[0]
    return evaluator.run_evaluation(
        extraction_data=extraction_case,
        retrieval_data=retrieval_case,
        rag_data=rag_case,
        sales_brief_data=sales_case,
    )


def should_fallback_to_standard_evaluation(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        signal in message
        for signal in [
            "http error 404",
            "http error 405",
            "method not allowed",
            "not found",
            "expecting value",
        ]
    )


def encode_submission_files(screenshot_files, sales_brief_file=None) -> str:
    files = []
    total_bytes = 0
    combined_upload_bytes = total_uploaded_file_size(screenshot_files, sales_brief_file)
    if combined_upload_bytes > MAX_COMBINED_UPLOAD_BYTES:
        raise ValueError(
            f"Uploaded files total {format_file_size(combined_upload_bytes)}. "
            f"Keep screenshots plus sales brief under {format_file_size(MAX_COMBINED_UPLOAD_BYTES)} total, "
            "or share large files as links."
        )
    if len(screenshot_files or []) > MAX_SCREENSHOTS:
        raise ValueError(f"Upload {MAX_SCREENSHOTS} screenshots or fewer.")
    for uploaded_file in screenshot_files or []:
        content = uploaded_file.getvalue()
        if len(content) > MAX_SINGLE_SCREENSHOT_BYTES:
            raise ValueError(
                f"{uploaded_file.name} is {format_file_size(len(content))}. "
                f"Each screenshot must be {format_file_size(MAX_SINGLE_SCREENSHOT_BYTES)} or less."
            )
        total_bytes += len(content)
        if total_bytes > MAX_SCREENSHOT_BYTES:
            raise ValueError(
                f"Screenshot uploads must be {format_file_size(MAX_SCREENSHOT_BYTES)} or less in total."
            )
        files.append(
            {
                "name": uploaded_file.name,
                "mime_type": uploaded_file.type or "image/png",
                "size_bytes": len(content),
                "data_base64": base64.b64encode(content).decode("ascii"),
                "category": "screenshot",
            }
        )

    if sales_brief_file is not None:
        content = sales_brief_file.getvalue()
        if len(content) > MAX_SALES_BRIEF_BYTES:
            raise ValueError(f"Sales brief upload must be {format_file_size(MAX_SALES_BRIEF_BYTES)} or less.")
        files.append(
            {
                "name": sales_brief_file.name,
                "mime_type": sales_brief_file.type or "application/octet-stream",
                "size_bytes": len(content),
                "data_base64": base64.b64encode(content).decode("ascii"),
                "category": "sales_brief",
            }
        )
    return json.dumps(files)


def estimate_databricks_parameter_chars(parameters: Dict[str, Any]) -> int:
    return sum(len("" if value is None else str(value)) for value in parameters.values())


def encode_screenshots(uploaded_files) -> str:
    return encode_submission_files(uploaded_files)


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

    submitted_answers = extract_submitted_answers(submission_json)
    size_kb = len(submission_json.encode("utf-8")) / 1024
    st.success("JSON payload submitted. Raw JSON is hidden from the judge page.")
    if submitted_answers:
        st.caption(f"{len(submitted_answers)} answer(s) detected. Use the comparison below for review.")
    else:
        st.caption("Submitted payload is stored, but no numbered answers were detected.")
    st.download_button(
        "Download submitted JSON",
        data=submission_json,
        file_name="submitted_project_answers.json",
        mime="application/json",
        help="Download only if you need to inspect the raw participant payload.",
        use_container_width=True,
        key=f"submitted_json_download_{len(submission_json)}_{int(size_kb * 100)}",
    )


def render_correctness_assessment(submission_json: str, stored_summary: str = "", stored_score: Any = None) -> None:
    assessment = score_submission_against_key(submission_json)
    score = stored_score
    if score is None or pd.isna(score):
        score = assessment.get("score")
    summary = stored_summary or assessment.get("summary", "")
    st.metric("Automatic Correctness Score", "N/A" if score is None else f"{float(score):.1f}/100")
    if summary:
        st.info(summary)

    details = assessment.get("details", [])
    if not details:
        st.caption("No answer comparison is available.")
        return

    answer_rows = []
    for detail in details:
        answer_rows.append(
            {
                "Q#": detail["question_number"],
                "Question": detail["question"],
                "Submitted Answer": detail["submitted_answer"],
                "Correct Answer": detail["correct_answer"],
                "Score": detail["score"],
                "Matched Keywords": ", ".join(detail["matched_keywords"]),
                "Missing Keywords": ", ".join(detail["missing_keywords"]),
            }
        )
    st.dataframe(pd.DataFrame(answer_rows), use_container_width=True, hide_index=True)

    with st.expander("Correct answer key and sources", expanded=False):
        for detail in details:
            st.markdown(f"**Question {detail['question_number']}**")
            st.write(detail["question"])
            st.success(detail["correct_answer"])
            sources = detail.get("answer_source") or []
            if sources:
                st.caption("Sources: " + " | ".join(sources))


def render_screenshots(screenshots_json: str) -> None:
    screenshots = [
        item
        for item in decode_screenshots(screenshots_json)
        if item.get("category", "screenshot") == "screenshot"
    ]
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


def render_sales_brief_upload(screenshots_json: str) -> None:
    sales_briefs = [
        item
        for item in decode_screenshots(screenshots_json)
        if item.get("category") == "sales_brief"
    ]
    if not sales_briefs:
        st.caption("No sales brief file submitted.")
        return

    for index, sales_brief in enumerate(sales_briefs):
        name = sales_brief.get("name", "sales_brief")
        mime_type = sales_brief.get("mime_type", "application/octet-stream")
        encoded = sales_brief.get("data_base64", "")
        try:
            file_bytes = base64.b64decode(encoded)
        except Exception:
            st.caption(f"{name}: could not decode file data.")
            continue

        if mime_type.startswith("image/"):
            st.image(file_bytes, caption=name, use_container_width=True)
        st.download_button(
            "Download sales brief",
            data=file_bytes,
            file_name=name,
            mime=mime_type,
            use_container_width=True,
            key=f"sales_brief_download_{index}_{len(file_bytes)}",
        )


def render_public_submission() -> None:
    st.markdown('<div class="main-title">Project Submission</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Submit your project details, video, JSON output, screenshots, and sales brief for judge review.</div>',
        unsafe_allow_html=True,
    )
    if not db_configured():
        st.warning("Databricks secrets are not configured. Submissions are only kept in this Streamlit session.")

    st.caption("Fields marked * are required.")
    participant_template_path = Path(APP_ROOT) / "participant_submission_template.json"
    if participant_template_path.exists():
        st.download_button(
            "Download answer JSON template",
            data=participant_template_path.read_bytes(),
            file_name=participant_template_path.name,
            mime="application/json",
            use_container_width=True,
        )

    with st.form("public_submission_form"):
        st.markdown("#### Team and Links")
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input(
                "Team name *",
                help="Use the exact team name shared by the organizers.",
            )
            submitter_name = st.text_input("Your name *")
            submitter_email = st.text_input("Your email *", placeholder="name@company.com")
            submission_url = st.text_input("Prototype or app URL (optional)")
        with c2:
            source_code_url = st.text_input("GitHub / source code URL (optional)")
            video_url = st.text_input(
                "Demo video URL *",
                placeholder="OneDrive, YouTube, Loom, or direct video URL",
                help="Required so judges can verify the working demo.",
            )

        st.markdown("#### Submission Artifacts")
        evidence_col, brief_col = st.columns(2)
        with evidence_col:
            screenshots = st.file_uploader(
                f"Screenshots (optional, max {format_file_size(MAX_SINGLE_SCREENSHOT_BYTES)} each)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                help=(
                    f"Upload up to {MAX_SCREENSHOTS} compressed screenshots. "
                    f"Each screenshot must be {format_file_size(MAX_SINGLE_SCREENSHOT_BYTES)} or less."
                ),
            )
        with brief_col:
            sales_brief_file = st.file_uploader(
                f"Sales brief / one-pager * (max {format_file_size(MAX_SALES_BRIEF_BYTES)})",
                type=["pdf", "doc", "docx", "png", "jpg", "jpeg", "webp"],
                accept_multiple_files=False,
                help=(
                    "Submit the generated sales brief as PDF, DOC, DOCX, or image. "
                    f"Keep it {format_file_size(MAX_SALES_BRIEF_BYTES)} or less."
                ),
            )
        current_upload_bytes = total_uploaded_file_size(screenshots, sales_brief_file)
        st.caption(
            f"File limits: each screenshot <= {format_file_size(MAX_SINGLE_SCREENSHOT_BYTES)}, "
            f"sales brief <= {format_file_size(MAX_SALES_BRIEF_BYTES)}, and all uploads together <= "
            f"{format_file_size(MAX_COMBINED_UPLOAD_BYTES)}. Databricks allows about "
            f"{DATABRICKS_PARAMETER_LIMIT_CHARS:,} characters per insert, and uploaded files expand when stored."
        )
        if current_upload_bytes:
            size_message = (
                f"Selected upload size: {format_file_size(current_upload_bytes)} / "
                f"{format_file_size(MAX_COMBINED_UPLOAD_BYTES)} app limit."
            )
            if current_upload_bytes > MAX_COMBINED_UPLOAD_BYTES:
                st.warning(size_message + " Please compress files or use links before submitting.")
            else:
                st.caption(size_message)

        description = st.text_area(
            "Short project description *",
            height=110,
            placeholder="Briefly describe what your project does and how judges should test it.",
        )

        st.markdown("#### Answer JSON")
        uploaded_json_file = st.file_uploader(
            "Upload completed answer JSON file",
            type=["json"],
            accept_multiple_files=False,
            help="Upload the completed participant_submission_template.json file, or paste the JSON below.",
        )
        submission_json = st.text_area(
            "Or paste completed answer JSON",
            height=220,
            placeholder='{\n  "answers": [\n    {\n      "question_number": 1,\n      "question": "...",\n      "answer": "..."\n    }\n  ]\n}',
            help="Paste the completed participant_submission_template.json content. Judges will see the comparison, not the full raw JSON.",
        )

        submitted = st.form_submit_button("Submit for judging", use_container_width=True)

    if not submitted:
        return

    final_submission_json = submission_json.strip()
    if uploaded_json_file is not None:
        try:
            final_submission_json = uploaded_json_file.getvalue().decode("utf-8").strip()
        except UnicodeDecodeError:
            final_submission_json = ""
            errors = ["Uploaded JSON file must be UTF-8 text."]
        else:
            errors = []
    else:
        errors = []

    if not project_name.strip():
        errors.append("Team name is required. Use the exact team name shared by the organizers.")
    if not submitter_name.strip():
        errors.append("Your name is required.")
    if not submitter_email.strip():
        errors.append("Your email is required.")
    elif not is_email(submitter_email):
        errors.append("Enter a valid email address.")
    if not video_url.strip():
        errors.append("Video URL is required.")
    elif not is_url(video_url):
        errors.append("Video URL must start with http:// or https://.")
    if submission_url.strip() and not is_url(submission_url):
        errors.append("Prototype/app URL must start with http:// or https://.")
    if source_code_url.strip() and not is_url(source_code_url):
        errors.append("GitHub/source code URL must start with http:// or https://.")
    if sales_brief_file is None:
        errors.append("Sales brief / one-pager is required.")
    if not description.strip():
        errors.append("Short project description is required.")
    if len(description) > MAX_TEXT_CHARS:
        errors.append(f"Description must be {MAX_TEXT_CHARS:,} characters or fewer.")
    if not final_submission_json:
        errors.append("Completed answer JSON is required. Upload a JSON file or paste the JSON.")
    if len(final_submission_json) > MAX_JSON_CHARS:
        errors.append(f"JSON payload must be {MAX_JSON_CHARS:,} characters or fewer.")
    if final_submission_json:
        try:
            json.loads(final_submission_json)
        except Exception:
            errors.append("The submitted JSON is not valid JSON.")

    screenshots_json = "[]"
    try:
        screenshots_json = encode_submission_files(screenshots, sales_brief_file)
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        for error in errors:
            st.error(error)
        return

    try:
        create_submission(
            {
                "project_name": project_name.strip(),
                "submitter_name": submitter_name.strip(),
                "submitter_email": submitter_email.strip(),
                "submission_url": submission_url.strip(),
                "video_url": video_url.strip(),
                "description": combine_description_with_source_link(description, source_code_url),
                "submission_json": final_submission_json,
                "screenshots_json": screenshots_json,
            }
        )
    except ValueError as exc:
        st.error(str(exc))
        return
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
    render_hackathon_scoring_guide()
    st.markdown('<div class="main-title">Judge Portal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Review PIH hackathon submissions using the five-criteria, 20-point scorecard.</div>',
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

    render_starter_warehouse_sidebar()


    if st.sidebar.button("Refresh data", use_container_width=True):
        load_submissions.clear()
        st.rerun()
    show_ai_scores = st.sidebar.toggle("Show AI scores", value=False)

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
                st.success(f"You reviewed this project. Your score: {float(review.get('total_score') or 0):.1f}/20")
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
                    st.metric(
                        "AI Score",
                        "Hidden" if not show_ai_scores else "N/A" if pd.isna(ai_value) else f"{float(ai_value):.1f}",
                    )
                with top_cols[2]:
                    st.metric("Judge Avg /20", "N/A" if pd.isna(avg_judge) else f"{float(avg_judge):.1f}")
                with top_cols[3]:
                    badge_class = "review-status-reviewed" if reviewed else "review-status-pending"
                    badge_label = "Reviewed" if reviewed else "Pending"
                    st.markdown(
                        f'<div class="review-status-badge {badge_class}">{badge_label}</div>',
                        unsafe_allow_html=True,
                    )
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

        st.markdown('<div class="section-header">Correct Answer Comparison</div>', unsafe_allow_html=True)
        render_correctness_assessment(
            selected.get("submission_json") or "",
            selected.get("correctness_summary") or "",
            selected.get("correctness_score"),
        )

        st.markdown('<div class="section-header">Sales Brief / One-Pager</div>', unsafe_allow_html=True)
        render_sales_brief_upload(selected.get("screenshots_json") or "")

        st.markdown('<div class="section-header">Screenshots</div>', unsafe_allow_html=True)
        render_screenshots(selected.get("screenshots_json") or "")

        if show_ai_scores:
            st.markdown('<div class="section-header">AI Evaluation</div>', unsafe_allow_html=True)
            ai_score = selected.get("ai_score")
            st.metric("AI Score", "N/A" if pd.isna(ai_score) else f"{float(ai_score):.1f}/100")
            st.info(selected.get("ai_summary") or "AI evaluation has not been run yet.")
        else:
            st.caption("AI score is hidden. Use the sidebar toggle to show it.")

        if st.button("Run AI evaluation for this project", use_container_width=True):
            with st.spinner("Running AI evaluation..."):
                try:
                    fallback_reason = ""
                    if selected.get("submission_url"):
                        try:
                            report = run_live_prototype_evaluation(
                                selected["submission_url"],
                                member_name=selected.get("project_name"),
                            )
                        except Exception as exc:
                            if not should_fallback_to_standard_evaluation(exc):
                                raise
                            fallback_reason = (
                                "Prototype URL does not expose the required POST evaluation endpoints. "
                                "Used the standard local benchmark instead."
                            )
                            report = run_standard_submission_evaluation(selected)
                    else:
                        report = run_standard_submission_evaluation(selected)

                    ai_summary = (
                        f"{fallback_reason} " if fallback_reason else ""
                    ) + f"AI evaluation completed with run ID {report.run_id}. Overall score: {report.overall_score:.1f}/100."
                    update_ai_result(
                        selected_id,
                        report.overall_score,
                        ai_summary,
                    )
                    if fallback_reason:
                        st.warning(fallback_reason)
                    st.success("AI evaluation saved.")
                    st.rerun()
                except Exception as exc:
                    show_optional_evaluator_error(exc)

    with score_col:
        st.markdown('<div class="section-header">Your Marks</div>', unsafe_allow_html=True)
        st.caption("PIH Hackathon scorecard: five criteria, 1-4 points each, 20 points total.")
        current_score = load_my_score(selected_id, judge_email)
        with st.form("judge_score_form"):
            score_values = {}
            for field in PIH_SCORE_FIELDS:
                score_values[field["storage_key"]] = st.slider(
                    field["display"],
                    1,
                    4,
                    coerce_pih_score(current_score[field["storage_key"]]),
                    1,
                    help=field["help"],
                )
            total_preview = pih_total_score(score_values)
            st.metric("Total score", f"{total_preview:.0f}/20")
            comments = st.text_area("Comments", value=current_score.get("comments") or "", height=140)
            if st.form_submit_button("Save marks", use_container_width=True):
                try:
                    save_judge_score(
                        selected_id,
                        judge_email,
                        {
                            **score_values,
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
                st.dataframe(format_judge_scores_for_display(scores_df), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not load judge responses: {exc}")


requested_page = str(st.query_params.get("page", "submit")).lower()

if not st.session_state.get("judge_logged_in"):
    if requested_page in {"judge", "login"}:
        st.sidebar.link_button("Open submit page", "?page=submit", use_container_width=True)
        render_login()
    else:
        hide_public_submission_sidebar()
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
        try:
            # Load sample data
            data = load_evaluation_dataset()
            ext_case = data.get("extraction_cases", [None])[0]
            ret_case = data.get("retrieval_cases", [None])[0]
            rag_case = data.get("rag_cases", [None])[0]
            hal_case = data.get("hallucination_cases", [None])[0]
            sales_case = data.get("sales_brief_cases", [None])[0]
            judge_case = data.get("judge_cases", [None])[0]

            evaluator = create_ai_evaluator()
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
        except Exception as exc:
            show_optional_evaluator_error(exc)

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
                report = run_live_prototype_evaluation(live_url, member_name=member_name)
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
                try:
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

                    evaluator = create_ai_evaluator()
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
                except Exception as exc:
                    show_optional_evaluator_error(exc)

