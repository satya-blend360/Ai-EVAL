from ai_eval.metrics.retrieval import RetrievalEvaluator

def test_retrieval_perfect_score():
    evaluator = RetrievalEvaluator()
    query = "test query"
    expected = ["Project A", "Project B"]
    retrieved = ["Project A", "Project B", "Project C"]
    
    metrics = evaluator.evaluate(query, expected, retrieved, k=5)
    
    # K=5, so precision@5 is 2/5 = 0.4
    assert metrics.precision_at_k == 0.4
    # All expected were retrieved, so recall is 2/2 = 1.0
    assert metrics.recall_at_k == 1.0
    # First relevant item is at rank 1, so MRR is 1.0
    assert metrics.mrr == 1.0
    # Perfect NDCG because all expected were at the top
    assert metrics.ndcg == 1.0

def test_retrieval_imperfect_score():
    evaluator = RetrievalEvaluator()
    query = "test query"
    expected = ["A", "B", "C"]
    retrieved = ["A", "D", "B", "E", "C"]
    
    metrics = evaluator.evaluate(query, expected, retrieved, k=5)
    
    # 3 relevant out of 5 retrieved -> precision = 3/5 = 0.6
    assert metrics.precision_at_k == 0.6
    # 3 relevant out of 3 expected -> recall = 3/3 = 1.0
    assert metrics.recall_at_k == 1.0
    # First relevant at rank 1 -> MRR = 1.0
    assert metrics.mrr == 1.0
    
    # NDCG math:
    # DCG = 1/log2(2) + 0/log2(3) + 1/log2(4) + 0/log2(5) + 1/log2(6) = 1.0 + 0 + 0.5 + 0 + 0.38685 = 1.88685
    # IDCG = 1/log2(2) + 1/log2(3) + 1/log2(4) = 1.0 + 0.63093 + 0.5 = 2.13093
    # NDCG = 1.88685 / 2.13093 = 0.8854
    assert round(metrics.ndcg, 4) == 0.8855  # round to 4 decimals

def test_retrieval_no_match():
    evaluator = RetrievalEvaluator()
    query = "test query"
    expected = ["A", "B"]
    retrieved = ["C", "D", "E"]
    
    metrics = evaluator.evaluate(query, expected, retrieved, k=5)
    
    assert metrics.precision_at_k == 0.0
    assert metrics.recall_at_k == 0.0
    assert metrics.mrr == 0.0
    assert metrics.ndcg == 0.0
