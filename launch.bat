@echo off
uvicorn app.main:app --reload
python listener.py
pause
