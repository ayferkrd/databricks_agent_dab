import os
import uvicorn
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from databricks.sdk import WorkspaceClient

from agent import run_agent

app = FastAPI()

CHAT_UI = Path(__file__).parent / "chat.html"


class ChatRequest(BaseModel):
    input: list[dict]
    # Optional production context: groups traces by conversation and caller
    session_id: str | None = None
    user_id: str | None = None


def get_forwarded_user_id(http_request: Request) -> str | None:
    """Resolve the caller's identity from the user-authorization forwarded token.

    Databricks Apps forwards the signed-in user's token in the
    x-forwarded-access-token header when user authorization is enabled
    (user_api_scopes in databricks.yml).
    """
    token = http_request.headers.get("x-forwarded-access-token")
    if not token:
        return None
    try:
        user_ws = WorkspaceClient(host=os.getenv("DATABRICKS_HOST"), token=token)
        return user_ws.current_user.me().user_name
    except Exception:
        return None  # keep the chat working if identity resolution fails


@app.get("/", response_class=HTMLResponse)
async def root():
    return CHAT_UI.read_text()


@app.post("/invocations")
async def invocations(request: ChatRequest, http_request: Request):
    # Real caller identity wins; fall back to the optional request field
    user_id = request.user_id or get_forwarded_user_id(http_request)
    reply = await run_agent(
        request.input, session_id=request.session_id, user_id=user_id
    )
    return {"output": reply}


def main():
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", 8000)))


if __name__ == "__main__":
    main()