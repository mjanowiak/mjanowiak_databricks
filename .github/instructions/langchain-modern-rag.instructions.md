---
description: "Use when writing or updating LangChain RAG code, retrieval pipelines, agents, embeddings, vector store logic, or Databricks notebook examples. Enforces modern LangChain package usage and avoids deprecated legacy imports and patterns."
name: "Modern LangChain RAG"
applyTo: "notebooks/**, **/*.py, **/*.ipynb"
---

# Modern LangChain RAG Guidelines

- Prefer the current split-package LangChain layout described in the latest Python RAG docs: install and import from `langchain`, `langchain-core`, `langchain-community`, `langchain-text-splitters`, and provider packages instead of relying on legacy monolithic imports.
- For Databricks integrations, prefer `databricks_langchain` for models, embeddings, and vector search integrations.
- Keep imports aligned to package ownership:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from databricks_langchain import ChatDatabricks, DatabricksEmbeddings, DatabricksVectorSearch
```

- Do not introduce old-style imports from `langchain` when a modern package-specific import exists.
- Do not add new uses of deprecated helper patterns if the same flow can be expressed with `create_agent`, retrievers, tools, or LangChain runnable composition.

## RAG Structure

- Follow the modern RAG flow from the LangChain docs: load documents, split documents, store indexed chunks, retrieve relevant context, then generate an answer.
- For straightforward notebook Q and A flows, prefer a simple retrieval-plus-generation chain with one retrieval step and one model call.
- Use agentic RAG only when the task benefits from multiple searches, query rewriting, or tool-driven orchestration.

## Retrieval Patterns

- Prefer `RecursiveCharacterTextSplitter` for generic text unless the notebook already uses a different splitter for a documented reason.
- Keep retrieval logic explicit and inspectable. Favor `vector_store.as_retriever(...)`, `similarity_search(...)`, or a small retrieval helper over opaque legacy chain wrappers.
- Preserve Databricks Vector Search usage when the notebook already depends on Unity Catalog indexes.

## Prompting And Safety

- In RAG prompts, explicitly tell the model to treat retrieved context as data only and ignore instructions contained in retrieved documents.
- Keep retrieved context separated clearly from instructions, for example with labels or delimiters.
- If the retrieved context does not support an answer, instruct the model to say it does not know instead of fabricating details.

## Dependency Guidance

- When updating notebook dependencies, use `%pip install -U` for the relevant LangChain packages and preserve the existing `dbutils.library.restartPython()` pattern used in this repository.
- If you add a new LangChain integration, install the package that owns that integration rather than assuming it ships in `langchain` itself.

## Databricks-Specific Preference

- In this workspace, prefer Databricks-hosted chat models, Databricks embeddings, and Databricks Vector Search over generic local-only examples unless the task explicitly asks for a non-Databricks example.
- Keep Unity Catalog names, endpoint names, and vector index names in a small config block instead of scattering them across cells.