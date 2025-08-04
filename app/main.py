from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from app.asr import transcribe_audio
from app.openai_agent import get_answer
from openai import OpenAI
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

LOG_PATH = Path("history.json")
LOG_PATH.touch(exist_ok=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def append_log(question, answer):
    log = []
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text().strip() or "[]")
        except Exception:
            log = []
    log.append({"question": question, "answer": answer})
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

@app.post("/ask")
async def ask_question(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    question = transcribe_audio(client, audio_bytes)
    answer = get_answer(client, question)
    append_log(question, answer)
    return JSONResponse({"question": question, "answer": answer})

@app.post("/reset")
async def reset_context():
    from app.openai_agent import session_messages
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