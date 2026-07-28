import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project root path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DEFAULT_WEIGHTS = {
    "extraction_accuracy": 0.25,
    "retrieval_quality": 0.25,
    "sales_brief_quality": 0.20,
    "hallucination_risk": 0.10,
    "completeness": 0.10,
    "cost_efficiency": 0.05,
    "response_time": 0.05
}

# Thresholds for converting raw physical values into normalized 0-100 scores
# Cost: Lower is better. Target is <= $0.002, Max unacceptable is >= $0.02
COST_TARGET_USD = 0.002
COST_MAX_USD = 0.020

# Latency: Lower is better. Target is <= 500ms, Max unacceptable is >= 5000ms
LATENCY_TARGET_MS = 500
LATENCY_MAX_MS = 5000

# LLM Configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai").lower()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
USE_MOCK_FALLBACK = os.getenv("USE_MOCK_FALLBACK", "True").lower() in ("true", "1", "yes")

# Directories
REPORTS_DIR = ROOT_DIR / "reports"
DATA_DIR = ROOT_DIR / "data"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
