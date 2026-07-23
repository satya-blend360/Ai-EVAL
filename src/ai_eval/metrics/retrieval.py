import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ai_eval.utils.llm import LLMProvider
from ai_eval.models import RetrievalMetrics
from ai_eval.utils.logger import logger

class RetrievalEvaluator:
    """Evaluates search and retrieval quality against expected project targets."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or LLMProvider()

    def evaluate(
        self,
        query: str,
        expected_projects: List[str],
        retrieved_projects: List[str],
        k: int = 5,
        project_details: Optional[Dict[str, str]] = None
    ) -> RetrievalMetrics:
        """
        Evaluates retrieval performance.
        
        Args:
            query: User's search query
            expected_projects: List of project identifiers (e.g., IDs, names) expected to be retrieved
            retrieved_projects: Ordered list of project identifiers returned by retrieval system
            k: Evaluation cutoff rank
            project_details: Optional dictionary mapping project identifiers to descriptions/summaries 
                             to assist in LLM relevance scoring
        """
        logger.info(f"Starting Retrieval Evaluation for query: '{query}'...")
        
        if not expected_projects:
            logger.warning("No expected projects provided. Returning default scores.")
            return RetrievalMetrics(precision_at_k=0.0, recall_at_k=0.0, mrr=0.0, ndcg=0.0, relevance_score=0.0)

        # Normalize lists for case-insensitive/robust comparison
        norm_expected = [str(p).strip().lower() for p in expected_projects]
        norm_retrieved = [str(p).strip().lower() for p in retrieved_projects]
        
        # 1. Precision@K
        retrieved_k = norm_retrieved[:k]
        relevant_retrieved_k = [p for p in retrieved_k if p in norm_expected]
        precision_val = len(relevant_retrieved_k) / k
        
        # 2. Recall@K (Recall at cutoff k)
        relevant_retrieved_all = [p for p in norm_retrieved if p in norm_expected]
        # Recall is based on total expected projects
        recall_val = len(relevant_retrieved_all) / len(norm_expected)
        
        # 3. Mean Reciprocal Rank (MRR)
        # Find first relevant item's rank
        mrr_val = 0.0
        for idx, item in enumerate(norm_retrieved):
            if item in norm_expected:
                mrr_val = 1.0 / (idx + 1)
                break
                
        # 4. Normalized Discounted Cumulative Gain (NDCG)
        # Calculate DCG@k
        dcg = 0.0
        for idx, item in enumerate(retrieved_k):
            rel = 1 if item in norm_expected else 0
            dcg += rel / math.log2(idx + 2)
            
        # Calculate Ideal DCG@k (IDCG)
        idcg = 0.0
        # The best possible ranking puts all expected items first
        for idx in range(min(len(expected_projects), k)):
            idcg += 1.0 / math.log2(idx + 2)
            
        ndcg_val = (dcg / idcg) if idcg > 0 else 0.0
        
        # 5. Semantic Relevance Score
        relevance_val = self._evaluate_semantic_relevance(query, retrieved_projects, project_details)
        
        return RetrievalMetrics(
            precision_at_k=round(precision_val, 4),
            recall_at_k=round(recall_val, 4),
            mrr=round(mrr_val, 4),
            ndcg=round(ndcg_val, 4),
            relevance_score=round(relevance_val, 4)
        )
        
    def _evaluate_semantic_relevance(
        self,
        query: str,
        retrieved: List[str],
        project_details: Optional[Dict[str, str]]
    ) -> float:
        """Uses an LLM to assess semantic relevance of retrieved list to the search intent."""
        if not retrieved:
            return 0.0
            
        # If no project details are provided, return the fraction of matches as relevance base
        if not project_details:
            # Simple heuristic: NDCG or MRR
            return 0.0
            
        # Compile document snippets
        retrieved_info = []
        for idx, pid in enumerate(retrieved[:5]):  # limit to top 5
            desc = project_details.get(pid, "No description available.")
            retrieved_info.append(f"Rank {idx+1}. Project [{pid}]: {desc}")
            
        docs_text = "\n\n".join(retrieved_info)
        
        class RelevanceGrade(BaseModel):
            relevance_score: float  # Scale 0.0 - 1.0
            reasoning: str

        system_prompt = (
            "You are a Search Relevance Evaluator.\n"
            "Your job is to read a user query and a list of search results, and evaluate the "
            "overall relevance quality of the top retrieved projects.\n"
            "Provide a relevance score between 0.0 (totally irrelevant) and 1.0 (perfectly relevant)."
        )
        
        user_prompt = (
            f"User Search Query: '{query}'\n\n"
            f"Top Retrieved Projects:\n{docs_text}\n\n"
            "Evaluate how relevant these projects are to the search query. "
            "Note that even if they are not exact matches, they should be topically and semantically related."
        )
        
        try:
            result, _ = self.llm_provider.call_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=RelevanceGrade
            )
            return result.relevance_score
        except Exception as e:
            logger.error(f"Semantic relevance evaluator failed: {e}")
            # fallback: return the precision@5
            return 0.0
