# Databricks notebook source
# MAGIC %md
# MAGIC # Quickstart: Build, test, and deploy an agent using Mosaic AI Agent Framework
# MAGIC This quickstart notebook demonstrates how to build, test, and deploy a generative AI agent ([AWS](https://docs.databricks.com/aws/en/generative-ai/guide/introduction-generative-ai-apps#what-are-gen-ai-apps) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/guide/introduction-generative-ai-apps#what-are-gen-ai-apps) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/guide/introduction-generative-ai-apps)) using Mosaic AI Agent Framework ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/build-genai-apps#-mosaic-ai-agent-framework) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/build-genai-apps#-mosaic-ai-agent-framework) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/build-genai-apps#-mosaic-ai-agent-framework)) on Databricks

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define and test an agent
# MAGIC This section defines and tests a simple agent with the following attributes:
# MAGIC
# MAGIC - The agent uses an LLM served on Databricks Foundation Model API ([AWS](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-model-apis/) | [GCP](https://docs.databricks.com/gcp/en/machine-learning/foundation-model-apis))
# MAGIC - The agent has access to a single tool, the built-in Python code interpreter tool on Databricks Unity Catalog. It can use this tool to run LLM-generated code in order to respond to user questions. ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/code-interpreter-tools#built-in-python-executor-tool) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/code-interpreter-tools) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/code-interpreter-tools))
# MAGIC
# MAGIC We will use `databricks_openai` SDK ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent#requirements) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent#requirements) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/author-agent#requirements)) to query the LLM endpoint.

# COMMAND ----------

# MAGIC %pip install -U -qqqq mlflow databricks-openai databricks-agents
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# WorkspaceClient is not imported in this cell, which causes a NameError.
# To fix, import WorkspaceClient from databricks.sdk.

from databricks.sdk import WorkspaceClient

# The snippet below tries to pick the first LLM API available in your Databricks workspace
# from a set of candidates. You can override and simplify it
# to just specify LLM_ENDPOINT_NAME.
import mlflow
# mlflow.openai.autolog()
WORKSPACE_ID = dbutils.notebook.entry_point.getDbutils().notebook().getContext().workspaceId().get()
print(workspace_id)
# AI Gateway endpoint configuration
DATABRICKS_TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
BASE_URL = "https://WORKSPACE_ID.cloud.databricks.com/"  # Replace with your non-sensitive placeholder
# MODEL = "databricks-llama-4-maverick"
MODEL = "databricks-gpt-oss-120b"
print(f"Configured for AI Gateway endpoint: {MODEL}")

LLM_ENDPOINT_NAME = f"{BASE_URL}/serving-endpoints"

from databricks_openai import DatabricksOpenAI
def is_endpoint_available(endpoint_name):
  try:
    client = DatabricksOpenAI()
    client.chat.completions.create(model=endpoint_name, messages=[{"role": "user", "content": "What is AI?"}])
    return True
  except Exception:
    return False
  
client = WorkspaceClient()
# for candidate_endpoint_name in ["databricks-gpt-oss-120b", "databricks-llama-4-maverick"]:
#     if is_endpoint_available(candidate_endpoint_name):
#       LLM_ENDPOINT_NAME = candidate_endpoint_name
# assert LLM_ENDPOINT_NAME is not None, "Please specify LLM_ENDPOINT_NAME"

# COMMAND ----------

# DBTITLE 1,Refresh UC function metadata (avoids "function not found" errors)
from databricks.sdk import WorkspaceClient

# Refresh Unity Catalog metadata for system.ai functions
# This ensures the python_exec tool is discoverable in your workspace
w = WorkspaceClient()
list(w.schemas.list("system"))
w.schemas.get("system.ai")
_ = list(w.functions.list(catalog_name="system", schema_name="ai"))

# COMMAND ----------

import json
import mlflow
from databricks_openai import UCFunctionToolkit, DatabricksFunctionClient, DatabricksOpenAI
# Import MLflow utilities for converting from chat completions to responses API format
from mlflow.types.responses import output_to_responses_items_stream, create_function_call_output_item

# Automatically log traces from LLM calls for ease of debugging
mlflow.openai.autolog()

