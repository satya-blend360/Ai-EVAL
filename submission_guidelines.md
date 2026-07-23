# Project Intelligence Hub (PIH) - Submission & Evaluation Guidelines

To programmatically evaluate and score user-submitted projects using your **Judges Scorecard Rubric** (Extraction Accuracy, Retrieval Quality, Sales Brief Quality, Hallucination Risk, Completeness, Cost Efficiency, and Response Time), you need to collect specific artifacts and data points from the user. 

Asking only for a **GitHub Repository URL** and a **Live Prototype URL** is a great starting point, but it is **not sufficient** for an automated evaluation engine to run metrics.

Here is what you need to collect from the user, how they should format it, and how it maps to your evaluation metrics.

---

## 📥 Required Submission Inputs

We recommend requiring the user to submit three items:
1. **GitHub Repository URL** (For code audits and manual reviews)
2. **Live Prototype URL** (For interactive UX validation)
3. **Either an API Sandbox Endpoint OR an Evaluation Trace File** (Choose one of the two strategies below for automated scoring):

---

### Strategy A: The Evaluation Trace File (Recommended)
Instead of your grading system trying to call their live server (which could have auth issues, rate limits, or be offline), you provide the user with a standardized **Test Input JSON** (containing sample intake documents, search queries, and questions). 

The user runs these inputs through their system and uploads the resulting outputs as an `execution_trace.json` file.

#### Expected `execution_trace.json` Schema:
```json
{
  "intake_results": [
    {
      "case_id": "intake_case_001",
      "extracted_fields": {
        "Project Name": "Retail Demand Forecasting",
        "Client": "ABC Retail",
        "Buyer Role": "VP of Supply Chain",
        "Function": "Demand Planning",
        "Lead Source": "Inbound RFP",
        "Business Objective": "Reduce inventory overhead by 15%",
        "Outcomes": "Achieved 18% inventory reduction and saved $1.2M",
        "Solution": "Time-series forecasting models using Prophet",
        "Technology": "Python, Snowflake, Prophet",
        "Team": "2 Data Scientists, 1 Data Engineer",
        "Differentiators": "Proprietary forecasting framework",
        "Revenue/Billing": "$220,000",
        "Start Year": "2024"
      },
      "field_citations": {
        "Project Name": "Project 'Demand Forecaster'...",
        "Client": "delivered for ABC Retail in..."
      },
      "api_performance": {
        "latency_ms": 3200.0,
        "prompt_tokens": 1200,
        "completion_tokens": 350,
        "model_used": "gpt-4o-mini"
      }
    }
  ],
  "search_results": [
    {
      "query": "Healthcare projects using Snowflake and ROI > 20%",
      "retrieved_project_ids": ["proj_health_01", "proj_health_03"],
      "api_performance": {
        "latency_ms": 450.0,
        "prompt_tokens": 500,
        "completion_tokens": 80,
        "model_used": "gpt-4o-mini"
      }
    }
  ],
  "qa_results": [
    {
      "project_id": "proj_health_01",
      "question": "What database was used?",
      "generated_answer": "Snowflake was utilized as the primary cloud data warehouse.",
      "retrieved_context_snippets": [
        "All historical claims data was loaded into Snowflake databases."
      ],
      "api_performance": {
        "latency_ms": 1500.0,
        "prompt_tokens": 800,
        "completion_tokens": 60,
        "model_used": "gpt-4o-mini"
      }
    }
  ],
  "sales_brief_results": [
    {
      "project_id": "proj_health_01",
      "sales_brief_text": "# Sales Brief: Claims Automation...",
      "api_performance": {
        "latency_ms": 4800.0,
        "prompt_tokens": 2500,
        "completion_tokens": 900,
        "model_used": "gpt-4o-mini"
      }
    }
  ]
}
```

---

### Strategy B: Exposed API Sandbox Endpoints
If you want to test their live system in real-time, the user must implement four public, unauthenticated (or token-authenticated) API endpoints on their prototype backend:

1. `POST /api/eval/intake`: Expects raw text/file stream. Returns extracted 13 fields, citations, and LLM token usage metadata.
2. `POST /api/eval/search`: Expects query string. Returns ranked project list and token metadata.
3. `POST /api/eval/qa`: Expects project ID and question. Returns answer text, retrieved context snippets, and token metadata.
4. `POST /api/eval/sales_brief`: Expects project context. Returns generated brief text and token metadata.

Your evaluation framework will query these endpoints directly, measuring execution latency and parsing responses.

---

## 📊 How the Framework Maps Inputs to the Judges Scorecard

Here is how your evaluation engine will parse these user submissions to compute their grades:

| Metric | Required Input Data for Metric | How the Framework Computes It |
| :--- | :--- | :--- |
| **1. Extraction Accuracy (25%)** | `intake_results.extracted_fields` + Ground Truth values | Compares user's extracted values for the 13 fields against correct values using string, numeric, and LLM semantic checks. |
| **2. Retrieval Quality (25%)** | `search_results.retrieved_project_ids` + Ground Truth rankings | Measures search ordering using precision, recall, MRR, and NDCG calculations. |
| **3. Sales Brief Quality (20%)** | `sales_brief_results.sales_brief_text` | Grades the brief out of 10 across readability, persuasive tone, fact evidence, completeness, and value metrics. |
| **4. Hallucination Risk (10%)** | `qa_results.generated_answer` + `qa_results.retrieved_context_snippets` | Evaluates if the generated QA answers are fully supported by document evidence snippets, mapping to `100 - hallucination_rate`. |
| **5. Completeness (10%)** | `intake_results.extracted_fields` + Ground Truth values | Calculates the percentage of required project fields that the user's intake AI successfully populated (detecting and flagging missing info). |
| **6. Cost Efficiency (5%)** | `api_performance.prompt_tokens` + `api_performance.completion_tokens` + `model_used` | Computes USD pricing based on token usage. Scores 100 if cost is $\le \$0.002$ per transaction, scaling down to 0 if cost is $\ge \$0.02$. |
| **7. Response Time (5%)** | `api_performance.latency_ms` logs | Checks response times. Scores 100 if latency is $\le 500\text{ms}$ and scales linearly down to 0 if latency is $\ge 5000\text{ms}$. |
