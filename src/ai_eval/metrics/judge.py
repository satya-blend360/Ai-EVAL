from typing import Optional, Dict, Any
from ai_eval.utils.llm import LLMProvider
from ai_eval.models import JudgeMetrics
from ai_eval.utils.logger import logger

class JudgeEvaluator:
    """General-purpose LLM-as-a-Judge agent evaluating outputs on a 1-10 scale."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or LLMProvider()

    def evaluate(
        self,
        input_context: str,
        output_generated: str,
        reference_ground_truth: Optional[str] = None,
        evaluation_criteria: Optional[str] = None
    ) -> JudgeMetrics:
        """
        Runs the LLM-as-a-Judge evaluator.
        
        Args:
            input_context: The prompt or task given to the AI model
            output_generated: The response produced by the AI model
            reference_ground_truth: Optional correct reference answer
            evaluation_criteria: Optional custom guidelines for evaluation
        """
        logger.info("Starting LLM-as-a-Judge evaluation...")
        
        if not output_generated:
            logger.warning("Empty output generated. Returning minimum scores.")
            return JudgeMetrics(
                accuracy=1.0,
                completeness=1.0,
                relevance=1.0,
                groundedness=1.0,
                usefulness=1.0,
                overall=1.0,
                reasoning="Empty output generated."
            )

        system_prompt = (
            "You are an expert LLM Evaluation Judge.\n"
            "Your task is to critically analyze an AI model's output and score it from 1.0 to 10.0 on five core areas:\n"
            "1. Accuracy: Factual correctness compared to the reference and context. No false details.\n"
            "2. Completeness: Answers all aspects of the input query. No missing elements.\n"
            "3. Relevance: Addresses the user request directly without going off-topic.\n"
            "4. Groundedness: The output is rooted strictly in reference data, avoiding hallucinations.\n"
            "5. Usefulness: Clear, structured, actionable, and helpful for the user.\n\n"
            "Be objective. Give high scores only for exceptional responses."
        )

        user_prompt = (
            f"User Prompt/Input Context:\n{input_context}\n\n"
            f"Reference Ground Truth:\n{reference_ground_truth or 'Not Provided'}\n\n"
            f"Custom Evaluation Criteria:\n{evaluation_criteria or 'Not Provided'}\n\n"
            f"AI Model Output to Evaluate:\n{output_generated}\n\n"
            "Perform evaluation and output the metrics."
        )

        try:
            result, _ = self.llm_provider.call_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=JudgeMetrics
            )
            
            # Ensure overall is calculated average
            scores = [
                result.accuracy,
                result.completeness,
                result.relevance,
                result.groundedness,
                result.usefulness
            ]
            overall_avg = sum(scores) / len(scores)
            
            return JudgeMetrics(
                accuracy=result.accuracy,
                completeness=result.completeness,
                relevance=result.relevance,
                groundedness=result.groundedness,
                usefulness=result.usefulness,
                overall=round(overall_avg, 2),
                reasoning=result.reasoning
            )
            
        except Exception as e:
            logger.error(f"LLM-as-a-Judge evaluation failed: {e}")
            return JudgeMetrics(
                accuracy=5.0,
                completeness=5.0,
                relevance=5.0,
                groundedness=5.0,
                usefulness=5.0,
                overall=5.0,
                reasoning=f"LLM-as-a-Judge error: {e}"
            )
