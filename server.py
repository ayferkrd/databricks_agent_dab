import os
import uvicorn
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent import run_agent

app = FastAPI()

CHAT_UI = Path(__file__).parent / "chat.html"


class ChatRequest(BaseModel):
    input: list[dict]


@app.get("/", response_class=HTMLResponse)
async def root():
    return CHAT_UI.read_text()


@app.post("/invocations")
async def invocations(request: ChatRequest):
    reply = await run_agent(request.input)
    return {"output": reply}


def main():
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", 8000)))


if __name__ == "__main__":
    main()