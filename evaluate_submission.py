import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Adjust path to import ai_eval package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from ai_eval.core.evaluator import AIEvaluator
from ai_eval.data.loader import load_evaluation_data
from ai_eval.config import REPORTS_DIR
from ai_eval.utils.logger import logger

def make_post_request(url, data_dict):
    """Sends a POST request to the user API and measures network response time."""
    data_bytes = json.dumps(data_dict).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    start_time = time.time()
    try:
        # 30 second timeout for evaluation endpoints
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode('utf-8')
            res_dict = json.loads(res_body)
            # Use backend-reported latency if available, otherwise fallback to network duration
            latency_ms = res_dict.get("performance_metadata", {}).get("latency_ms")
            if latency_ms is None:
                latency_ms = (time.time() - start_time) * 1000
            return res_dict, latency_ms, None
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return None, latency_ms, str(e)

def estimate_cost(model_name, prompt_tokens, completion_tokens):
    """Estimates LLM cost based on standard pricing models."""
    if not model_name:
        return 0.0
    model_name = model_name.lower()
    rates = {
        "gpt-4o": (5.00 / 1_000_000, 15.00 / 1_000_000),
        "gpt-4o-mini": (0.150 / 1_000_000, 0.600 / 1_000_000),
        "gpt-4-turbo": (10.00 / 1_000_000, 30.00 / 1_000_000),
        "claude-3-5-sonnet": (3.00 / 1_000_000, 15.00 / 1_000_000),
        "claude-3-opus": (15.00 / 1_000_000, 75.00 / 1_000_000),
        "claude-3-haiku": (0.25 / 1_000_000, 1.25 / 1_000_000),
    }
    for key, (in_rate, out_rate) in rates.items():
        if key in model_name:
            return (prompt_tokens * in_rate) + (completion_tokens * out_rate)
    # Default to gpt-4o-mini rates
    return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)

def run_live_evaluation(base_url: str, member_name: str = None):
    """Hits the 4 user API endpoints, grades them locally, and outputs the final report."""
    base_url = base_url.rstrip('/')
    logger.info(f"Starting Live Submission Evaluation against base URL: {base_url}")
    
    # 1. Load standard test case inputs
    data = load_evaluation_data()
    ext_case = data.get("extraction_cases", [None])[0]
    ret_case = data.get("retrieval_cases", [None])[0]
    rag_case = data.get("rag_cases", [None])[0]
    sales_case = data.get("sales_brief_cases", [None])[0]
    
    if not (ext_case and ret_case and rag_case and sales_case):
        raise ValueError("Standard test dataset is missing cases. Make sure test_data.json is populated.")
        
    user_perf = {
        "latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0
    }
    
    def record_perf(res_dict, net_lat):
        meta = res_dict.get("performance_metadata", {})
        user_perf["latency_ms"] += meta.get("latency_ms", net_lat)
        p_tok = meta.get("prompt_tokens", 0)
        c_tok = meta.get("completion_tokens", 0)
        user_perf["prompt_tokens"] += p_tok
        user_perf["completion_tokens"] += c_tok
        user_perf["total_tokens"] += meta.get("total_tokens", p_tok + c_tok)
        user_perf["cost_usd"] += estimate_cost(meta.get("model_used"), p_tok, c_tok)

    # API 1: Intake
    intake_url = f"{base_url}/api/eval/intake"
    logger.info(f"Querying Intake Endpoint: {intake_url}...")
    intake_res, net_lat, err = make_post_request(intake_url, {"source_text": ext_case["source_text"]})
    if err:
        raise ValueError(f"Intake API failed: {err}")
    record_perf(intake_res, net_lat)
    
    # API 2: Search
    search_url = f"{base_url}/api/eval/search"
    logger.info(f"Querying Search Endpoint: {search_url}...")
    search_res, net_lat, err = make_post_request(search_url, {"query": ret_case["query"], "k": ret_case.get("k", 5)})
    if err:
        raise ValueError(f"Search API failed: {err}")
    record_perf(search_res, net_lat)
    
    # API 3: Q&A
    qa_url = f"{base_url}/api/eval/qa"
    logger.info(f"Querying QA Endpoint: {qa_url}...")
    qa_res, net_lat, err = make_post_request(qa_url, {"project_id": "proj_apex_001", "question": rag_case["query"]})
    if err:
        raise ValueError(f"QA API failed: {err}")
    record_perf(qa_res, net_lat)
    
    # API 4: Sales Brief
    sales_url = f"{base_url}/api/eval/sales_brief"
    logger.info(f"Querying Sales Brief Endpoint: {sales_url}...")
    sales_res, net_lat, err = make_post_request(sales_url, {
        "project_context": sales_case["project_context"],
        "business_requirements": sales_case.get("business_requirements", "")
    })
    if err:
        raise ValueError(f"Sales Brief API failed: {err}")
    record_perf(sales_res, net_lat)
    
    # 3. Format inputs for our Local Semantic Evaluator
    evaluator = AIEvaluator()
    
    eval_extraction_data = {
        "extracted_fields": intake_res.get("extracted_fields", {}),
        "expected_fields": ext_case["expected_fields"],
        "source_text": ext_case.get("source_text"),
        "field_citations": intake_res.get("field_citations"),
        "confidence_scores": intake_res.get("confidence_scores")
    }
    
    eval_retrieval_data = {
        "query": ret_case["query"],
        "expected_projects": ret_case["expected_projects"],
        "retrieved_projects": search_res.get("retrieved_projects", []),
        "project_details": ret_case.get("project_details")
    }
    
    eval_rag_data = {
        "query": rag_case["query"],
        "contexts": qa_res.get("retrieved_context_snippets", []),
        "generated_answer": qa_res.get("generated_answer", ""),
        "ground_truth_answer": rag_case.get("ground_truth_answer")
    }
    
    eval_sales_data = {
        "sales_brief": sales_res.get("sales_brief_text", ""),
        "project_context": sales_case["project_context"],
        "business_requirements": sales_case.get("business_requirements")
    }
    
    report = evaluator.run_evaluation(
        extraction_data=eval_extraction_data,
        retrieval_data=eval_retrieval_data,
        rag_data=eval_rag_data,
        sales_brief_data=eval_sales_data
    )
    
    # Overwrite performance scores with User's prototype actual metrics
    report.performance.latency_ms = round(user_perf["latency_ms"], 2)
    report.performance.prompt_tokens = user_perf["prompt_tokens"]
    report.performance.completion_tokens = user_perf["completion_tokens"]
    report.performance.total_tokens = user_perf["total_tokens"]
    report.performance.cost_usd = round(user_perf["cost_usd"], 6)
    
    # Recalculate dynamic rubric score using the overwritten performance statistics
    score, weights_used = evaluator._calculate_overall_score(
        extraction=report.extraction,
        retrieval=report.retrieval,
        rag=report.rag,
        hallucination=report.hallucination,
        sales_brief=report.sales_brief,
        perf=report.performance,
        weights=evaluator.weights
    )
    report.overall_score = round(score, 2)
    report.weights_used = weights_used
    
    # If member_name is provided, sanitize and set as run_id to overwrite/create exactly one JSON per member
    if member_name:
        import re
        sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '', member_name)
        if sanitized_name:
            report.run_id = sanitized_name
            
    # Save the live evaluation report
    output_path = REPORTS_DIR / f"report_{report.run_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    logger.info(f"Submission evaluation report successfully saved to: {output_path}")
    
    # Also save as sample_report.json so dashboard loads it by default
    sample_path = REPORTS_DIR / "sample_report.json"
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
        
    return report

