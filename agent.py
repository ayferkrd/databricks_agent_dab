from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from databricks_openai import AsyncDatabricksOpenAI
import os

# Read the model service name injected by Databricks Apps
MODEL_SERVICE = os.getenv("MODEL_SERVICE")

# Point the OpenAI Agents SDK at Databricks instead of OpenAI
set_default_openai_client(AsyncDatabricksOpenAI(use_ai_gateway=True))
set_default_openai_api("responses")

# Define the agent
agent = Agent(
    name="Simple Chatbot",
    instructions="You are a helpful assistant. Answer the user's questions clearly and concisely.",
    model=MODEL_SERVICE,
)


async def run_agent(messages: list[dict]) -> str:
    """Run the agent with a list of messages and return the final reply."""
    result = await Runner.run(agent, messages)
    return result.final_output