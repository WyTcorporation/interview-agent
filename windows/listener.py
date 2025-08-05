import sounddevice as sd
import soundfile as sf
import time
import os
import requests

output_dir = "../input_audio"
os.makedirs(output_dir, exist_ok=True)
API_URL = "http://localhost:8000/ask/audio"  # або інший порт, якщо змінив

# Ці функції для постійного прослуховування колонок/екрану

# Отримуємо список хост-API (для перетворення індексу на назву)
hostapis = sd.query_hostapis()
devices = sd.query_devices()

# Знайти WASAPI + CABLE Output
for i, d in enumerate(devices):
    hostapi_index = d["hostapi"]
    hostapi_name = hostapis[hostapi_index]["name"]
    if "CABLE Output" in d["name"] and "WASAPI" in hostapi_name:
        sd.default.device = (i, None)
        print(f"🎧 Використовую пристрій: [{i}] {d['name']} ({hostapi_name})")
        break
else:
    print("❌ Не знайдено CABLE Output через WASAPI")
    exit(1)

def record_audio(duration=5, samplerate=48000):
    print("🎙️  Recording...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    timestamp = int(time.time())
    filename = os.path.join(output_dir, f"recording_{timestamp}.wav")
    sf.write(filename, audio, samplerate)
    print(f"💾 Saved: {filename}")
    return filename

def send_audio_to_api(filename):
    with open(filename, "rb") as f:
        files = {"file": (filename, f, "audio/wav")}
        response = requests.post(API_URL, files=files)
        if response.status_code == 200:
            print(f"🤖 Відповідь: {response.json()['answer']}")
        else:
            print(f"❌ Помилка API: {response.status_code} {response.text}")

while True:
    fname = record_audio()
    send_audio_to_api(fname)
    time.sleep(1)
