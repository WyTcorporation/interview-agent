from datetime import datetime
import base64
import cv2
import numpy as np
from PIL import ImageGrab

session_messages = []

_current_lang_code = "uk-UA"

_LANG_NAME_BY_CODE = {
    "en-US": "English",
    "uk-UA": "Ukrainian",
    "pl-PL": "Polish",
    "ru-RU": "Russian",
}

current_mode_prompt = "Дай коротку відповідь і приклад з коду (якщо доречно)."

def set_language(lang_code: str):
    global _current_lang_code
    if lang_code in _LANG_NAME_BY_CODE:
        _current_lang_code = lang_code

def get_language_name() -> str:
    return _LANG_NAME_BY_CODE.get(_current_lang_code, "Ukrainian")

# def get_system_prompt():
#     return {
#         "role": "system",
#         "content": (
#             f"Ти AI-асистент. {current_mode_prompt} "
#             "Відповідай на питання користувача."
#         )
#     }

def get_system_prompt():
    lang_name = get_language_name()
    return {
        "role": "system",
        "content": (
            # твій режимний prompt
            f"Ти AI-асистент. {current_mode_prompt} "
            # === NEW: інструкція мовою
            f"Always answer in {lang_name}. If the user switches languages, "
            f"still respond in {lang_name} unless explicitly asked otherwise."
            "Відповідай на питання користувача."
        )
    }

def get_answer(client, question: str) -> str:
    user_msg = {"role": "user", "content": question}

    # Додати в історію
    session_messages.append(user_msg)

    # Починаємо prompt з system + останніх N повідомлень (наприклад, 4)
    context = [get_system_prompt()] + session_messages[-4:]

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