# Get an OpenAI client configured to talk to Databricks model serving endpoints
# We'll use this to query an LLM in our agent
openai_client = DatabricksOpenAI()

# Load Databricks built-in tools (a stateless Python code interpreter tool)
client = DatabricksFunctionClient()
builtin_tools = UCFunctionToolkit(
    function_names=["system.ai.python_exec"], client=client
).tools
for tool in builtin_tools:
    del tool["function"]["strict"]


def call_tool(tool_name, parameters):
    if tool_name == "system__ai__python_exec":
        return DatabricksFunctionClient().execute_function(
            "system.ai.python_exec", parameters=parameters
        ).value
    raise ValueError(f"Unknown tool: {tool_name}")

def call_llm(prompt):
    for chunk in openai_client.chat.completions.create(
        model=LLM_ENDPOINT_NAME,
        messages=[{"role": "user", "content": prompt}],
        tools=builtin_tools,
        stream=True
    ):
        yield chunk.to_dict()

def run_agent(prompt):
    """
    Send a user prompt to the LLM, and yield LLM + tool call responses
    The LLM is allowed to call the code interpreter tool if needed, to respond to the user
    """
    # Convert output into Responses API-compatible events
    for chunk in output_to_responses_items_stream(call_llm(prompt)):
        yield chunk.model_dump(exclude_none=True)
    # If the model executed a tool, call it and yield the tool call output in Responses API format
    if chunk.item.get('type') == 'function_call':
        tool_name = chunk.item["name"]
        tool_args = json.loads(chunk.item["arguments"])
        tool_result = call_tool(tool_name, tool_args)
        yield {"type": "response.output_item.done", "item": create_function_call_output_item(call_id=chunk.item["call_id"], output=tool_result)}

# COMMAND ----------

for output_chunk in run_agent("What is the square root of 429?"):
    print(output_chunk)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare agent code for logging
# MAGIC
# MAGIC Wrap your agent definition in MLflow’s [ResponsesAgent interface](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html#mlflow.pyfunc.ResponsesAgent) to prepare your code for logging.
# MAGIC
# MAGIC By using MLflow’s standard agent authoring interface, you get built-in UIs for chatting with your agent and sharing it with others after deployment. ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent#-use-chatagent-to-author-agents) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/author-agent))

# COMMAND ----------

import uuid
import mlflow
from typing import Any, Optional, Generator

from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse, ResponsesAgentStreamEvent, output_to_responses_items_stream

mlflow.openai.autolog()

class QuickstartAgent(ResponsesAgent):
    def predict_stream(self, request: ResponsesAgentRequest): 
        # Extract the user's prompt from the request
        prompt = request.input[-1].content
        # Stream response items from our agent
        for chunk in run_agent(prompt):
            yield ResponsesAgentStreamEvent(**chunk)

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        outputs = [
            event.item
            for event in self.predict_stream(request)
            if event.type == "response.output_item.done"
        ]
        return ResponsesAgentResponse(output=outputs)


# COMMAND ----------

from mlflow.types.responses import ResponsesAgentRequest

AGENT = QuickstartAgent()

# Create a proper ResponsesAgentRequest with input field
request = ResponsesAgentRequest(
    input=[
            {
                "role": "user", 
                "content": "What's the square root of 429?"
            }
    ]
)

for event in AGENT.predict_stream(request):
    print(event)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Log the agent
# MAGIC
# MAGIC Log the agent and register it to Unity Catalog as a model ([AWS](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/manage-model-lifecycle/) | [GCP](https://docs.databricks.com/gcp/en/machine-learning/manage-model-lifecycle/)). This step packages the agent code and its dependencies into a single artifact to deploy it to a serving endpoint.
# MAGIC
# MAGIC The following code cells do the following:
# MAGIC
# MAGIC 1. Copy the agent code from above and combine it into a single cell.
# MAGIC 1. Add the `%%writefile` cell magic command at the top of the cell to save the agent code to a file called `quickstart_agent.py`.
# MAGIC 1. Add a [mlflow.models.set_model()](https://mlflow.org/docs/latest/model#models-from-code) call to the bottom of the cell. This tells MLflow which Python agent object to use for making predictions when your agent is deployed.
# MAGIC 1. Log the agent code in the `quickstart_agent.py` file using MLflow APIs ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/log-agent) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/log-agent)).

