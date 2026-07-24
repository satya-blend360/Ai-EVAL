"""Data loader exports for the AI evaluation package."""

__all__ = [
    "load_evaluation_data",
    "get_extraction_cases",
    "get_retrieval_cases",
    "get_rag_cases",
    "get_hallucination_cases",
    "get_sales_brief_cases",
    "get_judge_cases",
]


def __getattr__(name):
    if name in __all__:
        from ai_eval.data import loader

        return getattr(loader, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
