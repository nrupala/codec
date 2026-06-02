import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from codec.config import Config
from codec.engine import CodeCEngine


app = FastAPI(title="CodeC Web UI")

static_dir = os.path.join(os.path.dirname(__file__), "static")
template_dir = os.path.join(os.path.dirname(__file__), "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=template_dir)

_engine: CodeCEngine | None = None


class ChatMessage(BaseModel):
    message: str


def get_engine() -> CodeCEngine:
    global _engine
    if _engine is None:
        config = Config()
        _engine = CodeCEngine(config)
    return _engine


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("terminal.html", {"request": request})


@app.post("/api/chat")
async def chat(msg: ChatMessage):
    try:
        engine = get_engine()
        response = await engine.process(msg.message)
        return JSONResponse({"response": response})
    except SystemExit:
        return JSONResponse({"response": "Goodbye!", "exit": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/status")
async def status():
    engine = get_engine()
    summary = engine.state_manager.get_summary()
    return JSONResponse(summary)


def run(host: str = "127.0.0.1", port: int = 8512):
    import uvicorn
    print(f"CodeC Web UI → http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    uvicorn.run(app, host=host, port=port, log_level="warning")
