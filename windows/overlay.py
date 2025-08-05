import tkinter as tk
import sounddevice as sd
import soundfile as sf
import threading
import requests
import os
import uuid
import keyboard
import pyttsx3
import time
import numpy as np

API_URL = "http://localhost:8000/ask/audio"
SAMPLERATE = 16000
CHANNELS = 1

# ✨ ОБЕРИ свою мову і голос:
LANG_CODE = "ru"  # або 'en', 'pl', 'ru' і т.д.
VOICE_NAME = "Irina"

# Цей клас для запису голосом питань в вигляді програми поверх всіх вікон


class OverlayAssistant:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="black")

        self.offset_x = 0
        self.offset_y = 0

        self.engine = pyttsx3.init()
        self.voice = self.pick_voice(LANG_CODE, VOICE_NAME)

        self.text_label = tk.Label(self.root, text="🎙 Тримай F9 щоб говорити | Ctrl+F9 — озвучити", font=("Segoe UI", 11),
                                   bg="black", fg="lime", wraplength=300, justify="left")
        self.text_label.pack(padx=10, pady=(10, 5))

        self.button_frame = tk.Frame(self.root, bg="black")
        self.button_frame.pack(pady=(0, 10))

        self.tts_button = tk.Button(self.button_frame, text="🔈 Озвучити", command=self.speak_text,
                                    font=("Segoe UI", 9), bg="gray20", fg="white")
        self.tts_button.pack(side="left", padx=5)

        self.close_button = tk.Button(self.button_frame, text="✖", command=self.root.destroy,
                                      font=("Segoe UI", 9), bg="darkred", fg="white")
        self.close_button.pack(side="left", padx=5)

        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.last_answer = ""
        self.recording = False
        self.audio_frames = []

        threading.Thread(target=self.listen_hotkey_loop, daemon=True).start()

        self.root.geometry("+60+60")

    def pick_voice(self, lang_code, voice_name=""):
        voices = self.engine.getProperty("voices")
        matched = []
        for v in voices:
            langs = v.languages[0] if isinstance(v.languages[0], str) else v.languages[0].decode(errors="ignore")
            if lang_code.lower() in langs.lower() or lang_code.lower() in v.id.lower():
                matched.append(v)
        if voice_name:
            matched = [v for v in matched if voice_name.lower() in v.name.lower()]
        return matched[0] if matched else self.engine.getProperty("voice")

    def speak_text(self):
        if not self.last_answer:
            return
        self.engine.setProperty("voice", self.voice.id)
        self.engine.setProperty("rate", 175)
        self.engine.say(self.last_answer)
        self.engine.runAndWait()

    def listen_hotkey_loop(self):
        self.text_label.config(text="🎙 Тримай F9 щоб говорити | Ctrl+F9 — озвучити")
        keyboard.add_hotkey("ctrl+F9", self.speak_text)

        while True:
            keyboard.wait("F9")
            self.start_recording()
            while keyboard.is_pressed("F9"):
                time.sleep(0.1)
            self.stop_and_send()

    def start_recording(self):
        if self.recording:
            return
        self.text_label.config(text="🔴 Запис активний... Відпустіть F9 щоб відправити")
        self.root.lift()  # Повертаємо overlay поверх, навіть якщо він загубився
        self.root.update()
        self.audio_frames = []
        self.recording = True
        threading.Thread(target=self._record_loop, daemon=True).start()

    def _record_loop(self):
        with sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype='int16', callback=self.audio_callback):
            while self.recording:
                time.sleep(0.1)

    def audio_callback(self, indata, frames, time_info, status):
        self.audio_frames.append(indata.copy())

    def stop_and_send(self):
        if not self.recording:
            return
        self.recording = False
        self.text_label.config(text="⏳ Обробка...")
        self.root.update()

        if not self.audio_frames:
            self.text_label.config(text="⚠️ Нічого не записано")
            return

        audio_np = np.concatenate(self.audio_frames, axis=0)
        filename = f"temp_{uuid.uuid4().hex}.wav"
        sf.write(filename, audio_np, samplerate=SAMPLERATE)

        try:
            with open(filename, "rb") as f:
                response = requests.post(API_URL, files={"file": f})
            if response.status_code == 200:
                self.last_answer = response.json().get("answer", "🤖 Нема відповіді")
                self.text_label.config(text=f"🧠 {self.last_answer}")
            else:
                self.text_label.config(text=f"❌ Статус: {response.status_code}")
        except Exception as e:
            self.text_label.config(text=f"⚠️ Помилка: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

        # self.root.after(10000, lambda: self.text_label.config(text="🎙 Тримай F9 щоб говорити | Ctrl+F9 — озвучити"))

    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f'+{x}+{y}')

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("📢 Список голосів у системі:")
    eng = pyttsx3.init()
    for v in eng.getProperty("voices"):
        langs = v.languages[0].decode(errors="ignore") if isinstance(v.languages[0], bytes) else v.languages[0]
        print(f"  🔹 {v.name} | {v.id} | lang: {langs}")
    print("\nℹ️ Обери потрібну мову і вкажи у LANG_CODE / VOICE_NAME у файлі overlay.py\n")

    OverlayAssistant().run()
