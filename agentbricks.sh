#!/bin/sh


# Install the Agent Bricks CLI
pip install databricks-agentbricks

# Authenticate with OAuth and set the profile as the CLI's default
databricks auth login --host https://&lt;your-workspace-url&gt; --profile &lt;profile&gt;
agentbricks login --profile &lt;profile&gt;

# 1. Scaffold a project (templates: langgraph or openai)
agentbricks init --framework langgraph my-agent
cd my-agent

# 2. Run locally at http://localhost:8000
agentbricks dev

# 3. Deploy to the Databricks agent runtime
agentbricks deploy my-agent