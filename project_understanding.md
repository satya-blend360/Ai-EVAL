# Project Intelligence Hub (PIH) - AI Evaluation Framework

The **Project Intelligence Hub (PIH) AI Evaluation Framework** is a production-grade Python framework designed to assess, score, and audit the quality and performance of AI knowledge management systems. It supports qualitative LLM-as-a-Judge metrics, physical latency/cost analysis, search/retrieval performance, RAG metrics, sales brief rubric grading, and automatic factual claim auditing to identify hallucinations.

---

## 📂 Architecture Overview

The system is modularly organized:
- **Core Pipeline**: Orchestrated by [AIEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/core/evaluator.py#L33) in [evaluator.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/core/evaluator.py), which coordinates individual evaluation modules and calculates a final normalized score out of 100.
- **Evaluation Modules**: Located in [src/ai_eval/metrics/](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/):
  - [extraction.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/extraction.py) ([ExtractionEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/extraction.py#L8)): Compares extracted schema fields with ground truth data. Employs exact matching, numeric matching, token overlap checks, and falls back to LLM semantic checks for complex text fields.
  - [retrieval.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/retrieval.py) ([RetrievalEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/retrieval.py#L8)): Calculates search-specific metrics, including Precision@K, Recall@K, MRR, and NDCG, plus semantic relevance.
  - [rag.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/rag.py) ([RAGEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/rag.py#L40)): Analyzes the RAG triad (Faithfulness, Answer Relevancy, Groundedness, Context Precision, and Context Recall) via structured LLM responses.
  - [hallucination.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/hallucination.py) ([HallucinationEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/hallucination.py#L6)): Breaks down answers into atomic assertions and audits them against retrieved evidence blocks to track the exact hallucination rate.
  - [sales_brief.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/sales_brief.py) ([SalesBriefEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/sales_brief.py#L6)): Grades generated briefs from 1 to 10 across dimensions such as visual readability, tone professionalism, evidence usage, completeness, persuasiveness, and client ROI value.
  - [judge.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/judge.py) ([JudgeEvaluator](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/judge.py#L6)): General-purpose LLM-as-a-Judge evaluator for qualitative ratings (1-10) with reasoning.
  - [performance.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/performance.py) ([PerformanceTracker](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/metrics/performance.py#L6)): Tracks request latency, API costs (in USD), prompt/completion tokens, and throughput (tokens/sec).
- **Configuration & Utilities**:
  - [config.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/config.py): Stores system weights, API cost/latency thresholds, models, and directory targets.
  - [models.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/models.py): Defines Pydantic validation models (such as [EvaluationReport](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/models.py#L91)) enforcing schema safety on evaluation outputs.
  - [llm.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/utils/llm.py) ([LLMProvider](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/utils/llm.py#L18)): Unified wrapper to query OpenAI and Anthropic, with a fallback **Mock Mode** using synthetic generation.
  - [loader.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/data/loader.py): Loads test datasets from [test_data.json](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/test_data.json).
- **Dashboard**:
  - [app.py](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/dashboard/app.py): Streamlit web application providing a dark-themed visual playground, KPI breakdown cards, radar charts of components, historical trend graphs, and an interactive testbench.

---

## 📊 Judges Scorecard Rubric & Calculation

The system aggregates component scores into a single **overall normalized score (0-100)**:

| Category | Rubric Weight | Scoring Method |
| :--- | :--- | :--- |
| **Extraction Accuracy** | 25% | Field-by-field verification rate (0-100) |
| **Retrieval Quality** | 25% | Average of Precision@K, Recall@K, MRR, and NDCG (scaled 0-100) |
| **Sales Brief Quality** | 20% | Rubric grade scaled from 1-10 to 0-100 |
| **Hallucination Risk** | 10% | $100.0 - \text{Hallucination Rate}$ |
| **Completeness** | 10% | Percentage of required fields extracted (0-100) |
| **Cost Efficiency** | 5% | Normalized cost (100 if $\le \$0.002$, 0 if $\ge \$0.020$) |
| **Response Time** | 5% | Normalized latency (100 if $\le 500\text{ms}$, 0 if $\ge 5000\text{ms}$) |

### 🔄 Dynamic Weight Redistribution
If a component's evaluation data is omitted (e.g. only testing retrieval), [AIEvaluator._calculate_overall_score](file:///C:/Users/SaisrisatyaPadala/Desktop/projects/Ai%20EVAL/src/ai_eval/core/evaluator.py#L212) automatically sets its weight to `0.0` and scales the remaining active weights proportionally so that the overall score remains normalized out of 100.
