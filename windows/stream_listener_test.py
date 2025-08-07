import subprocess
import threading
import time
import keyboard
import requests
import uuid
import os

API_URL = "http://localhost:8000/ask/audio"
OUTPUT_FILE = f"temp_{uuid.uuid4().hex}.wav"

def record_audio_ffmpeg():
    return subprocess.Popen([
        "ffmpeg",
        "-f", "dshow",
        "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",
        "-t", "00:00:30",
        "-acodec", "pcm_s16le",
        "-ar", "48000",
        "-ac", "1",
        OUTPUT_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def send_audio(filepath):
    try:
        with open(filepath, "rb") as f:
            response = requests.post(API_URL, files={"file": (os.path.basename(filepath), f, "audio/wav")})
            if response.ok:
                print("🤖 Відповідь:", response.json().get("answer"))
            else:
                print("❌ API помилка:", response.status_code, response.text)
    except Exception as e:
        print("⚠️ Виняток:", e)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

print("🎧 FFMPEG Listener активний")
print("⌨️ Утримуй F8 щоб записати звук з CABLE Output...")

while True:
    keyboard.wait("F8")
    print("🔴 Запис з CABLE Output...")
    start_time = time.time()  # ⏱ старт запису

    proc = record_audio_ffmpeg()
    while keyboard.is_pressed("F8"):
        time.sleep(0.1)

    print("⏳ Завершення запису...")
    try:
        proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.terminate()

    time.sleep(0.3)  # щоб файл дописався

    if os.path.exists(OUTPUT_FILE):
        print("📤 Відправка...")
        send_start = time.time()
        send_audio(OUTPUT_FILE)
        end_time = time.time()

        print(f"⏱ Запис: {send_start - start_time:.2f} сек | Відповідь: {end_time - send_start:.2f} сек | Загалом: {end_time - start_time:.2f} сек")
    else:
        print("⚠️ Файл не записано!")
