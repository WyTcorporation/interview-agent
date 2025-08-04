import sounddevice as sd
import soundfile as sf
import time
import os
import requests
import json

output_dir = "../input_audio"
os.makedirs(output_dir, exist_ok=True)
API_URL = "http://localhost:8000/ask"  # або інший порт, якщо змінив

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


# import sounddevice as sd
# import soundfile as sf
# import time
# import os
# import requests
# from datetime import datetime
#
# output_dir = "input_audio"
# os.makedirs(output_dir, exist_ok=True)
#
# devices = sd.query_devices()
# for i, d in enumerate(devices):
#     if "CABLE Output" in d["name"] and "WASAPI" in d["hostapi"].lower():
#         sd.default.device = (i, None)
#         # sd.default.device = ("CABLE Output", None)  # Windows
#         print(f"🎧 Використовую {d['name']} (#{i})")
#         break
#
# def record_audio(duration=5, samplerate=16000):
#     print("🎙️  Recording...")
#     audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
#     sd.wait()
#
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     filename = os.path.join(output_dir, f"recording_{timestamp}.wav")
#     sf.write(filename, audio, samplerate)
#     return filename
#
# def send_to_api(filename):
#     with open(filename, "rb") as f:
#         try:
#             r = requests.post("http://localhost:8000/ask", files={"file": f})
#             if r.status_code == 200:
#                 result = r.json()
#                 log_entry = f"\nQ: {result['question']}\nA: {result['answer']}\n"
#                 print(log_entry)
#                 with open("interview.log", "a", encoding="utf-8") as logf:
#                     logf.write(log_entry)
#             else:
#                 print(f"❌ API error: {r.status_code} - {r.text}")
#         except Exception as e:
#             print(f"⚠️ Exception during POST: {e}")
#
# while True:
#     try:
#         fname = record_audio()
#         send_to_api(fname)
#         time.sleep(1)
#     except KeyboardInterrupt:
#         print("🛑 Stopped by user.")
#         break

# import sounddevice as sd
# import soundfile as sf
# import time
# import os
#
# output_dir = "input_audio"
# os.makedirs(output_dir, exist_ok=True)
#
# def record_audio(duration=5, samplerate=16000):
#     print("Recording...")
#     sd.default.device = ("CABLE Output", None) # Windows
#     # d.default.device = ("Monitor of Built-in Audio", None) # Ubuntu
#     audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
#     sd.wait()
#     timestamp = int(time.time())
#     filename = os.path.join(output_dir, f"recording_{timestamp}.wav")
#     sf.write(filename, audio, samplerate)
#     print(f"Saved: {filename}")
#
# while True:
#     record_audio()
#     time.sleep(1)