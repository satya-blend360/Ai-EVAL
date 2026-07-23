from pydantic import BaseModel, Field, conint, confloat
from typing import List, Dict, Any, Optional

# --- Information Extraction Models ---

class ExtractionFieldResult(BaseModel):
    field_name: str
    expected_value: Any
    extracted_value: Any
    is_correct: bool
    is_missing: bool
    citation_provided: bool
    citation_valid: bool
    comments: Optional[str] = None

class ExtractionMetrics(BaseModel):
    accuracy: float = Field(..., description="Field accuracy percentage (0-100)")
    completeness: float = Field(..., description="Field completeness percentage (0-100)")
    confidence_score: float = Field(..., description="Average confidence score of extraction (0-100)")
    citation_coverage: float = Field(..., description="Percentage of fields with valid citations (0-100)")
    missing_field_detection: float = Field(..., description="F1 or accuracy of detecting missing fields (0-100)")
    field_details: Dict[str, ExtractionFieldResult] = Field(default_factory=dict)

# --- Retrieval Models ---

class RetrievalMetrics(BaseModel):
    precision_at_k: float = Field(..., description="Precision at K (usually K=5) (0.0-1.0)")
    recall_at_k: float = Field(..., description="Recall at K (0.0-1.0)")
    mrr: float = Field(..., description="Mean Reciprocal Rank (0.0-1.0)")
    ndcg: float = Field(..., description="Normalized Discounted Cumulative Gain (0.0-1.0)")
    relevance_score: float = Field(..., description="Semantic relevance score (0.0-1.0)")

# --- RAG Models ---

class RAGMetrics(BaseModel):
    context_precision: float = Field(..., description="Relevancy of retrieved context to query (0.0-1.0)")
    context_recall: float = Field(..., description="Completeness of retrieved context for the answer (0.0-1.0)")
    faithfulness: float = Field(..., description="Factual consistency of answer with context (0.0-1.0)")
    answer_relevancy: float = Field(..., description="How relevant the answer is to the query (0.0-1.0)")
    groundedness: float = Field(..., description="Groundedness of answer in the retrieved context (0.0-1.0)")

# --- Hallucination Models ---

class ClaimDetail(BaseModel):
    claim: str
    is_supported: bool
    evidence: Optional[str] = None
    reasoning: Optional[str] = None

class HallucinationMetrics(BaseModel):
    supported_claims: int = Field(..., description="Number of claims supported by evidence")
    total_claims: int = Field(..., description="Total claims extracted from generated text")
    hallucination_rate: float = Field(..., description="Percentage of claims unsupported (0-100)")
    claims: List[ClaimDetail] = Field(default_factory=list)

# --- Sales Brief Models ---

class SalesBriefMetrics(BaseModel):
    readability: float = Field(..., description="Readability score (1.0-10.0)")
    professionalism: float = Field(..., description="Professional tone and formatting (1.0-10.0)")
    evidence_usage: float = Field(..., description="Usage of project facts and numbers (1.0-10.0)")
    completeness: float = Field(..., description="Coverage of required sales details (1.0-10.0)")
    persuasiveness: float = Field(..., description="Sales pitch quality and conviction (1.0-10.0)")
    business_value: float = Field(..., description="Demonstration of client ROI / value (1.0-10.0)")
    overall: float = Field(..., description="Overall score normalized out of 10.0")
    feedback: Optional[str] = Field(None, description="Qualitative feedback for improvement")

# --- LLM-as-a-Judge Models ---

class JudgeMetrics(BaseModel):
    accuracy: float = Field(..., description="Evaluator score for accuracy (1.0-10.0)")
    completeness: float = Field(..., description="Evaluator score for completeness (1.0-10.0)")
    relevance: float = Field(..., description="Evaluator score for relevance (1.0-10.0)")
    groundedness: float = Field(..., description="Evaluator score for groundedness (1.0-10.0)")
    usefulness: float = Field(..., description="Evaluator score for usefulness (1.0-10.0)")
    overall: float = Field(..., description="Overall evaluator score normalized out of 10.0")
    reasoning: str = Field(..., description="Qualitative reasoning text explaining the scores")

# --- Performance Models ---

class PerformanceMetrics(BaseModel):
    latency_ms: float = Field(..., description="Latency of request in milliseconds")
    cost_usd: float = Field(..., description="Estimated cost of API calls in USD")
    prompt_tokens: int = Field(..., description="Number of prompt/input tokens used")
    completion_tokens: int = Field(..., description="Number of completion/output tokens used")
    total_tokens: int = Field(..., description="Total tokens used")
    throughput_tokens_per_sec: float = Field(..., description="Token throughput (total tokens / latency in seconds)")

# --- Combined Evaluation Output ---

class EvaluationReport(BaseModel):
    run_id: str
    timestamp: str
    extraction: Optional[ExtractionMetrics] = None
    retrieval: Optional[RetrievalMetrics] = None
    rag: Optional[RAGMetrics] = None
    hallucination: Optional[HallucinationMetrics] = None
    sales_brief: Optional[SalesBriefMetrics] = None
    judge: Optional[JudgeMetrics] = None
    performance: Optional[PerformanceMetrics] = None
    overall_score: float = Field(..., description="Final overall rubric score normalized to 100")
    weights_used: Dict[str, float] = Field(default_factory=dict)
