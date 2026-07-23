import pytest
from ai_eval.utils.llm import LLMProvider
from ai_eval.metrics.rag import RAGEvaluator
from ai_eval.metrics.hallucination import HallucinationEvaluator
from ai_eval.metrics.sales_brief import SalesBriefEvaluator
from ai_eval.metrics.judge import JudgeEvaluator

@pytest.fixture
def mock_llm():
    # Force mock mode
    return LLMProvider(provider="mock")

def test_rag_mock_evaluation(mock_llm):
    evaluator = RAGEvaluator(mock_llm)
    metrics = evaluator.evaluate(
        query="What is Project Apex?",
        contexts=["Project Apex migrated database systems to AWS Aurora."],
        generated_answer="Project Apex migrated databases to AWS Aurora.",
        ground_truth_answer="Project Apex is a database migration project to AWS Aurora."
    )
    
    assert 0.0 <= metrics.faithfulness <= 1.0
    assert 0.0 <= metrics.answer_relevancy <= 1.0
    assert 0.0 <= metrics.groundedness <= 1.0
    assert 0.0 <= metrics.context_precision <= 1.0
    assert 0.0 <= metrics.context_recall <= 1.0

def test_hallucination_mock_evaluation(mock_llm):
    evaluator = HallucinationEvaluator(mock_llm)
    metrics = evaluator.evaluate(
        generated_answer="Project Horizon was completed in 2024 for $5M ARR.",
        evidence_texts=["Project Horizon was executed for Globex in 2024 with a budget of $500,000."]
    )
    
    assert metrics.total_claims > 0
    assert 0.0 <= metrics.hallucination_rate <= 100.0
    assert len(metrics.claims) == metrics.total_claims

def test_sales_brief_mock_evaluation(mock_llm):
    evaluator = SalesBriefEvaluator(mock_llm)
    metrics = evaluator.evaluate(
        sales_brief="Sales brief text...",
        project_context={"Project Name": "Apex", "Client": "Acme", "Revenue/Billing": "$250k"}
    )
    
    assert 1.0 <= metrics.readability <= 10.0
    assert 1.0 <= metrics.professionalism <= 10.0
    assert 1.0 <= metrics.overall <= 10.0
    assert metrics.feedback is not None

def test_judge_mock_evaluation(mock_llm):
    evaluator = JudgeEvaluator(mock_llm)
    metrics = evaluator.evaluate(
        input_context="Describe Project Apex tech stack.",
        output_generated="Python, AWS Aurora, AWS Glue",
        reference_ground_truth="Python, AWS Aurora, AWS Glue, AWS DMS"
    )
    
    assert 1.0 <= metrics.accuracy <= 10.0
    assert 1.0 <= metrics.overall <= 10.0
    assert len(metrics.reasoning) > 0
