# Project Guidelines

## Architecture
- This workspace is a Databricks-focused learning repository built around notebooks, dashboards, and supporting assets rather than a conventional Python package.
- Treat `notebooks/Studebaker_RAG_LLM.ipynb` as the primary end-to-end RAG example. Related notebooks cover indexing, vector search, model serving, deployment, and agent examples.
- Expect Databricks-specific runtime dependencies such as `spark`, `dbutils`, Unity Catalog objects, Databricks model serving endpoints, Vector Search indexes, and Volumes paths.

## Code Style
- Preserve Databricks notebook structure. When editing `.py` notebooks, keep `# COMMAND ----------` cell markers and do not convert them to standard script section markers.
- Keep notebook changes localized and readable. Prefer small, self-contained cells with explicit configuration near the top of the notebook or section.
- Follow the existing Databricks and LangChain import style already used in the repo, especially `databricks_langchain`, `langchain_core`, MLflow, and Databricks SDK libraries.
- When adding configuration, prefer clearly named constants or a small config block for catalog, schema, endpoint, vector index, and volume paths instead of scattering literals across cells.

## Build And Test
- There is no conventional local build or test pipeline in this repository.
- Validation is primarily notebook execution inside Databricks, plus MLflow-based evaluation against the ground-truth text files in `notebooks/`.
- The workspace includes a Databricks Asset Bundle config in `databricks.yml`. Prefer changes that remain compatible with bundle-based Databricks workflows.
- Many notebooks install dependencies inline with `%pip` and then call `dbutils.library.restartPython()`. Preserve that pattern when updating notebook dependencies.

## Conventions
- Assume code runs in Databricks unless the file clearly targets another environment. Do not replace Databricks APIs with generic local-only alternatives unless the task explicitly asks for portability.
- Use fully qualified Unity Catalog names for registered models, tables, volumes, and indexes when practical: `catalog.schema.object_name`.
- For model registration work, use MLflow with `mlflow.set_registry_uri("databricks-uc")` and Unity Catalog model names.
- For retrieval and RAG code, preserve the existing pattern of Databricks-hosted chat models, Databricks Vector Search, and MLflow evaluation.
- Keep sample data, ground-truth outputs, and notebook assumptions in sync. If a notebook change affects evaluation inputs or expected outputs, update the related reference files.
- Avoid introducing abstractions that fight the notebook-first structure unless the task clearly benefits from extracting reusable code.

## Agent Guidance
- Before making broad changes, inspect nearby notebook cells for execution-order dependencies and shared variables.
- Call out environment assumptions clearly when a change depends on existing Databricks endpoints, Unity Catalog permissions, or workspace resources that may not exist outside the authoring environment.
- Prefer concise, practical edits over framework-heavy refactors. This repository is primarily instructional and example-driven.