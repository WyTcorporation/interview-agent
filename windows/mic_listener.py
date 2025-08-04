import sounddevice as sd
import soundfile as sf
import time
import os
import requests
import uuid

output_dir = "../input_audio"
os.makedirs(output_dir, exist_ok=True)

API_URL = "http://localhost:8000/ask/audio"

def record_audio(duration=4, samplerate=16000):
    print("🎙️  Запис з мікрофона...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    filename = os.path.join(output_dir, f"mic_{uuid.uuid4().hex}.wav")
    sf.write(filename, audio, samplerate)
    return filename

def send_audio_to_api(filename):
    with open(filename, "rb") as f:
        response = requests.post(API_URL, files={"file": f})
        if response.status_code == 200:
            print(f"🤖 Відповідь: {response.json()['answer']}")
        else:
            print(f"❌ Помилка API: {response.status_code} {response.text}")
    os.remove(filename)

while True:
    try:
        fname = record_audio()
        send_audio_to_api(fname)
        time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Зупинено вручну.")
        break
