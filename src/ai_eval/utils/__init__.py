"""Utility exports for the AI evaluation package.

Keep this module lightweight. Streamlit Cloud's Python 3.14 import loader can
raise KeyError during circular package initialization when __init__ eagerly
imports submodules that import this package again.
"""

__all__ = ["LLMProvider", "logger"]


def __getattr__(name):
    if name == "LLMProvider":
        from ai_eval.utils.llm import LLMProvider

        return LLMProvider
    if name == "logger":
        from ai_eval.utils.logger import logger

        return logger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
