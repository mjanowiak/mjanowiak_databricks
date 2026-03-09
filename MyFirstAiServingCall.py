# Databricks notebook source
# MAGIC %md
# MAGIC # AI Gateway Quickstart: databricks-llama-4-maverick
# MAGIC
# MAGIC This notebook demonstrates how to connect to and use your AI Gateway endpoint. AI Gateway is the enterprise control plane for governing LLM endpoints and coding agents, enabling you to analyze usage, configure permissions, and manage capacity across providers.
# MAGIC
# MAGIC **What you'll learn:**
# MAGIC * How to authenticate and connect to your AI Gateway endpoint
# MAGIC * Using the OpenAI-compatible Chat Completions API
# MAGIC * Next steps for production deployment

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC
# MAGIC Install the required Python packages to interact with your AI Gateway endpoint.

# COMMAND ----------

# MAGIC %pip install openai mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Configure your connection to the AI Gateway endpoint. The endpoint URL and model name are pre-configured for this endpoint.

# COMMAND ----------

import mlflow
mlflow.openai.autolog()

# AI Gateway endpoint configuration
DATABRICKS_TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
workspace_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().workspaceId().get()
print(workspace_id)
BASE_URL = f"https://{workspace_id}.cloud.databricks.com/"
# MODEL = "databricks-llama-4-maverick"
MODEL = "databricks-gpt-oss-120b"
print(f"Configured for AI Gateway endpoint: {MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chat Completions (OpenAI-Compatible)
# MAGIC
# MAGIC The chat completions API is the most common format for conversational AI. This example uses the OpenAI-compatible MLflow format, which works with most LLM providers.

# COMMAND ----------

from openai import OpenAI

client = OpenAI(
  api_key=DATABRICKS_TOKEN,
  base_url=f"{BASE_URL}/serving-endpoints"
)
mlflow.set_tags({"model": MODEL, "anything": "custom"})

response = client.chat.completions.create(
  model=MODEL,
  messages=[
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hello! How can I assist you today?"},
    {"role": "user", "content": "What is Databricks?"},
  ],
  max_tokens=256
)

print(response.choices[0].message.content)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Now that you've successfully connected to your AI Gateway endpoint, explore these enterprise features:
# MAGIC
# MAGIC ### Monitor Usage
# MAGIC * Query the **`system.ai_gateway.usage`** table to analyze request patterns, costs, and performance metrics
# MAGIC * View the built-in usage dashboard by clicking **View Dashboard** on the AI Gateway page
# MAGIC
# MAGIC ### Configure Governance
# MAGIC * Set **rate limits** to control usage and manage costs per user or application
# MAGIC * Configure **permissions** to control who can access specific endpoints
# MAGIC * Enable **inference tables** to log all requests and responses for audit and compliance
# MAGIC
# MAGIC ### Ensure Reliability
# MAGIC * Add **fallback models** to automatically route requests if the primary model is unavailable
# MAGIC
# MAGIC ### Learn More
# MAGIC Visit the [AI Gateway documentation](https://docs.databricks.com/aws/en/ai-gateway/overview-beta) for detailed configuration options and best practices.

# COMMAND ----------

df = spark.sql("SELECT * FROM system.ai_gateway.usage")
display(df)

# COMMAND ----------


