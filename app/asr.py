import os
import uuid

# Створимо папку recordings, якщо її ще нема
os.makedirs("recordings", exist_ok=True)

def transcribe_audio(client, audio_bytes: bytes) -> str:
    temp_filename = os.path.join("recordings", f"{uuid.uuid4().hex}.wav")

    try:
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)

        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcript.text
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