def main():
    parser = argparse.ArgumentParser(description="Evaluate a live Project Intelligence Hub submission.")
    parser.add_argument("--base_url", required=True, help="Base URL of the user's running prototype API (e.g. http://localhost:8000)")
    parser.add_argument("--member_name", required=False, help="Name/ID of the team member")
    args = parser.parse_args()
    
    base_url = args.base_url
    member_name = args.member_name
    
    try:
        report = run_live_evaluation(base_url, member_name=member_name)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)
        
    # Output report summary to console
    print("\n" + "="*60)
    print(f"       SUBMISSION EVALUATION REPORT ({report.run_id})")
    print("="*60)
    print(f"Timestamp: {report.timestamp}")
    print(f"User Base URL: {base_url}")
    print(f"Overall Rubric Score: {report.overall_score:.2f} / 100.0")
    print("-"*60)
    print("WEIGHTED COMPONENT SCORES:")
    
    weights = report.weights_used
    if report.extraction:
        if "extraction_accuracy" in weights:
            print(f" - Extraction Accuracy:     {report.extraction.accuracy:.1f}% (Weight: {weights.get('extraction_accuracy', 0)*100:.1f}%)")
        if "completeness" in weights:
            print(f" - Completeness:            {report.extraction.completeness:.1f}% (Weight: {weights.get('completeness', 0)*100:.1f}%)")
    if report.retrieval:
        if "retrieval_quality" in weights:
            ret_q = (report.retrieval.precision_at_k + report.retrieval.recall_at_k + report.retrieval.mrr + report.retrieval.ndcg) / 4.0 * 100
            print(f" - Retrieval Quality:       {ret_q:.1f}% (Weight: {weights.get('retrieval_quality', 0)*100:.1f}%)")
    if report.hallucination:
        if "hallucination_risk" in weights:
            hal_score = 100.0 - report.hallucination.hallucination_rate
            print(f" - Hallucination Risk:      {hal_score:.1f}% (Weight: {weights.get('hallucination_risk', 0)*100:.1f}%)")
    if report.sales_brief:
        if "sales_brief_quality" in weights:
            print(f" - Sales Brief Quality:     {report.sales_brief.overall*10.0:.1f}% (Weight: {weights.get('sales_brief_quality', 0)*100:.1f}%)")
            
    # Re-fetch normalized Cost & Latency values
    from ai_eval.config import COST_TARGET_USD, COST_MAX_USD, LATENCY_TARGET_MS, LATENCY_MAX_MS
    cost = report.performance.cost_usd
    cost_score = 100.0
    if cost > COST_TARGET_USD:
        cost_score = max(0.0, 100.0 * (COST_MAX_USD - cost) / (COST_MAX_USD - COST_TARGET_USD))
        
    lat = report.performance.latency_ms
    lat_score = 100.0
    if lat > LATENCY_TARGET_MS:
        lat_score = max(0.0, 100.0 * (LATENCY_MAX_MS - lat) / (LATENCY_MAX_MS - LATENCY_TARGET_MS))
        
    if "cost_efficiency" in weights:
        print(f" - Cost Efficiency:         {cost_score:.1f}% (Weight: {weights.get('cost_efficiency', 0)*100:.1f}%)")
    if "response_time" in weights:
        print(f" - Response Time:           {lat_score:.1f}% (Weight: {weights.get('response_time', 0)*100:.1f}%)")
        
    print("-"*60)
    print("PROTOTYPE PERFORMANCE STATISTICS:")
    print(f" - Combined Latency: {report.performance.latency_ms:.2f} ms")
    print(f" - LLM Token Count:  {report.performance.total_tokens} tokens")
    print(f" - Est. LLM Pricing: ${report.performance.cost_usd:.6f}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
