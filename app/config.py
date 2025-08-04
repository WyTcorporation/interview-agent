from openai import OpenAI
import os


def get_openai_client()-> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
