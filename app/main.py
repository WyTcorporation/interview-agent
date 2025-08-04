from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from app.asr import transcribe_audio
from app.openai_agent import get_answer, session_messages
from app.config import get_openai_client
import json
from pathlib import Path
from pydantic import BaseModel
import subprocess

LOG_PATH = Path("history.json")
LOG_PATH.touch(exist_ok=True)

client = get_openai_client()

def append_log(question, answer, source="mic"):
    log = []
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text().strip() or "[]")
        except Exception:
            log = []
    log.append({
        "question": question,
        "answer": answer,
        "source": source
    })
    LOG_PATH.write_text(json.dumps(log[-100:], indent=2))  # зберігаємо останні 100

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


class TextRequest(BaseModel):
    text: str

@app.post("/ask/audio")
async def ask_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    question = transcribe_audio(client, audio_bytes)
    answer = get_answer(client, question)
    append_log(question, answer, source="mic")
    return JSONResponse({"question": question, "answer": answer})

@app.post("/ask/text")
async def ask_text(body: TextRequest):
    question = body.text.strip()
    answer = get_answer(client, question)
    append_log(question, answer, source="text")
    return JSONResponse({"question": question, "answer": answer})

# @app.post("/ask")
# async def ask_question(file: UploadFile = File(None), body: TextRequest = Body(None)):
#     if file:
#         audio_bytes = await file.read()
#         question = transcribe_audio(client, audio_bytes)
#         source = "mic"
#     elif body and body.text:
#         question = body.text.strip()
#         source = "text"
#     else:
#         return JSONResponse({"error": "No input provided"}, status_code=400)
#
#     answer = get_answer(client, question)
#     append_log(question, answer, source=source)
#     return JSONResponse({"question": question, "answer": answer})

@app.post("/reset")
async def reset_context():
    session_messages.clear()
    LOG_PATH.write_text("[]")
    return {"status": "reset"}

@app.get("/history")
async def get_history():
    if LOG_PATH.exists():
        try:
            content = LOG_PATH.read_text().strip()
            if content:
                return JSONResponse(content=json.loads(content))
        except Exception as e:
            print("Error reading history:", e)
    return JSONResponse(content=[])


import subprocess

listener_proc = None

@app.post("/listener/start")
async def start_listener():
    global listener_proc
    if listener_proc and listener_proc.poll() is None:
        return {"status": "already running"}
    listener_proc = subprocess.Popen(["python", "listener.py"])
    return {"status": "started"}

@app.post("/listener/stop")
async def stop_listener():
    global listener_proc
    if listener_proc and listener_proc.poll() is None:
        listener_proc.terminate()
        listener_proc = None
        return {"status": "stopped"}
    return {"status": "not running"}
