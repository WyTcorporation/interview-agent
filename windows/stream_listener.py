import sounddevice as sd
import numpy as np
import threading
import requests
import io
import time
import keyboard
import soundfile as sf
import uuid

# === НАЛАШТУВАННЯ ===
API_URL = "http://localhost:8000/ask/audio"
SAMPLE_RATE = 48000
CHANNELS = 1

recording = False
recorded_frames = []

print("🎧 Ініціалізація Push-to-Hold Listener")

# Знайти індекс CABLE Output (WASAPI)
hostapis = sd.query_hostapis()
devices = sd.query_devices()
device_index = None
for i, d in enumerate(devices):
    hostapi_index = d["hostapi"]
    hostapi_name = hostapis[hostapi_index]["name"]
    if "CABLE Output" in d["name"] and "WASAPI" in hostapi_name:
        device_index = i
        print(f"🎧 Використовую пристрій: [{i}] {d['name']} ({hostapi_name})")
        break
else:
    raise RuntimeError("❌ CABLE Output через WASAPI не знайдено")

def send_audio(frames):
    audio_np = np.concatenate(frames, axis=0)
    buffer = io.BytesIO()
    sf.write(buffer, audio_np, samplerate=SAMPLE_RATE, format='WAV')
    buffer.seek(0)

    try:
        response = requests.post(API_URL, files={"file": (f"kai_{uuid.uuid4().hex}.wav", buffer, "audio/wav")})
        if response.ok:
            print("🤖 Відповідь:", response.json().get("answer"))
        else:
            print("❌ API помилка:", response.status_code, response.text)
    except Exception as e:
        print("⚠️ Виняток при надсиланні:", e)

def record_loop():
    global recording, recorded_frames
    def callback(indata, frames, time_info, status):
        if status:
            print("⚠️ Статус потоку:", status)
        if recording:
            recorded_frames.append(indata.copy())

    with sd.InputStream(device=device_index, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=callback):
        while True:
            time.sleep(0.05)

def keyboard_loop():
    global recording, recorded_frames
    print("⌨️ Утримуй F8 щоб записати, відпусти щоб надіслати")
    while True:
        keyboard.wait("F8")
        print("🔴 Запис... (утримуй)")
        recorded_frames = []
        recording = True
        while keyboard.is_pressed("F8"):
            time.sleep(0.1)
        recording = False
        if recorded_frames:
            print(f"📤 Відправка {len(recorded_frames)} фрагментів")
            send_audio(recorded_frames)
        else:
            print("⚠️ Нічого не записано")

threading.Thread(target=record_loop, daemon=True).start()
keyboard_loop()
