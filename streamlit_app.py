import os
import json
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

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
