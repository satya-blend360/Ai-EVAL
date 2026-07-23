from ai_eval.core.evaluator import AIEvaluator
from ai_eval.models import PerformanceMetrics

def test_evaluator_weights_redistribution():
    evaluator = AIEvaluator()
    
    # Define custom test weights
    custom_weights = {
        "extraction_accuracy": 0.20,
        "retrieval_quality": 0.30,
        "sales_brief_quality": 0.50
    }
    
    # Mock performance (cost & latency)
    perf = PerformanceMetrics(
        latency_ms=100.0,
        cost_usd=0.0001,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        throughput_tokens_per_sec=150.0
    )
    
    # Case 1: All components present
    # We will pass score values to _calculate_overall_score to see if they math out
    # Mock models
    from ai_eval.models import ExtractionMetrics, RetrievalMetrics, SalesBriefMetrics
    
    ext = ExtractionMetrics(accuracy=90.0, completeness=100.0, confidence_score=95.0, citation_coverage=100.0, missing_field_detection=100.0)
    ret = RetrievalMetrics(precision_at_k=1.0, recall_at_k=1.0, mrr=1.0, ndcg=1.0, relevance_score=1.0) # 100% search quality
    sb = SalesBriefMetrics(readability=8.0, professionalism=8.0, evidence_usage=8.0, completeness=8.0, persuasiveness=8.0, business_value=8.0, overall=8.0, feedback="good")
    
    score, weights_used = evaluator._calculate_overall_score(
        extraction=ext,
        retrieval=ret,
        rag=None,
        hallucination=None,
        sales_brief=sb,
        perf=perf,
        weights=custom_weights
    )
    
    # Expected:
    # component_scores:
    # extraction_accuracy: 90
    # retrieval_quality: 100
    # sales_brief_quality: 80
    #
    # Active weights:
    # extraction_accuracy: 0.2
    # retrieval_quality: 0.3
    # sales_brief_quality: 0.5
    # Total active: 1.0.
    # Normalized weights are: 0.2, 0.3, 0.5.
    # Overall score = 90 * 0.2 + 100 * 0.3 + 80 * 0.5 = 18 + 30 + 40 = 88.0
    assert score == 88.0
    assert weights_used["extraction_accuracy"] == 0.20
    assert weights_used["retrieval_quality"] == 0.30
    assert weights_used["sales_brief_quality"] == 0.50

def test_evaluator_weights_redistribution_missing_component():
    evaluator = AIEvaluator()
    
    custom_weights = {
        "extraction_accuracy": 0.20,
        "retrieval_quality": 0.30,
        "sales_brief_quality": 0.50
    }
    
    perf = PerformanceMetrics(
        latency_ms=100.0,
        cost_usd=0.0001,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        throughput_tokens_per_sec=150.0
    )
    
    # Case 2: Sales Brief component is missing
    from ai_eval.models import ExtractionMetrics, RetrievalMetrics
    ext = ExtractionMetrics(accuracy=90.0, completeness=100.0, confidence_score=95.0, citation_coverage=100.0, missing_field_detection=100.0)
    ret = RetrievalMetrics(precision_at_k=1.0, recall_at_k=1.0, mrr=1.0, ndcg=1.0, relevance_score=1.0)
    
    score, weights_used = evaluator._calculate_overall_score(
        extraction=ext,
        retrieval=ret,
        rag=None,
        hallucination=None,
        sales_brief=None,
        perf=perf,
        weights=custom_weights
    )
    
    # Active weights:
    # extraction_accuracy: 0.20
    # retrieval_quality: 0.30
    # Total active weight = 0.50.
    # Normalized weights:
    # extraction_accuracy: 0.20 / 0.50 = 0.40
    # retrieval_quality: 0.30 / 0.50 = 0.60
    #
    # Overall score = 90 * 0.40 + 100 * 0.60 = 36 + 60 = 96.0
    assert score == 96.0
    assert weights_used["extraction_accuracy"] == 0.40
    assert weights_used["retrieval_quality"] == 0.60
    assert "sales_brief_quality" not in weights_used
