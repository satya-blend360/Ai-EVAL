import time
from ai_eval.metrics.performance import PerformanceTracker

def test_performance_tracker_init():
    tracker = PerformanceTracker()
    assert tracker.latency_ms == 0.0
    assert tracker.cost_usd == 0.0
    assert tracker.prompt_tokens == 0
    assert tracker.completion_tokens == 0
    assert tracker.total_tokens == 0

def test_performance_tracker_timer():
    tracker = PerformanceTracker()
    start = tracker.start_timer()
    time.sleep(0.1)  # wait 100ms
    tracker.stop_timer(start)
    assert tracker.latency_ms >= 90.0  # approximate boundary
    assert tracker.latency_ms <= 300.0

def test_performance_tracker_api_record():
    tracker = PerformanceTracker()
    metadata = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "cost_usd": 0.0003,
        "latency_ms": 250.0
    }
    tracker.record_api_call(metadata)
    
    metrics = tracker.compile()
    assert metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 50
    assert metrics.total_tokens == 150
    assert metrics.cost_usd == 0.0003
    assert metrics.latency_ms == 250.0
    assert metrics.throughput_tokens_per_sec == 600.0  # 150 tokens / 0.25 sec
