# Notes of the AI Generative Engineer Exam for Databricks.

## Perplexity
    - How "surprised" a model is when generating the next word.
    - High Perplexity - worse predictions
    - Low Perplexity - better predictions
    - Used in Training a model or fine-tuning? (not used in RAG Systems)
    - “How many words the model thinks could come next.”

## Rouge
    - Summarization**
    - How much of the reference text appears in the Generated Answer.
    - FOCUS: **RECALL**
    - Counts Overlapping N-Grams, Sequences.
    - Important content matters more then exact wording.

## Blue - Translation
    - How much of the Reference text matches in the generated answer.
    - FOCUS: **Precision**
    - Counts overlapping N-Grams with a penalty for short outputs.
    - Exact Phrase Matching matters more.

## NDCG - Normal Discounted Cumulative Gain
    - How well the retriever ranks documents for a query.
    - Order Matters, Relevant documents higher in the list are better.
    - NDCG rewards systems that place relevant documents higher
    - Compute Discounted Cumulative gain, Compute Ideal Ranking, Normalize
    - `Mlflow.evaluate()`, `mlflow.log_metric("ndcg@5", score)`
    - Many calculate this using Sklearn.  

## Precision
    - How many PREDICTED positives are correct TP/TP+FP
    - When False Positives are costly (FP)
    - If retrieving inaccurate responses, focus on precision.

## Recall
    - How many of ACTUAL positives were correct. TP/TP+FN
    - When Missing Positives are costly (FN)

## High Recall, Low Precision 
    - Catching most of the relevant docs + lots of irrelevant docs.
    - LLM Summarizer has to sort thru lots of irrelevant stuff.
    - Decrease Top K, Implement Re-ranker, Increase Similarity Score, Choose more robust embeddings.

## Model Registering Benefits
- Register Model Signature - allows for proper inputs and outputs to be known and sent.

## How to share data from Production to Development.
- Create a development specific view of the Production data using the unity catalog.

## Steps to Log Model using MLFlow
1. Train the Model
2. Log Model to MLFlow
3. configure metadata
4. register model with Unity Catalog

## Feature Serving
- Service in Databricks to provide on-demand and pre-materialized features for models not utilizing databricks model serving.

## Review these things.
- Vector Search Client, from databricks library. (Assembling and Deploying Applications)
    - Option 1 Delta Sync Index, 
    - Delta Source table -> Embedding Model -> vector index -> Endpoint
    - Option 2 Self Managed Embeddings (pre-calculated embeddings)
- Incomplete Output 
    - Decrease Chunk Size to enable LLM to process full chunks.
    - Add Segment Labels to help LLM find relevant content
    
- Model Types Available
    - Cost Considerations
    - Low Request volume - use pay as go models

## Chunking Strategies
- Fixed-size + overlap (Databricks default baseline)
    - Use LangChain `RecursiveCharacterTextSplitter` with chunk_size + chunk_overlap before indexing in Databricks Vector Search.
    - Best first pass for Delta Sync indexes and fast prototyping.
- Semantic chunking (quality-focused)
    - Split at topic/meaning boundaries, then embed with `DatabricksEmbeddings` and store in `DatabricksVectorSearch`.
    - Better precision when documents change topics often.
- Structure-aware chunking (doc-aware)
    - Chunk by headings/sections/tables first, then optionally sub-chunk with LangChain splitters.
    - Works well for policies, manuals, and notebook-exported docs.
- RAPTOR (advanced RAG)
    - Build hierarchical summaries (chunk -> section -> doc) for multi-hop reasoning.
    - Use for long corpora where important context is scattered.
- Practical Databricks tuning
    - Start around 300-800 tokens, 10-20% overlap, and tune using retrieval metrics (precision/recall/NDCG) in MLflow evaluation.

## Mosaic AI

## Agent Bricks

## MLFlow Evaluations Metrics and techniques

## Data Patterns for Agent Orchestration

## Cost Considerations for Agent Deployments

## Security Setup in unity catalog and for Agents Accessing Data
