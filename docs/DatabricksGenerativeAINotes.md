# Notes of the AI Generative Engineer Exam for Databricks.
- **Perplexity** - How "surprised" a model is when generating the next word.
    - High Perplexity - worse predictions
    - Low Perplexity - better predictions
    - Used in Training a model or fine-tuning? (not used in RAG Systems)
    - “How many words the model thinks could come next.”

- **Rouge - Summarization**
    - How much of the reference text appears in the Generated Answer.
    - FOCUS: **RECALL**
    - Counts Overlapping N-Grams, Sequences.
    - Important content matters more then exact wording.

- **Blue - Translation**
    - How much of the Reference text matches in the generated answer.
    - FOCUS: **Precision**
    - Counts overlapping N-Grams with a penalty for short outputs.
    - Exact Phrase Matching matters more.

- **NDCG - Normal Discounted Cumulative Gain**
    - How well the retriever ranks documents for a query.
    - Order Matters, Relevant documents higher in the list are better.
    - NDCG rewards systems that place relevant documents higher
    - Compute Discounted Cumulative gain, Compute Ideal Ranking, Normalize
    - `Mlflow.evaluate()`, `mlflow.log_metric("ndcg@5", score)`
    - Many calculate this using Sklearn.  

- Precision - How many PREDICTED positives are correct TP/TP+FP
    - When False Positives are costly (FP)
    - If retrieving inaccurate responses, focus on precision.
- Recall - How many of ACTUAL positives were correct. TP/TP+FN
    - When Missing Positives are costly (FN)
- High Recall, Low Precision 
    - Catching most of the relevant docs + lots of irrelevant docs.
    - LLM Summarizer has to sort thru lots of irrelevant stuff.
    - Decrease Top K, Implement Re-ranker, Increase Similarity Score, Choose more robust embeddings.

- Register Model Signature - allows for proper inputs and outputs to be known and sent.

Model Types Available
Cost Considerations
- Low Request volume - use pay as go models

Share data from Production to Development.
- Create a development specific view of the Production data using the unity catalog.