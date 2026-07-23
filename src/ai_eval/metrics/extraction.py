import re
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ai_eval.utils.llm import LLMProvider
from ai_eval.models import ExtractionMetrics, ExtractionFieldResult
from ai_eval.utils.logger import logger

class ExtractionEvaluator:
    """Evaluates the quality of information extraction against ground truth data."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or LLMProvider()

    def evaluate(
        self,
        extracted_fields: Dict[str, Any],
        expected_fields: Dict[str, Any],
        source_text: Optional[str] = None,
        field_citations: Optional[Dict[str, str]] = None,
        confidence_scores: Optional[Dict[str, float]] = None
    ) -> ExtractionMetrics:
        """
        Evaluates extraction metrics.
        
        Args:
            extracted_fields: Dict of field names and their extracted values
            expected_fields: Dict of field names and their expected (ground truth) values
            source_text: The original document content to verify citations
            field_citations: Dict mapping fields to the exact quote/citation text
            confidence_scores: Dict of confidence scores (0.0 - 1.0) provided by the extractor
        """
        logger.info("Starting Information Extraction Evaluation...")
        
        field_details = {}
        correct_count = 0
        total_eval_fields = 0
        
        # Track missing fields metrics
        expected_missing_fields = set()
        correctly_detected_missing = 0
        incorrectly_extracted_missing = 0
        
        expected_present_fields = 0
        extracted_present_fields = 0
        
        citations_checked = 0
        valid_citations = 0
        
        all_fields = set(expected_fields.keys()).union(set(extracted_fields.keys()))
        
        for field in all_fields:
            expected_val = expected_fields.get(field)
            extracted_val = extracted_fields.get(field)
            
            # 1. Determine completeness and missing field flags
            is_expected_empty = self._is_empty(expected_val)
            is_extracted_empty = self._is_empty(extracted_val)
            
            if is_expected_empty:
                expected_missing_fields.add(field)
                if is_extracted_empty:
                    correctly_detected_missing += 1
                else:
                    incorrectly_extracted_missing += 1
            else:
                expected_present_fields += 1
                if not is_extracted_empty:
                    extracted_present_fields += 1
            
            # Skip scoring accuracy for fields that aren't in expected or are expected to be missing
            if is_expected_empty:
                # If we correctly left it empty, it's correct. If we hallucinated something, it's incorrect.
                is_correct = is_extracted_empty
                comments = "Correctly left empty." if is_correct else f"Hallucinated value: '{extracted_val}' when field was missing."
            else:
                total_eval_fields += 1
                # 2. Score Accuracy (with semantic matching for complex text)
                is_correct, comments = self._evaluate_field_accuracy(field, extracted_val, expected_val)
                if is_correct:
                    correct_count += 1
            
            # 3. Check citations
            citation_provided = False
            citation_valid = False
            
            if field_citations and field_citations.get(field):
                citation_provided = True
                citations_checked += 1
                citation_quote = field_citations[field]
                
                if source_text and citation_quote:
                    # Clean whitespaces for robust matching
                    clean_source = re.sub(r'\s+', ' ', source_text).lower()
                    clean_quote = re.sub(r'\s+', ' ', citation_quote).lower()
                    if clean_quote in clean_source:
                        citation_valid = True
                        valid_citations += 1
                    else:
                        citation_valid = False
                else:
                    # If no source text is provided but citation exists, we treat it as valid by default
                    citation_valid = True
                    valid_citations += 1
            
            field_details[field] = ExtractionFieldResult(
                field_name=field,
                expected_value=expected_val,
                extracted_value=extracted_val,
                is_correct=is_correct,
                is_missing=is_extracted_empty,
                citation_provided=citation_provided,
                citation_valid=citation_valid,
                comments=comments
            )
            
        # Calculate rates
        accuracy_rate = (correct_count / total_eval_fields * 100) if total_eval_fields > 0 else 100.0
        
        completeness_rate = (extracted_present_fields / expected_present_fields * 100) if expected_present_fields > 0 else 100.0
        
        # Missing Field Detection: Accuracy of classification (true negative + true positive)
        # TN = correctly left empty, FP = hallucinated value.
        # We calculate: correctly_detected / total expected missing
        missing_count = len(expected_missing_fields)
        missing_detect_rate = (correctly_detected_missing / missing_count * 100) if missing_count > 0 else 100.0
        
        # Citation coverage: percentage of extracted non-empty fields that have valid citations
        citation_cov_rate = (valid_citations / extracted_present_fields * 100) if extracted_present_fields > 0 else 100.0
        
        # Confidence score
        avg_confidence = 100.0
        if confidence_scores:
            scores = [v for k, v in confidence_scores.items() if k in extracted_fields and not self._is_empty(extracted_fields[k])]
            if scores:
                # scale to 0-100 if provided as 0-1
                avg_val = sum(scores) / len(scores)
                avg_confidence = avg_val * 100.0 if avg_val <= 1.0 else avg_val
                
        return ExtractionMetrics(
            accuracy=round(accuracy_rate, 2),
            completeness=round(completeness_rate, 2),
            confidence_score=round(avg_confidence, 2),
            citation_coverage=round(citation_cov_rate, 2),
            missing_field_detection=round(missing_detect_rate, 2),
            field_details=field_details
        )
        
    def _is_empty(self, val: Any) -> bool:
        if val is None:
            return True
        if isinstance(val, str) and val.strip() in ("", "None", "N/A", "n/a", "null", "unknown"):
            return True
        if isinstance(val, list) and len(val) == 0:
            return True
        if isinstance(val, dict) and len(val) == 0:
            return True
        return False
        
    def _evaluate_field_accuracy(self, field: str, extracted: Any, expected: Any) -> tuple[bool, str]:
        """Checks if the extracted field is correct relative to the expected field."""
        if self._is_empty(extracted):
            return False, "Value was expected but is missing."
            
        # 1. Exact string matching (after normalization)
        norm_ext = str(extracted).strip().lower()
        norm_exp = str(expected).strip().lower()
        
        if norm_ext == norm_exp:
            return True, "Exact match."
            
        # Try numeric matching
        try:
            # strip non-numeric characters for simple values like start year, revenue
            num_ext = re.sub(r'[^\d.]', '', norm_ext)
            num_exp = re.sub(r'[^\d.]', '', norm_exp)
            if num_ext and num_exp and float(num_ext) == float(num_exp):
                return True, "Numeric equivalent match."
        except ValueError:
            pass

        # 2. Check if a simple token overlap is sufficient for short fields
        short_fields = {"client", "buyer role", "lead source", "start year", "revenue/billing", "function"}
        if field.lower() in short_fields:
            # If one is a substring of another (e.g. "Microsoft Corporation" and "Microsoft")
            if norm_ext in norm_exp or norm_exp in norm_ext:
                return True, "Substring match."
                
        # 3. For complex text fields, use LLM semantic judge
        # Complex fields: Business Objective, Outcomes, Solution, Technology, Team, Differentiators
        logger.info(f"Using LLM semantic check for field '{field}'...")
        
        class SemanticEquivalence(BaseModel):
            is_equivalent: bool
            reason: str

        system_prompt = (
            "You are an expert AI Evaluation Auditor.\n"
            "Your task is to judge whether an extracted value is semantically equivalent "
            "to the expected ground truth value for a specific field in a project record.\n"
            "Minor phrasing changes, synonyms, or differences in list formatting are acceptable. "
            "However, missing critical information or adding incorrect facts is NOT equivalent."
        )
        
        user_prompt = (
            f"Field Name: {field}\n"
            f"Expected Ground Truth: {expected}\n"
            f"Extracted Value: {extracted}\n\n"
            "Does the extracted value convey the same information as the expected ground truth?"
        )
        
        try:
            result, _ = self.llm_provider.call_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=SemanticEquivalence
            )
            return result.is_equivalent, result.reason
        except Exception as e:
            logger.error(f"Semantic checking failed for field {field}: {e}")
            # fallback to simple word overlap
            overlap = set(norm_ext.split()).intersection(set(norm_exp.split()))
            is_match = len(overlap) >= min(len(norm_exp.split()), 2)
            return is_match, f"Fallback overlap check. Common words: {list(overlap)}"
