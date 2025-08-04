import tkinter as tk
import sounddevice as sd
import soundfile as sf
import threading
import requests
import os
import uuid
import keyboard
import pyttsx3

API_URL = "http://localhost:8000/ask/audio"
DURATION = 4
SAMPLERATE = 16000

# ✨ ОБЕРИ свою мову і голос:
LANG_CODE = "ru"  # або 'en', 'pl', 'ru' і т.д.
VOICE_NAME = "Irina"   # залиш порожнім, щоб вибрати перший голос з цією мовою

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

        # UI
        self.text_label = tk.Label(self.root, text="🤖 Готовий (F9 – слухати)", font=("Segoe UI", 11),
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
        threading.Thread(target=self.listen_hotkeys, daemon=True).start()

        self.root.geometry("+60+60")

    def pick_voice(self, lang_code, voice_name=""):
        voices = self.engine.getProperty("voices")
        matched = []
        for v in voices:
            # Безпечна обробка мов
            langs = v.languages[0] if isinstance(v.languages[0], str) else v.languages[0].decode(errors="ignore")
            if lang_code.lower() in langs.lower() or lang_code.lower() in v.id.lower():
                matched.append(v)

        if voice_name:
            matched = [v for v in matched if voice_name.lower() in v.name.lower()]

        if matched:
            voice = matched[0]
            print(f"✅ Обрано голос: {voice.name} | {voice.id}")
            return voice
        else:
            print("⚠️ Голос не знайдено — використано стандартний")
            return self.engine.getProperty("voice")

    def speak_text(self):
        if not self.last_answer:
            return
        self.engine.setProperty("voice", self.voice.id)
        self.engine.setProperty("rate", 175)
        self.engine.say(self.last_answer)
        self.engine.runAndWait()

    def listen_hotkeys(self):
        keyboard.add_hotkey("F9", self.capture_audio)
        keyboard.add_hotkey("ctrl+F9", self.speak_text)
        self.text_label.config(text="🎙 Натисни F9 щоб спитати | Ctrl+F9 — озвучити")
        keyboard.wait()

    def capture_audio(self):
        self.text_label.config(text="🔴 Записую...")
        self.root.update()

        filename = f"temp_{uuid.uuid4().hex}.wav"
        audio = sd.rec(int(DURATION * SAMPLERATE), samplerate=SAMPLERATE, channels=1, dtype='int16')
        sd.wait()
        sf.write(filename, audio, SAMPLERATE)

        try:
            with open(filename, "rb") as f:
                response = requests.post(API_URL, files={"file": f})
            if response.status_code == 200:
                self.last_answer = response.json().get("answer", "🤖 Нема відповіді")
                self.text_label.config(text=f"🧠 {self.last_answer}")
            else:
                self.text_label.config(text=f"❌ {response.status_code}")
        except Exception as e:
            self.text_label.config(text=f"⚠️ Помилка: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

        self.root.after(10000, lambda: self.text_label.config(text="🎙 Натисни F9 щоб спитати | Ctrl+F9 — озвучити"))

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
