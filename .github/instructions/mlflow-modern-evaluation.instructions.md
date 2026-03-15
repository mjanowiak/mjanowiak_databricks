---
description: "Use when writing or updating MLflow evaluation, GenAI evaluation, tracing, scorer, judge, monitoring, or Databricks notebook code. Enforces MLflow 3.x evaluation patterns and guardrails instead of older MLflow evaluation APIs."
name: "Modern MLflow Evaluation"
applyTo: "notebooks/**, **/*.py, **/*.ipynb"
---

# Modern MLflow Evaluation Guidelines

- For GenAI, agent, and RAG evaluation, prefer `mlflow.genai.evaluate(...)` and `mlflow.genai.scorers`.
- Prefer MLflow 3.x evaluation datasets and tracing-based evaluation flows over ad hoc legacy evaluation code.
- Do not introduce new uses of older `mlflow.evaluate(...)` for GenAI evaluation when `mlflow.genai.evaluate(...)` is the appropriate API.

## Core Evaluation Pattern

- Structure evaluation around three parts: evaluation data, a traced `predict_fn` or traced app, and explicit scorers.
- Prefer versioned MLflow Evaluation Datasets for reusable or production-grade evaluation sets.
- Use a list of dictionaries, Pandas DataFrame, or Spark DataFrame only for quick prototyping or when data already exists in that format.
- Keep `inputs` keys aligned with the `predict_fn` parameter names. If the app interface does not match the dataset schema, add a small wrapper function instead of mutating the dataset shape inconsistently.

```python
import mlflow
from mlflow.genai.scorers import Correctness, Safety, Guidelines

@mlflow.trace
def answer_question(question: str) -> str:
    return app(question)

results = mlflow.genai.evaluate(
    data=eval_data,
    predict_fn=answer_question,
    scorers=[
        Correctness(),
        Safety(),
        Guidelines(name="helpfulness", guidelines="Answer accurately and concisely."),
    ],
)
```

## Tracing Requirements

- Prefer traced evaluation targets. A `predict_fn` should emit one trace per invocation or call a function decorated with `@mlflow.trace`.
- For trace-based evaluation, prefer evaluating MLflow traces directly when outputs already exist in traces.
- For multi-turn evaluations and automatic conversation evaluation, ensure session IDs are present in traces.

## Scorer Selection

- Choose scorer type deliberately:
- Use code-based scorers for objective or deterministic checks.
- Use LLM judges for subjective or semantic quality checks such as correctness, safety, relevance, and guideline adherence.
- For RAG systems, usually start with `Correctness`, `Safety`, `RelevanceToQuery`, and retrieval-aware scorers such as `RetrievalRelevance` when trace or retrieval context is available.
- For multi-turn agent workflows, consider conversation or agent-oriented scorers instead of only single-turn answer quality.
- Prefer multiple complementary scorers rather than a single pass-fail metric.

## Data And Predict Function Guardrails

- Prefer MLflow Evaluation Datasets for curated, reusable, or versioned benchmarks.
- Use `expected_response`, `expected_facts`, or other expectation fields intentionally and keep their semantics consistent across the dataset.
- Load expensive logged models once outside the `predict_fn`, then call them inside the wrapper so evaluation does not reload the model on every row.
- Keep output shape stable across rows. Do not mix incompatible return types inside one evaluation run.

## Automatic Evaluation Guardrails

- Use automatic evaluation for continuous quality monitoring of traced traffic, not as a replacement for curated offline regression tests.
- Automatic evaluation requires MLflow tracing to be enabled.
- Automatic evaluation of LLM judges requires an AI Gateway endpoint for judge execution.
- Automatic evaluation only supports LLM judges, not code-based scorers.
- For session-level automatic evaluation, ensure traces carry session IDs and understand that sessions are typically evaluated after a period of inactivity.
- Start with a higher sampling rate in development, then reduce sampling in production to control cost.
- Use filters to target high-value or high-risk traffic, for example production traces or successful traces only.
- Combine multiple judges to cover safety, hallucination risk, user experience, and task quality instead of relying on one judge.

## Databricks And Notebook Preferences

- In this workspace, keep evaluation code notebook-friendly and explicit. Put experiment setup, dataset definition, scorer configuration, and evaluation execution in clearly separated cells.
- Preserve `%pip install -U ...` plus `dbutils.library.restartPython()` when notebook dependencies need to change.
- When evaluation depends on Databricks-hosted endpoints, Unity Catalog models, or logged pyfunc models, call out those environment assumptions in the notebook.

## Avoid Deprecated Or Older Patterns

- Do not add new GenAI examples that rely on older `mlflow.evaluate(...)` APIs if the workflow is evaluating LLM, RAG, or agent behavior.
- Do not add new uses of deprecated `mlflow.transformers.generate_signature_output`; prefer `input_example` when logging transformer models.
- Do not hide evaluation criteria in implicit defaults. Always declare the scorers or judges that matter for the task.

## Minimal Quality Bar

- Every non-trivial GenAI evaluation should include at least one task-quality scorer and one safety or policy-oriented scorer.
- When comparing versions, keep the dataset fixed and compare runs in MLflow rather than changing both the system and the benchmark at the same time.
- If production monitoring is enabled, pair it with offline regression evaluation so quality regressions are caught before deployment as well as after deployment.