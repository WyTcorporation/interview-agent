from datetime import datetime
import base64
import cv2
import numpy as np
from PIL import ImageGrab

session_messages = []

system_msg = {
    "role": "system",
    "content": (
        "Ти досвідчений інженер. "
        "Відповідай лаконічно, впевнено, технічно. "
        "Не пояснюй як викладач. Не пиши води. "
        "Можеш використовувати код, якщо доречно."
    )
}


def get_answer(client, question: str) -> str:
    user_msg = {"role": "user", "content": question}

    # Додати в історію
    session_messages.append(user_msg)

    # Починаємо prompt з system + останніх N повідомлень (наприклад, 4)
    context = [system_msg] + session_messages[-4:]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=context,
        temperature=0.9
    )

    assistant_msg = {
        "role": "assistant",
        "content": response.choices[0].message.content.strip()
    }

    # Додаємо відповідь у контекст
    session_messages.append(assistant_msg)

    # логування у файл
    with open("interview.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}\\nQ: {question}\\nA: {assistant_msg['content']}\\n\\n")

    return assistant_msg["content"]


def get_answer_with_image(client, prompt: str, image_b64: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Ти аналітик. Користувач надіслав питання і зображення. "
                "Використай зображення при відповіді. Відповідай коротко і технічно."
            )
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.9
    )

    assistant_msg = {
        "role": "assistant",
        "content": response.choices[0].message.content.strip()
    }

    session_messages.append(assistant_msg)
    return assistant_msg["content"]



def capture_screenshot_b64() -> str:
    screenshot = ImageGrab.grab()
    screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode(".jpg", screenshot_np)
    return base64.b64encode(buffer).decode()
