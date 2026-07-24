"""Core exports for the AI evaluation package."""

__all__ = ["AIEvaluator"]


def __getattr__(name):
    if name == "AIEvaluator":
        from ai_eval.core.evaluator import AIEvaluator

        return AIEvaluator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
