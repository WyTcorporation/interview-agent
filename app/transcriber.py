import openai
import requests
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

def transcribe_and_send(filepath):
    with open(filepath, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    q = transcript["text"]
    print("🧠", q)
    requests.post("http://interview-agent:8000/ask", files={"file": open(filepath, "rb")})