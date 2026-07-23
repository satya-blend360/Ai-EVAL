import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from ai_eval.core.evaluator import AIEvaluator
from ai_eval.data.loader import load_evaluation_data
from ai_eval.config import REPORTS_DIR
from ai_eval.utils.logger import logger

def main():
    logger.info("Initializing Evaluation CLI Run...")
    
    # 1. Load sample data
    data = load_evaluation_data()
    
    # Extract the first case for each type
    ext_case = data.get("extraction_cases", [None])[0]
    ret_case = data.get("retrieval_cases", [None])[0]
    rag_case = data.get("rag_cases", [None])[0]
    hal_case = data.get("hallucination_cases", [None])[0]
    sales_case = data.get("sales_brief_cases", [None])[0]
    judge_case = data.get("judge_cases", [None])[0]
    
    # 2. Instantiate Evaluator
    evaluator = AIEvaluator()
    
    # 3. Run Pipeline
    logger.info("Running evaluation pipeline on sample cases...")
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
    
    # 4. Save report
    output_path = REPORTS_DIR / f"report_{report.run_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    logger.info(f"Evaluation report successfully saved to: {output_path}")
    
    # Also save as sample_report.json for default loading
    sample_path = REPORTS_DIR / "sample_report.json"
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    
    # 5. Output beautiful console summaries
    print("\n" + "="*60)
    print(f"       AI EVALUATION PIPELINE REPORT ({report.run_id})")
    print("="*60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Overall Normalized Score: {report.overall_score:.2f} / 100.0")
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
    if report.performance:
        # Calculate cost & latency scores
        cost_score = 100.0
        cost = report.performance.cost_usd
        from ai_eval.config import COST_TARGET_USD, COST_MAX_USD, LATENCY_TARGET_MS, LATENCY_MAX_MS
        if cost > COST_TARGET_USD:
            cost_score = max(0.0, 100.0 * (COST_MAX_USD - cost) / (COST_MAX_USD - COST_TARGET_USD))
            
        lat_score = 100.0
        lat = report.performance.latency_ms
        if lat > LATENCY_TARGET_MS:
            lat_score = max(0.0, 100.0 * (LATENCY_MAX_MS - lat) / (LATENCY_MAX_MS - LATENCY_TARGET_MS))
            
        if "cost_efficiency" in weights:
            print(f" - Cost Efficiency:         {cost_score:.1f}% (Weight: {weights.get('cost_efficiency', 0)*100:.1f}%)")
        if "response_time" in weights:
            print(f" - Response Time:           {lat_score:.1f}% (Weight: {weights.get('response_time', 0)*100:.1f}%)")
        
    print("-"*60)
    print("PERFORMANCE METRICS:")
    if report.performance:
        print(f" - Latency:       {report.performance.latency_ms:.2f} ms")
        print(f" - Token Count:   {report.performance.total_tokens} tokens")
        print(f" - API Cost:      ${report.performance.cost_usd:.6f}")
        print(f" - Throughput:    {report.performance.throughput_tokens_per_sec:.2f} tokens/sec")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
