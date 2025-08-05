import tkinter as tk
import requests
import base64
import io
import mss
from PIL import Image

API_URL = "http://localhost:8000/screen/analyze"

system_prompt = "Ти — технічний співбесідник.Проаналізуй цю частину екрана. Якщо бачиш на екрані питання (тестове або програмне), коротко дай відповідь і поясни чому. Якщо є варіанти — вибери правильний."

# Цей клас для знімок з екрана з перетягуванням між екранами

class ScreenTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🖥️ Screen Assistant")
        self.root.geometry("400x80")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        tk.Label(self.root, text="Перемістіть це вікно на потрібний монітор").pack(pady=5)
        tk.Button(self.root, text="🧠 Спитати", command=self.capture_and_send).pack(pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def capture_and_send(self):
        self.root.withdraw()
        self.root.after(300, self._do_capture)

    def _do_capture(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # [1] = перший повний екран, [2] — другий і т.д.

            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            img.save("screenshot.jpg")

            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()

        try:
            res = requests.post(API_URL, json={
                "image_b64": img_b64,
                "prompt":system_prompt
            })

            if res.ok:
                print("✅ Відповідь:", res.json()["answer"])
            else:
                print("❌ API Error:", res.status_code, res.text)
        except Exception as e:
            print("⚠️ Виняток:", e)

        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ScreenTool().run()
