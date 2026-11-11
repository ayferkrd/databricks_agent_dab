from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from agents.tracing import set_trace_processors
from databricks.sdk import WorkspaceClient
from databricks_openai import AsyncDatabricksOpenAI
from databricks_openai.agents import McpServer
import mlflow
import os

# Point the OpenAI Agents SDK at Databricks
set_default_openai_client(AsyncDatabricksOpenAI(use_ai_gateway=True))
set_default_openai_api("responses")

# Send traces to MLflow instead of OpenAI
set_trace_processors([])
mlflow.set_tracking_uri("databricks")
mlflow.openai.autolog()

# Read environment variables injected by the DAB
MODEL_SERVICE = os.getenv("MODEL_SERVICE")
mlflow.set_experiment(experiment_id=os.getenv("MLFLOW_EXPERIMENT_ID"))

# MCP configuration: the table's full name comes from its app resource
LISTINGS_TABLE = os.getenv("LISTINGS_TABLE")

ws = WorkspaceClient()

# The Databricks-provided SQL MCP, reached through Unity Gateway
DBSQL_URL = f"{ws.config.host}/ai-gateway/mcp-services/system.ai.dbsql"

INSTRUCTIONS = (
    "You are a helpful assistant. Answer the user's questions clearly and concisely. "
    f"For questions about San Francisco Airbnb listings, query {LISTINGS_TABLE} with the execute_sql tool."
)


@mlflow.trace(name="tool_calling_chatbot_run", span_type="AGENT")
async def run_agent(messages: list[dict]) -> str:
    """Run the agent with MCP tools and return the final reply."""
    mlflow.update_current_trace(tags={"agent_name": "Tool-calling Chatbot", "model_service": MODEL_SERVICE})
    # Connect to the MCP for this request; leaving the block closes the connection
    async with McpServer(url=DBSQL_URL, workspace_client=ws, name="dbsql", timeout=60.0) as mcp_server:
        # Define the agent with MCP tool access
        agent = Agent(
            name="Simple Chatbot",
            instructions=INSTRUCTIONS,
            model=MODEL_SERVICE,
            mcp_servers=[mcp_server],
        )
        result = await Runner.run(agent, messages)
    return result.final_output