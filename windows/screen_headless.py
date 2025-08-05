import requests
import base64
import io
import mss
from PIL import Image

API_URL = "http://localhost:8000/screen/analyze"

system_prompt = "Ти — технічний співбесідник.Проаналізуй цю частину екрана. Якщо бачиш на екрані питання (тестове або програмне), коротко дай відповідь і поясни чому. Якщо є варіанти — вибери правильний."

def capture_and_send(prompt=system_prompt):
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        res = requests.post(API_URL, json={
            "image_b64": img_b64,
            "prompt": prompt
        })

        if res.ok:
            print("✅ Відповідь:", res.json()["answer"])
        else:
            print("❌ API Error:", res.status_code, res.text)

    except Exception as e:
        print("⚠️ Виняток:", e)

if __name__ == "__main__":
    capture_and_send()
