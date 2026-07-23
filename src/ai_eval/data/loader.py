import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ai_eval.utils.logger import logger
from ai_eval.config import ROOT_DIR

DEFAULT_DATA_PATH = ROOT_DIR / "test_data.json"

def load_evaluation_data(file_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Loads evaluation test cases from a JSON file."""
    path = Path(file_path) if file_path else DEFAULT_DATA_PATH
    
    if not path.exists():
        logger.warning(f"Evaluation dataset not found at {path}. Returning empty dataset.")
        return {
            "extraction_cases": [],
            "retrieval_cases": [],
            "rag_cases": [],
            "hallucination_cases": [],
            "sales_brief_cases": [],
            "judge_cases": []
        }
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Loaded evaluation dataset from {path}")
            return data
    except Exception as e:
        logger.error(f"Failed to load evaluation dataset: {e}")
        return {}

def get_extraction_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("extraction_cases", [])

def get_retrieval_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("retrieval_cases", [])

def get_rag_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("rag_cases", [])

def get_hallucination_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("hallucination_cases", [])

def get_sales_brief_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("sales_brief_cases", [])

def get_judge_cases(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return load_evaluation_data(file_path).get("judge_cases", [])
