import time
from typing import List, Dict, Any
from ai_eval.models import PerformanceMetrics
from ai_eval.utils.logger import logger

class PerformanceTracker:
    """Tracks latency, token usage, cost, and throughput for evaluation requests."""

    def __init__(self):
        self.latency_ms = 0.0
        self.cost_usd = 0.0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def start_timer(self) -> float:
        """Helper to start measuring duration in seconds."""
        return time.time()

    def stop_timer(self, start_time: float):
        """Stops the timer and adds to latency."""
        duration_ms = (time.time() - start_time) * 1000
        self.latency_ms += duration_ms

    def record_api_call(self, metadata: Dict[str, Any]):
        """Records token and cost metadata from an LLM API response."""
        self.prompt_tokens += metadata.get("prompt_tokens", 0)
        self.completion_tokens += metadata.get("completion_tokens", 0)
        self.total_tokens += metadata.get("total_tokens", 0)
        self.cost_usd += metadata.get("cost_usd", 0.0)
        
        # If the API call returns latency, we add it, otherwise we rely on stop_timer
        if "latency_ms" in metadata:
            self.latency_ms += metadata["latency_ms"]

    def compile(self) -> PerformanceMetrics:
        """Compiles the tracked values into a PerformanceMetrics model."""
        latency_sec = self.latency_ms / 1000.0
        throughput = (self.total_tokens / latency_sec) if latency_sec > 0 else 0.0
        
        return PerformanceMetrics(
            latency_ms=round(self.latency_ms, 2),
            cost_usd=round(self.cost_usd, 6),
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            throughput_tokens_per_sec=round(throughput, 2)
        )
