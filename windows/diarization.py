import os
import uuid
from pyannote.audio import Pipeline
from tempfile import NamedTemporaryFile
import whisper
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv("HUGGINGFACE_TOKEN")

# Завантажуємо модель diarization (один раз)
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)

# Завантажуємо Whisper
whisper_model = whisper.load_model("base")

def save_temp_wav(audio_bytes: bytes) -> str:
    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    with open(temp_filename, "wb") as f:
        f.write(audio_bytes)
    return temp_filename

def extract_questions_from_diarization(audio_path: str, speaker_label: str = None):
    # 1. Отримати сегменти з diarization
    diarization = pipeline(audio_path)

    # 2. Транскрибувати через Whisper
    result = whisper_model.transcribe(audio_path)
    segments = result["segments"]  # [{'start': ..., 'end': ..., 'text': ...}]

    # 3. Поєднати дані: кому належить який сегмент
    speaker_segments = []
    for seg in segments:
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if turn.start <= seg["start"] <= turn.end:
                speaker_segments.append({
                    "speaker": speaker,
                    "text": seg["text"].strip(),
                    "start": seg["start"],
                    "end": seg["end"]
                })
                break

    # 4. Якщо speaker_label заданий — залишаємо лише його
    if speaker_label:
        speaker_segments = [s for s in speaker_segments if s["speaker"] == speaker_label]

    # 5. Витягаємо лише ті сегменти, які є питаннями
    questions = [s["text"] for s in speaker_segments if s["text"].strip().endswith("?")]

    return questions
