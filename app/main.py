import os
import sys
from dbm import sqlite3

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
from db.db_start import init_db, log_to_db, DB_PATH
from windows.diarization import save_temp_wav, extract_questions_from_diarization

init_db()

LOG_PATH = Path("history.json")
LOG_PATH.touch(exist_ok=True)

client = get_openai_client()

MODE_PROMPT = "short"

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

@app.post("/ask/file")
async def ask_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    question = transcribe_audio(client, audio_bytes)
    answer = get_answer(client, question)
    append_log(question, answer, source="mic")
    log_to_db(question, answer, source="mic", model="gpt-4o", mode=MODE_PROMPT)
    return JSONResponse({"question": question, "answer": answer})

@app.post("/ask/audio")
async def ask_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    question = transcribe_audio(client, audio_bytes)
    answer = get_answer(client, question)
    append_log(question, answer, source="mic")
    log_to_db(question, answer, source="mic", model="gpt-4o", mode=MODE_PROMPT)
    return JSONResponse({"question": question, "answer": answer})

class TextRequest(BaseModel):
    text: str

@app.post("/ask/text")
async def ask_text(body: TextRequest):
    question = body.text.strip()
    answer = get_answer(client, question)
    append_log(question, answer, source="text")
    log_to_db(question, answer, source="text", model="gpt-4o", mode=MODE_PROMPT)
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

SCREEN_PATH = str(Path("windows/screen_headless.py").resolve())

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
    log_to_db(req.prompt, answer, source="screen", model="gpt-4o", mode=MODE_PROMPT)
    return {"question": req.prompt, "answer": answer}

PROMPTS_PATH = Path("app/prompts.json")

def load_prompts():
    try:
        return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print("❌ Помилка при завантаженні prompts.json:", e)
        return {}
@app.post("/mode")
async def set_mode(mode: str = Body(...)):
    global MODE_PROMPT
    MODE_PROMPT = mode
    global current_mode_prompt
    prompts = load_prompts()
    if mode in prompts:
        current_mode_prompt = prompts[mode]
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

OVERLAY_PATH = str(Path("windows/overlay.py").resolve())
@app.post("/overlay", response_class=HTMLResponse)
async def start_overlay():
    subprocess.Popen([sys.executable, OVERLAY_PATH])
    return {"status": "started"}

OVERLAY_LISTENER_PATH = str(Path("windows/overlay_listener.py").resolve())

@app.post("/overlay/listener")
async def start_overlay_listener():
    subprocess.Popen([sys.executable, OVERLAY_LISTENER_PATH])
    return {"status": "started"}

@app.get("/latest")
async def get_latest():
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text().strip() or "[]")
            if log:
                return {"question": log[-1]["question"], "answer": log[-1]["answer"]}
        except Exception:
            pass
    return {"question": "", "answer": "❌ Немає відповіді"}


@app.get("/analytics/questions_per_day")
def questions_per_day():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute('''
            SELECT DATE(timestamp) as day, COUNT(*) 
            FROM history 
            GROUP BY day 
            ORDER BY day DESC
        ''').fetchall()
    return [{"day": row[0], "count": row[1]} for row in rows]

@app.post("/ask/audio")
async def ask_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # ✨ Зберігаємо тимчасово
    temp_path = save_temp_wav(audio_bytes)

    try:
        # 🔍 Diarize
        questions = extract_questions_from_diarization(temp_path)

        if not questions:
            questions = ["(не знайдено питань або не вдалося розпізнати)"]

        # 🤖 GPT відповіді
        answers = [get_answer(client, q) for q in questions]

        full_question = "\n\n".join(questions)
        full_answer = "\n\n".join(answers)

        # 🧾 логування
        append_log(full_question, full_answer, source="mic")
        log_to_db(full_question, full_answer, source="mic", model="gpt-4o", mode=MODE_PROMPT)

        return JSONResponse({"question": full_question, "answer": full_answer})

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)