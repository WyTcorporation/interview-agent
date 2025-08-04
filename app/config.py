from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def get_openai_client()-> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
