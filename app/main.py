import sys
from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from app.asr import transcribe_audio
from app.openai_agent import get_answer, session_messages, get_answer_with_image, capture_screenshot_b64
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


listener_proc = None
LISTENER_PATH = str(Path("windows/listener.py").resolve())

@app.post("/listener/start")
async def start_listener():
    global listener_proc
    if listener_proc and listener_proc.poll() is None:
        return {"status": "already running"}
    listener_proc = subprocess.Popen([sys.executable, LISTENER_PATH])
    return {"status": "started"}

@app.post("/listener/stop")
async def stop_listener():
    global listener_proc
    if listener_proc and listener_proc.poll() is None:
        listener_proc.terminate()
        listener_proc = None
        return {"status": "stopped"}
    return {"status": "not running"}

class ScreenRequest(BaseModel):
    prompt: str

SCREEN_PATH = str(Path("windows/screen.py").resolve())

@app.post("/screen/run")
async def run_screen_tool():
    subprocess.Popen([sys.executable, SCREEN_PATH])
    return {"status": "started"}

class ScreenImageRequest(BaseModel):
    image_b64: str
    prompt: str

@app.post("/screen/analyze")
async def screen_analyze(req: ScreenImageRequest):
    answer = get_answer_with_image(client, req.prompt, req.image_b64)
    append_log(req.prompt, answer, source="screen")
    return {"question": req.prompt, "answer": answer}

@app.post("/mode")
async def set_mode(mode: str = Body(...)):
    global current_mode_prompt

    MODES = {
        "short": "Коротко, впевнено, як досвідчений інженер.",
        "code": "Дай коротку відповідь і приклад з коду (якщо доречно).",
        "hr": "Відповідай простими словами, зрозуміло навіть HR.",
        "long": "Відповідай розгорнуто, з прикладами і поясненням."
    }

    if mode in MODES:
        current_mode_prompt = MODES[mode]
        return {"status": "ok", "mode": mode}
    else:
        return JSONResponse(status_code=400, content={"error": "Невідомий режим"})


MIC_LISTENER_PATH = str(Path("windows/mic_listener.py").resolve())
mic_listener_proc = None

@app.post("/mic/start")
async def start_mic_listener():
    global mic_listener_proc
    if mic_listener_proc and mic_listener_proc.poll() is None:
        return {"status": "already running"}
    mic_listener_proc = subprocess.Popen([sys.executable, MIC_LISTENER_PATH])
    return {"status": "started"}

@app.post("/mic/stop")
async def stop_mic_listener():
    global mic_listener_proc
    if mic_listener_proc and mic_listener_proc.poll() is None:
        mic_listener_proc.terminate()
        mic_listener_proc = None
        return {"status": "stopped"}
    return {"status": "not running"}
