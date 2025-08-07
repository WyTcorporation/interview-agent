import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline

load_dotenv()
hf_token = os.getenv("HUGGINGFACE_TOKEN")
print(hf_token)
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token=hf_token
)

def diarize(file_path: str):
    diarization = pipeline(file_path)
    segments = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end
        })

    return segments

# 👇 Пример використання
if __name__ == "__main__":
    audio_file = "your_audio.wav"
    segs = diarize(audio_file)
    for s in segs:
        print(f"[{s['start']:.2f}–{s['end']:.2f}] {s['speaker']}")