# COMMAND ----------

# MAGIC %%writefile quickstart_agent.py
# MAGIC
# MAGIC import json
# MAGIC import uuid
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks_openai import UCFunctionToolkit, DatabricksFunctionClient, DatabricksOpenAI
# MAGIC from typing import Any, Optional, Generator
# MAGIC
# MAGIC import mlflow
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentStreamEvent, ResponsesAgentResponse, output_to_responses_items_stream, create_function_call_output_item
# MAGIC
# MAGIC
# MAGIC # Get an OpenAI client configured to talk to Databricks model serving endpoints
# MAGIC # We'll use this to query an LLM in our agent
# MAGIC openai_client = DatabricksOpenAI()
# MAGIC
# MAGIC # The snippet below tries to pick the first LLM API available in your Databricks workspace
# MAGIC # from a set of candidates. You can override and simplify it
# MAGIC # to just specify LLM_ENDPOINT_NAME.
# MAGIC LLM_ENDPOINT_NAME = None
# MAGIC
# MAGIC def is_endpoint_available(endpoint_name):
# MAGIC   try:
# MAGIC     client = DatabricksOpenAI()
# MAGIC     client.chat.completions.create(model=endpoint_name, messages=[{"role": "user", "content": "What is AI?"}])
# MAGIC     return True
# MAGIC   except Exception:
# MAGIC     return False
# MAGIC
# MAGIC client = WorkspaceClient()
# MAGIC for candidate_endpoint_name in ["databricks-claude-3-7-sonnet", "databricks-meta-llama-3-3-70b-instruct"]:
# MAGIC     if is_endpoint_available(candidate_endpoint_name):
# MAGIC       LLM_ENDPOINT_NAME = candidate_endpoint_name
# MAGIC assert LLM_ENDPOINT_NAME is not None, "Please specify LLM_ENDPOINT_NAME"
# MAGIC
# MAGIC # Automatically log traces from LLM calls for ease of debugging
# MAGIC mlflow.openai.autolog()
# MAGIC
# MAGIC # Get an OpenAI client configured to talk to Databricks model serving endpoints
# MAGIC # We'll use this to query an LLM in our agent
# MAGIC openai_client = DatabricksOpenAI()
# MAGIC
# MAGIC # Load Databricks built-in tools (a stateless Python code interpreter tool)
# MAGIC client = DatabricksFunctionClient()
# MAGIC builtin_tools = UCFunctionToolkit(
# MAGIC     function_names=["system.ai.python_exec"], client=client
# MAGIC ).tools
# MAGIC for tool in builtin_tools:
# MAGIC     del tool["function"]["strict"]
# MAGIC
# MAGIC
# MAGIC def call_tool(tool_name, parameters):
# MAGIC     if tool_name == "system__ai__python_exec":
# MAGIC         return DatabricksFunctionClient().execute_function(
# MAGIC             "system.ai.python_exec", parameters=parameters
# MAGIC         ).value
# MAGIC     raise ValueError(f"Unknown tool: {tool_name}")
# MAGIC
# MAGIC def call_llm(prompt):
# MAGIC     for chunk in openai_client.chat.completions.create(
# MAGIC         model=LLM_ENDPOINT_NAME,
# MAGIC         messages=[{"role": "user", "content": prompt}],
# MAGIC         tools=builtin_tools,
# MAGIC         stream=True
# MAGIC     ):
# MAGIC         yield chunk.to_dict()
# MAGIC
# MAGIC
# MAGIC def run_agent(prompt):
# MAGIC     """
# MAGIC     Send a user prompt to the LLM, and yield LLM + tool call responses
# MAGIC     The LLM is allowed to call the code interpreter tool if needed, to respond to the user
# MAGIC     """
# MAGIC     # Convert output into Responses API-compatible events
# MAGIC     for chunk in output_to_responses_items_stream(call_llm(prompt)):
# MAGIC         yield chunk.model_dump(exclude_none=True)
# MAGIC     # If the model executed a tool, call it and yield the tool call output in Responses API format
# MAGIC     if chunk.item.get('type') == 'function_call':
# MAGIC         tool_name = chunk.item["name"]
# MAGIC         tool_args = json.loads(chunk.item["arguments"])
# MAGIC         tool_result = call_tool(tool_name, tool_args)
# MAGIC         yield {"type": "response.output_item.done", "item": create_function_call_output_item(call_id=chunk.item["call_id"], output=tool_result)}
# MAGIC
# MAGIC
# MAGIC class QuickstartAgent(ResponsesAgent):
# MAGIC     def predict_stream(self, request: ResponsesAgentRequest): 
# MAGIC         # Extract the user's prompt from the request
# MAGIC         prompt = request.input[-1].content
# MAGIC         # Stream response items from our agent
# MAGIC         for chunk in run_agent(prompt):
# MAGIC             yield ResponsesAgentStreamEvent(**chunk)
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         outputs = [
# MAGIC             event.item
# MAGIC             for event in self.predict_stream(request)
# MAGIC             if event.type == "response.output_item.done"
# MAGIC         ]
# MAGIC         return ResponsesAgentResponse(output=outputs)
# MAGIC
# MAGIC AGENT = QuickstartAgent()
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Test ResponsesAgent
# Test the ResponsesAgent implementation
from quickstart_agent import QuickstartAgent, LLM_ENDPOINT_NAME
from mlflow.types.responses import ResponsesAgentRequest

print(f"Using LLM endpoint: {LLM_ENDPOINT_NAME}")

# Create agent instance
agent = QuickstartAgent()

# Create test request - input should be a list of messages
request = ResponsesAgentRequest(
    input=[
        {
            "role": "user", 
            "content": "What's the square root of 144?"
        }
    ]
)

# Test the agent
print("\nTesting agent...")
response = agent.predict(request)
print(f"\nAgent response:")
for i, output_item in enumerate(response.output):
    print(f"Item {i+1}: Type={output_item.type}")
    print(f" {output_item}")


# COMMAND ----------

import mlflow
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from pkg_resources import get_distribution
from quickstart_agent import LLM_ENDPOINT_NAME

# Register the model to the workspace default catalog.
# Specify a catalog (e.g. "main") and schema name (e.g. "custom_schema") if needed,
# in order to register the agent to a different location
default_catalog_name = spark.sql("SELECT current_catalog()").collect()[0][0]
catalog_name = default_catalog_name if default_catalog_name != "hive_metastore" else "main"
schema_name = "default"
registered_model_name = f"{catalog_name}.{schema_name}.quickstart_agent"

# Specify Databricks product resources that the agent needs access to (our builtin python
# code interpreter tool and LLM serving endpoint), so that Databricks can automatically
# configure authentication for the agent to access these resources when it's deployed.
resources = [
    DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT_NAME),
    DatabricksFunction(function_name="system.ai.python_exec"),
]

mlflow.set_registry_uri("databricks-uc")
with mlflow.start_run():
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="quickstart_agent.py",
        extra_pip_requirements=[
            f"databricks-connect=={get_distribution('databricks-connect').version}"
        ],
        resources=resources,
        registered_model_name=registered_model_name,
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy the agent
# MAGIC
# MAGIC Run the cell below to deploy the agent ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-framework/deploy-agent) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/deploy-agent) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-framework/deploy-agent)). Once the agent endpoint starts, you can chat with it via AI Playground ([AWS](https://docs.databricks.com/aws/en/large-language-models/ai-playground) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/large-language-models/ai-playground) | [GCP](https://docs.databricks.com/gcp/en/large-language-models/ai-playground)), or share it with stakeholders ([AWS](https://docs.databricks.com/aws/en/generative-ai/agent-evaluation/review-app) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-evaluation/review-app) | [GCP](https://docs.databricks.com/gcp/en/generative-ai/agent-evaluation/review-app)) for initial feedback, before sharing it more broadly.

# COMMAND ----------

from databricks import agents

deployment_info = agents.deploy(
    model_name=registered_model_name,
    model_version=logged_agent_info.registered_model_version,
    scale_to_zero=True,
    deploy_feedback_model=False
)
