from datetime import datetime

session_messages = []

def get_answer(client, question: str) -> str:
    system_msg = {
        "role": "system",
        "content": (
            "Ти досвідчений інженер. "
            "Відповідай лаконічно, впевнено, технічно. "
            "Не пояснюй як викладач. Не пиши води. "
            "Можеш використовувати код, якщо доречно."
        )
    }

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

# def get_answer(client,question: str) -> str:
#
#     with open("app/prompt.txt", "r", encoding="utf-8") as f:
#         base_prompt = f.read()
#
#     system_msg = {
#         "role": "system",
#         "content": base_prompt
#     }
#
#     user_msg = {
#         "role": "user",
#         "content": f"Q: {question}"
#     }
#
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[system_msg, user_msg],
#         temperature=0.7
#     )
#
#     return response.choices[0].message.content.strip()
