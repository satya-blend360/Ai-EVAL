# Project Intelligence Hub (PIH) - AI Evaluation Framework

A production-grade Python AI Evaluation Framework designed for the **Project Intelligence Hub (PIH)**. This framework continuously assesses, scores, and audits the performance of AI knowledge management systems. It provides modular services to evaluate information extraction, retrieval, retrieval-augmented generation (RAG), hallucination rates, sales briefs, and performance (tokens, latency, cost).

---

## 🚀 Key Features

* **Modular Architecture**: Clean, decoupled evaluation services for distinct AI features.
* **Unified Scoring Rubric**: Merges domain quality metrics (extraction, search, generation) and physical characteristics (cost, latency) into a single normalized score out of 100.
* **Robust Fallbacks**: Works out-of-the-box in **Mock Mode** if API keys are missing, and handles real API requests to OpenAI or Anthropic when keys are provided.
* **Semantic LLM-as-a-Judge**: Custom prompt-engineered evaluators for qualitative tasks (accuracy, completeness, relevance, groundedness, usefulness) yielding structured JSON outputs.
* **Factual Claim Auditing**: Automatically breaks down generated answers into atomic assertions and cross-references them with retrieved evidence blocks to track exact hallucination rates.
* **Visual Streamlit Dashboard**: Sleek dark mode dashboard displaying KPIs, sub-component breakdowns, historical run comparison charts, and an interactive testbench playground.

---

## 📂 Directory Structure

```text
ai-eval-framework/
│
├── .env.example                 # Configuration environment template
├── requirements.txt            # Python dependencies (Streamlit, Pandas, Plotly, LangChain, etc.)
├── README.md                   # Setup and execution documentation
├── run_eval.py                 # CLI script to execute standard evaluation pipeline
├── test_data.json              # Structured evaluation test cases
│
├── src/
│   └── ai_eval/
│       ├── __init__.py
│       ├── config.py           # Configuration manager (weights, thresholds, API keys)
│       ├── models.py           # Pydantic validation schemas for metrics inputs and outputs
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   └── evaluator.py    # Main evaluation engine coordinating all sub-evaluations
│       │
│       ├── metrics/
│       │   ├── __init__.py
│       │   ├── extraction.py   # Information extraction verification (accuracy, completeness, citations)
│       │   ├── retrieval.py    # Math metrics for search (Precision, Recall, MRR, NDCG, semantic relevance)
│       │   ├── rag.py          # RAG triad metrics (Faithfulness, Relevancy, Groundedness, Context Precision/Recall)
│       │   ├── hallucination.py# Factual claim verification & hallucination rate calculation
│       │   ├── sales_brief.py  # Sales brief multi-dimensional rubric grading (1-10)
│       │   ├── judge.py        # General-purpose LLM-as-a-Judge agent (1-10)
│       │   └── performance.py  # Performance tracker (latency, API cost, tokens, and throughput)
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   └── loader.py       # Helper functions to load evaluation dataset cases
│       │
│       └── utils/
│           ├── __init__.py
│           ├── llm.py          # Resilient LLM API wrapper (supports OpenAI, Anthropic, and Mock fallback)
│           └── logger.py       # Standardized logger
│
├── dashboard/
│   └── app.py                  # Interactive Streamlit dashboard
│
├── tests/                      # Pytest unit tests
│   ├── __init__.py
│   ├── test_extraction.py      # Tests exact/substring/numeric match logic
│   ├── test_retrieval.py       # Tests search metrics calculations
│   ├── test_performance.py     # Tests latency and cost tracking calculations
│   ├── test_evaluator.py       # Tests scoring weight redistribution
│   └── test_mock_evaluators.py # Integration tests for prompt-based metrics
│
└── reports/                    # Folder containing JSON evaluation reports
    └── sample_report.json
```

---

## 🛠️ Setup & Installation

### 1. Clone & Initialize Workspace
Navigate to your workspace directory and create a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup Configuration
Copy the `.env.example` file to `.env`:
```powershell
cp .env.example .env
```
Open `.env` and fill in your API keys if you want to run live LLM evaluations. If no keys are specified, the framework will gracefully fall back to **Mock Mode** using high-fidelity synthetically generated mock evaluation results.

---

## 📊 Scoring Rubric & Metrics

The **Overall Score** is calculated as a normalized value from **0 to 100** according to the following weights:

| Category | Rubric Weight | Metric Calculation Method |
| :--- | :--- | :--- |
| **Extraction Accuracy** | 20% | Field-by-field check (exact, substring, numeric, or semantic LLM check) |
| **Retrieval Quality** | 25% | Balanced average of Precision@K, Recall, MRR, and NDCG ($0.0 - 1.0 \times 100$) |
| **RAG Quality** | 20% | Average of Context Precision, Context Recall, Faithfulness, Relevancy, and Groundedness |
| **Sales Brief Quality** | 15% | Multi-dimensional grade (Readability, Professionalism, Evidence, Completeness, Persuasiveness, Value) |
| **Hallucination Safety** | 10% | Inverse of hallucination rate: $100.0 - \text{Hallucination Rate}$ |
| **Cost Efficiency** | 5% | Normalized cost (Score 100 if $\le \$0.002$, 0 if $\ge \$0.020$, linear interpolation) |
| **Latency** | 5% | Normalized latency (Score 100 if $\le 500\text{ms}$, 0 if $\ge 5000\text{ms}$, linear interpolation) |

> [!NOTE]
> **Dynamic Weight Redistribution**: If a sub-evaluation data block is omitted (e.g. you only want to evaluate RAG), the framework automatically sets its weight to 0 and redistributes the remaining weights proportionally so that the overall score remains normalized out of 100.

---

## 💻 Running the Framework

### Run Evaluation CLI
To run a full evaluation pipeline on the sample test cases and save a JSON report under the `reports/` folder, execute:
```powershell
python run_eval.py
```
This prints a structured, easy-to-read summary to the console containing weighted component scores and execution performance statistics.

### Run Streamlit Dashboard
To launch the visual assessment console, execute:
```powershell
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501`. Here you can select historical runs, view deep dives of each evaluation category (such as exact claim audits highlighting hallucinations in red), and perform real-time evaluations using the playground.

### Run Unit Tests
To run the automated tests using `pytest` to verify mathematical and logical correctness:
```powershell
pytest
```
All tests are located in the `tests/` directory and check core metric math, parsing, and mock model pipelines.
