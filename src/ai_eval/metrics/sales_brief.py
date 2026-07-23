from typing import Optional, Dict, Any
from ai_eval.utils.llm import LLMProvider
from ai_eval.models import SalesBriefMetrics
from ai_eval.utils.logger import logger

class SalesBriefEvaluator:
    """Evaluates generated sales briefs against a multi-dimensional rubric (1-10)."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or LLMProvider()

    def evaluate(
        self,
        sales_brief: str,
        project_context: Dict[str, Any],
        business_requirements: Optional[str] = None
    ) -> SalesBriefMetrics:
        """
        Grades a sales brief.
        
        Args:
            sales_brief: The text of the generated sales brief
            project_context: The raw project data/facts that the brief is based on
            business_requirements: Special rules/guidelines the brief was supposed to follow
        """
        logger.info("Starting Sales Brief Rubric Evaluation...")
        
        if not sales_brief:
            logger.warning("Empty sales brief provided. Returning minimum scores.")
            return SalesBriefMetrics(
                readability=1.0,
                professionalism=1.0,
                evidence_usage=1.0,
                completeness=1.0,
                persuasiveness=1.0,
                business_value=1.0,
                overall=1.0,
                feedback="Empty brief."
            )

        project_facts = "\n".join([f"- {k}: {v}" for k, v in project_context.items()])

        system_prompt = (
            "You are an expert Sales Quality Auditor.\n"
            "Your task is to grade a generated sales brief using a strict 1 to 10 scale for six dimensions:\n"
            "1. Readability: Visual structure, paragraph flow, clear headings, formatting, and ease of reading.\n"
            "2. Professionalism: Correct business tone, sales etiquettes, professional language, no typos.\n"
            "3. Evidence Usage: Accurate incorporation of project facts, metrics, client names, and specific numbers from project data.\n"
            "4. Completeness: Coverage of all essential sales elements (objectives, solutions, client profile, call to action).\n"
            "5. Persuasiveness: Convincing power, compelling narrative, and urgency created in the text.\n"
            "6. Business Value: Highlights ROI, strategic business outcomes, and tangible client value.\n\n"
            "Score each metric out of 10.0. Be objective and critical. Provide concrete feedback."
        )

        user_prompt = (
            f"Original Project Facts/Data:\n{project_facts}\n\n"
            f"Business Requirements (if any):\n{business_requirements or 'None'}\n\n"
            f"Generated Sales Brief:\n{sales_brief}\n\n"
            "Perform the evaluation and output the metrics in the requested JSON structure."
        )

        try:
            result, _ = self.llm_provider.call_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=SalesBriefMetrics
            )
            
            # Ensure overall score is correct average
            scores = [
                result.readability,
                result.professionalism,
                result.evidence_usage,
                result.completeness,
                result.persuasiveness,
                result.business_value
            ]
            overall_avg = sum(scores) / len(scores)
            
            return SalesBriefMetrics(
                readability=result.readability,
                professionalism=result.professionalism,
                evidence_usage=result.evidence_usage,
                completeness=result.completeness,
                persuasiveness=result.persuasiveness,
                business_value=result.business_value,
                overall=round(overall_avg, 2),
                feedback=result.feedback
            )
            
        except Exception as e:
            logger.error(f"Sales brief evaluation failed: {e}")
            return SalesBriefMetrics(
                readability=5.0,
                professionalism=5.0,
                evidence_usage=5.0,
                completeness=5.0,
                persuasiveness=5.0,
                business_value=5.0,
                overall=5.0,
                feedback=f"Evaluator error: {e}"
            )
