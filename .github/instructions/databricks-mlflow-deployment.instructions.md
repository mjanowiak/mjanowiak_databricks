---
description: "Use when writing or updating Databricks MLflow code for Unity Catalog model registration, model aliases, deployment jobs, batch inference, or serving endpoints. Enforces Databricks-specific MLflow 3 and Mosaic AI deployment patterns."
name: "Databricks MLflow Deployment"
applyTo: "notebooks/**, **/*.py, **/*.ipynb"
---

# Databricks MLflow Deployment Guidelines

- Prefer Databricks-managed MLflow with Unity Catalog for governed model lifecycle work.
- Treat Unity Catalog as the default registry for new Databricks MLflow model workflows.
- Prefer Databricks-native deployment patterns over generic standalone MLflow deployment examples.

## Unity Catalog Model Registration

- Use full three-level Unity Catalog names for registered models: `catalog.schema.model_name`.
- Prefer `mlflow.set_registry_uri("databricks-uc")` in notebooks when registration behavior must be explicit, even though MLflow 3 commonly defaults to Unity Catalog.
- Register models directly from `log_model(..., registered_model_name=...)` or with `mlflow.register_model(...)` using a Unity Catalog model name.
- New Unity Catalog model versions must include a model signature. Prefer `input_example` so the signature is inferred automatically.
- When training from Unity Catalog tables, log inputs with `mlflow.log_input(...)` to preserve lineage on the registered model version.

```python
import mlflow

mlflow.set_registry_uri("databricks-uc")

with mlflow.start_run():
    mlflow.sklearn.log_model(
        sk_model=model,
        name="model",
        input_example=input_example,
        registered_model_name="main.default.my_model",
    )
```

## Unity Catalog Permissions And Guardrails

- Assume Unity Catalog is required unless the task explicitly targets the legacy workspace model registry.
- Call out permission prerequisites when relevant: `USE CATALOG`, `USE SCHEMA`, and `CREATE MODEL` to create new registered models.
- For new versions under an existing model, account for ownership and model-version creation permissions.
- If Unity Catalog registration fails with authorization issues, note the Databricks-documented fallback environment variable `MLFLOW_USE_DATABRICKS_SDK_MODEL_ARTIFACTS_REPO_FOR_UC=True`.
- Model access control in Unity Catalog is governed as a function-like securable. Do not describe old workspace registry ACL behavior as if it applies to Unity Catalog.

## Aliases Instead Of Stages

- Do not introduce model stages for Unity Catalog workflows. Unity Catalog uses aliases, not stages, for deployment selection.
- Use aliases such as `Champion`, `Candidate`, or environment-specific names to decouple deployment targets from specific version numbers.
- For batch and serving workloads, prefer alias-based model URIs so workloads pick up approved versions without code changes.

```python
from mlflow import MlflowClient

client = MlflowClient()
client.set_registered_model_alias("main.default.my_model", "Champion", 3)
```

## Promotion Across Environments

- Prefer pipelines-as-code that train and register directly in the target environment when feasible.
- If promotion without retraining is required, use `copy_model_version(...)` across Unity Catalog models instead of ad hoc artifact copying.
- Keep environment boundaries explicit in catalog and schema names such as `dev`, `staging`, and `prod`.
- After promotion, use aliases to identify the deployable version in the destination environment.

## Serving Endpoints

- For real-time inference on Databricks, prefer Mosaic AI Model Serving backed by a registered model in Unity Catalog.
- Keep endpoint configuration externalized in a small config block or variables instead of scattering endpoint names across notebook cells.
- When serving agent-like or dependent models, declare required Databricks resources explicitly when logging the model so authentication can be configured correctly.
- Prefer updating endpoints to a version resolved from a Unity Catalog alias rather than hard-coding version numbers into endpoint logic.
- Call out serverless and workspace entitlement prerequisites when a notebook assumes endpoint creation or querying is available.

## Deployment Jobs

- For governed deployment workflows, prefer MLflow 3 deployment jobs attached to Unity Catalog models.
- Databricks recommends creating deployment jobs programmatically from notebooks using the Databricks SDK so the workflow is code-defined and reproducible.
- Model deployment jobs should use job-level parameters named `model_name` and `model_version`.
- Prefer a simple baseline workflow of evaluation, approval, and deployment, then extend it only if staged rollout or rollback logic is truly needed.
- Keep max concurrent runs at 1 unless there is a strong reason to accept deployment race conditions.
- For approval tasks, note that Databricks recommends disabling retries because the first run is expected to pause or fail pending approval.
- Connect deployment jobs to Unity Catalog models with the MLflow client rather than relying on manual-only setup when writing infrastructure notebooks.

## Deployment Job Security Guardrails

- Treat deployment jobs as privileged automation. Databricks documents that auto-triggered deployment jobs run using the model owner's credentials.
- Prefer configuring the deployment job to run as a minimally privileged service principal, not as a broad human owner account.
- Be explicit that granting model-version creation rights on a connected model can indirectly allow execution of deployment job code.
- If approval is part of the workflow, use Unity Catalog tags and, when needed, governed tag policies for separated approval responsibilities.

## Batch Inference

- Distinguish batch inference from real-time serving. Do not default to serving endpoints when a Spark or SQL batch workflow is the better fit.
- For batch scoring over Spark data, prefer `mlflow.pyfunc.spark_udf(...)` or Databricks AI Functions, depending on the model type and workflow.
- For custom MLflow models in this repository, preserve the existing `spark_udf` pattern when extending notebook examples unless the task explicitly requests AI Functions.
- For batch jobs that should follow production rollouts automatically, use alias-based model URIs such as `models:/catalog.schema.model@Champion`.
- Keep batch outputs in governed Databricks objects such as Unity Catalog tables when the notebook is part of a production-oriented workflow.

## Databricks Notebook Preferences

- Keep registration, alias management, deployment, and batch inference logic in separate notebook cells or sections.
- Preserve `%pip install ...` plus `dbutils.library.restartPython()` when changing notebook dependencies.
- Keep catalog, schema, model name, endpoint name, and output table name in a small config block near the top of the workflow.
- Call out environment assumptions clearly when code depends on Databricks Model Serving, specific serving endpoints, Unity Catalog privileges, or existing Lakeflow Jobs.

## Avoid Older Or Less Appropriate Patterns

- Do not create new Databricks examples that rely on workspace model registry unless the task explicitly targets legacy behavior.
- Do not describe Unity Catalog deployment using stages such as `Production` or `Staging`; use aliases instead.
- Do not hard-code model version numbers into recurring batch or serving workflows when aliases provide a safer deployment boundary.
- Do not mix serving-endpoint deployment guidance with offline batch-scoring guidance as if they are interchangeable.