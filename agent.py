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
    "You are a travel assistant. Use the provided weather data and average nightly fee for the location in your response. Answer the user's questions clearly and concisely. "
    f"For questions about San Francisco Airbnb listings, query {LISTINGS_TABLE} with the execute_sql tool."
)


@mlflow.trace(span_type="TOOL")
def lookup_weather(city: str) -> dict:
    """Simulated weather tool for demonstration."""
    weather_data = {
        "tokyo": {"temp_f": 72, "condition": "partly cloudy", "humidity": 65},
        "london": {"temp_f": 58, "condition": "rainy", "humidity": 80},
        "new york": {"temp_f": 68, "condition": "sunny", "humidity": 45},
    }
    return weather_data.get(city.lower(), {"temp_f": 0, "condition": "unknown", "humidity": 0})



@mlflow.trace(name="tool_calling_chatbot_run", span_type="AGENT")
async def run_agent(messages: list[dict], session_id: str | None = None, user_id: str | None = None) -> str:
    """Run the agent with MCP tools and return the final reply."""
    # Session/user go on the trace for grouping in the Sessions view
    trace_context = {}
    if session_id:
        trace_context["session_id"] = session_id
    if user_id:
        trace_context["user"] = user_id
    mlflow.update_current_trace(
        tags={"agent_name": "Tool-calling Chatbot", "model_service": MODEL_SERVICE},
        **trace_context,
    )

    # Per-request details stay as span attributes
    span = mlflow.get_current_active_span()
    span.set_attributes({
        "app_version": "1.2.0",
        "request_source": "web_ui"
    })

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