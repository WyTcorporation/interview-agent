FROM python:3.10-slim

WORKDIR /app

RUN apt update && apt install -y ffmpeg && pip install --no-cache-dir \
    fastapi uvicorn openai jinja2 python-multipart soundfile requests

COPY ./app /app
COPY ./static /app/static
COPY ./templates /app/templates

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
