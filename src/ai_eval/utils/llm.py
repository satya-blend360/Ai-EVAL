import os
import json
import time
import random
from typing import Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from ai_eval.utils.logger import logger
from ai_eval.config import (
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    OPENAI_MODEL,
    ANTHROPIC_MODEL,
    USE_MOCK_FALLBACK
)

T = TypeVar('T', bound=BaseModel)

class LLMProvider:
    """Unified manager for calling LLMs (OpenAI, Anthropic, or Mock Fallback)."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or DEFAULT_PROVIDER).split("#", 1)[0].strip().lower()
        self.model = model or DEFAULT_MODEL
        self.openai_model = model if model and self.provider == "openai" else OPENAI_MODEL
        self.anthropic_model = model if model and self.provider == "anthropic" else ANTHROPIC_MODEL

        # Explicit mock mode is still useful for tests and offline demos.
        self.is_mock = False
        if self.provider == "mock":
            self.is_mock = True
        elif self.provider not in {"openai", "anthropic", "auto"}:
            raise ValueError(f"Unsupported provider: {self.provider}")

        if self.is_mock:
            logger.info("LLMProvider initialized in MOCK Mode.")
        else:
            logger.info(
                "LLMProvider initialized with real provider fallback chain: "
                + " -> ".join(self._provider_chain())
            )

        self.call_history = []

    def call_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.0
    ) -> tuple[T, Dict[str, Any]]:
        """
        Calls the LLM with structured output matching the provided Pydantic model.
        Returns the parsed model and metadata (tokens, latency, cost).
        """
        start_time = time.time()

        if self.is_mock:
            # Generate mock data matching response_model
            latency = random.uniform(0.3, 1.2)  # simulate network delay
            time.sleep(latency)

            mock_data = self._generate_mock_data(response_model, user_prompt)
            latency_ms = (time.time() - start_time) * 1000

            # Estimate tokens
            prompt_tokens = len(system_prompt + user_prompt) // 4
            completion_tokens = len(json.dumps(mock_data)) // 4
            cost = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000  # mock gpt-4o-mini pricing

            metadata = {
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
            parsed_object = response_model.model_validate(mock_data)
        else:
            parsed_object, metadata = self._call_with_provider_fallback(
                system_prompt,
                user_prompt,
                response_model,
                temperature,
                start_time,
            )

        self.call_history.append(metadata)
        return parsed_object, metadata

    def _provider_chain(self) -> list[str]:
        if self.provider == "anthropic":
            return ["anthropic", "openai"]
        return ["openai", "anthropic"]

    def _call_with_provider_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float,
        start_time: float,
    ) -> tuple[T, Dict[str, Any]]:
        errors = []

        for provider in self._provider_chain():
            if provider == "openai":
                if not OPENAI_API_KEY:
                    errors.append("OpenAI: OPENAI_API_KEY is missing")
                    continue
                model = self.openai_model
                call = self._call_openai
            else:
                if not ANTHROPIC_API_KEY:
                    errors.append("Anthropic: ANTHROPIC_API_KEY is missing")
                    continue
                model = self.anthropic_model
                call = self._call_anthropic

            try:
                parsed_object, metadata = call(
                    system_prompt,
                    user_prompt,
                    response_model,
                    temperature,
                    start_time,
                    model,
                )
                metadata["provider"] = provider
                metadata["model"] = model
                logger.info(f"LLM call succeeded with {provider} model {model}.")
                return parsed_object, metadata
            except Exception as exc:
                error_text = self._sanitize_error(exc)
                logger.error(f"{provider.title()} API call failed: {error_text}", exc_info=True)
                errors.append(f"{provider.title()}: {error_text}")

        detail = " | ".join(errors) if errors else "No provider attempts were made."
        raise RuntimeError(
            "API keys not working. OpenAI failed and Anthropic fallback also failed. "
            "Please change or add new API keys. Details: "
            f"{detail}"
        )

    def _sanitize_error(self, exc: Exception) -> str:
        message = f"{type(exc).__name__}: {exc}"
        for secret in [OPENAI_API_KEY, ANTHROPIC_API_KEY]:
            if secret:
                message = message.replace(secret, "[redacted]")
        return message[:500]

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float,
        start_time: float,
        model: str,
    ) -> tuple[T, Dict[str, Any]]:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=response_model,
            temperature=temperature
        )

        latency_ms = (time.time() - start_time) * 1000
        choice = response.choices[0]
        parsed_object = choice.message.parsed
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else len(system_prompt + user_prompt) // 4
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens

        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        metadata = {
            "latency_ms": latency_ms,
            "cost_usd": cost,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        return parsed_object, metadata

    def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float,
        start_time: float,
        model: str,
    ) -> tuple[T, Dict[str, Any]]:
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_core.prompts import ChatPromptTemplate
        except ImportError as exc:
            raise RuntimeError("langchain-anthropic is not installed. Run `pip install -r requirements.txt`.") from exc

        chat_kwargs = {
            "model": model,
            "anthropic_api_key": ANTHROPIC_API_KEY,
        }
        if not model.startswith(("claude-fable-5", "claude-opus-5", "claude-sonnet-5")):
            chat_kwargs["temperature"] = temperature
        chat = ChatAnthropic(**chat_kwargs)

        structured_llm = chat.with_structured_output(response_model)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])

        chain = prompt | structured_llm
        result = chain.invoke({})

        latency_ms = (time.time() - start_time) * 1000

        prompt_tokens = len(system_prompt + user_prompt) // 4
        completion_tokens = len(json.dumps(result.model_dump())) // 4
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        metadata = {
            "latency_ms": latency_ms,
            "cost_usd": cost,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
        return result, metadata

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimates pricing in USD."""
        # Simple lookup table for known models
        rates = {
            "gpt-4o": (5.00 / 1_000_000, 15.00 / 1_000_000),
            "gpt-4o-mini": (0.150 / 1_000_000, 0.600 / 1_000_000),
            "gpt-4-turbo": (10.00 / 1_000_000, 30.00 / 1_000_000),
            "gpt-3.5-turbo": (0.50 / 1_000_000, 1.50 / 1_000_000),
            "claude-sonnet-5": (3.00 / 1_000_000, 15.00 / 1_000_000),
            "claude-opus-5": (5.00 / 1_000_000, 25.00 / 1_000_000),
            "claude-3-5-sonnet": (3.00 / 1_000_000, 15.00 / 1_000_000),
            "claude-3-opus": (15.00 / 1_000_000, 75.00 / 1_000_000),
            "claude-3-haiku": (0.25 / 1_000_000, 1.25 / 1_000_000),
        }

        # Find matches
        for key, (in_rate, out_rate) in rates.items():
            if key in model:
                return (prompt_tokens * in_rate) + (completion_tokens * out_rate)

        # Default: gpt-4o-mini rates
        return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)

    def _generate_mock_data(self, response_model: Type[T], user_prompt: str) -> Dict[str, Any]:
        """Generates realistic mock data based on the requested output schema."""
        model_name = response_model.__name__

        if "Extraction" in model_name:
            if "accuracy" in response_model.model_fields:
                return {
                    "accuracy": round(random.uniform(88, 98), 1),
                    "completeness": round(random.uniform(90, 99), 1),
                    "confidence_score": round(random.uniform(92, 98), 1),
                    "citation_coverage": round(random.uniform(85, 96), 1),
                    "missing_field_detection": round(random.uniform(90, 100), 1),
                    "field_details": {}
                }
        elif "Judge" in model_name:
            if "accuracy" in response_model.model_fields:
                return {
                    "accuracy": round(random.uniform(8.8, 9.8), 1),
                    "completeness": round(random.uniform(9.0, 9.9), 1),
                    "relevance": round(random.uniform(9.2, 10.0), 1),
                    "groundedness": round(random.uniform(8.5, 9.6), 1),
                    "usefulness": round(random.uniform(8.8, 9.8), 1),
                    "overall": round(random.uniform(8.8, 9.7), 2),
                    "reasoning": "The system output is highly accurate, matching the reference facts precisely. All required details about the tech stack are present and correctly formatted, and the language is clear and useful."
                }

        if "Hallucination" in model_name:
            # Hallucination checking: claim extraction
            claims = [
                {"claim": "The project was executed for Microsoft in 2024.", "is_supported": True, "evidence": "Reference mentions contract with Microsoft in Q2 2024.", "reasoning": "Exact match found."},
                {"claim": "The solution utilized Python, Qdrant, and Azure OpenAI.", "is_supported": True, "evidence": "Tech stack includes Python, Qdrant vector database, and Azure OpenAI endpoint.", "reasoning": "Exact match found."},
                {"claim": "The project reduced response latency by 85%.", "is_supported": True, "evidence": "Performance improvements section highlights latency reduction from 1200ms to 180ms (85% speedup).", "reasoning": "Exact match found."},
                {"claim": "The project generated $5M in annual recurring revenue.", "is_supported": False, "evidence": "None", "reasoning": "The reference mentions project billing was $500,000, not $5M ARR. This is a hallucinated claim."}
            ]

            # Randomly decide if there's a hallucination
            has_hallucination = random.choice([True, False, False, False])  # 25% chance of hallucination in mock
            if not has_hallucination:
                claims[3]["is_supported"] = True
                claims[3]["evidence"] = "Reference mentions project billing was $5M over two years."
                claims[3]["reasoning"] = "Supported by page 2 financial summary."

            supported = sum(1 for c in claims if c["is_supported"])
            rate = ((len(claims) - supported) / len(claims)) * 100

            return {
                "supported_claims": supported,
                "total_claims": len(claims),
                "hallucination_rate": round(rate, 1),
                "claims": claims
            }

        if "SalesBrief" in model_name:
            # Sales brief evaluation
            readability = round(random.uniform(8.0, 9.8), 1)
            professionalism = round(random.uniform(8.5, 9.9), 1)
            evidence_usage = round(random.uniform(7.8, 9.6), 1)
            completeness = round(random.uniform(8.0, 9.5), 1)
            persuasiveness = round(random.uniform(8.2, 9.8), 1)
            business_value = round(random.uniform(8.0, 9.7), 1)
            overall = round((readability + professionalism + evidence_usage + completeness + persuasiveness + business_value) / 6, 2)

            return {
                "readability": readability,
                "professionalism": professionalism,
                "evidence_usage": evidence_usage,
                "completeness": completeness,
                "persuasiveness": persuasiveness,
                "business_value": business_value,
                "overall": overall,
                "feedback": "Excellent sales brief. The tone is highly professional, and it clearly articulates the business value and ROI. Incorporating a few more metrics about the technology performance would make the pitch even stronger."
            }

        # Fallback dictionary for basic fields
        res = {}
        for field_name, field_def in response_model.model_fields.items():
            if field_name == "accuracy" or field_name == "completeness" or field_name == "citation_coverage" or field_name == "missing_field_detection" or field_name == "confidence_score":
                res[field_name] = round(random.uniform(85.0, 99.0), 1)
            elif field_name == "overall" or field_name == "relevance" or field_name == "groundedness":
                res[field_name] = round(random.uniform(8.5, 9.8), 1)
            elif field_name == "reasoning" or field_name == "feedback":
                res[field_name] = "Generated placeholder reasoning based on mock data analysis."
            elif field_def.annotation == str:
                res[field_name] = f"Mock {field_name}"
            elif field_def.annotation == int:
                res[field_name] = random.randint(1, 100)
            elif field_def.annotation == float:
                res[field_name] = round(random.uniform(0.0, 1.0), 2)
            elif field_def.annotation == bool:
                res[field_name] = True
            elif getattr(field_def.annotation, "__origin__", None) is list:
                res[field_name] = []
            elif getattr(field_def.annotation, "__origin__", None) is dict:
                res[field_name] = {}
            else:
                res[field_name] = None

        return res
