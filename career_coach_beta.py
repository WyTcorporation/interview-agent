from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
import streamlit as st
from langchain.prompts import PromptTemplate

load_dotenv()  # Loads variables from .env into environment
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key: {openai_api_key}")

llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

prompt_template = PromptTemplate(
    input_variables=["position", "company", "strengths", "weaknesses"],
    template= """You are a career coach. Provide tailored interview tips for the
position of {position} at {company}.
Highlight your strengths in {strengths} and prepare for questions
about your weaknesses such as {weaknesses}."""
)

st.title("Interview Helper")

position = st.text_input("What is your position: ")
company = st.text_input("What is your company: ")
strengths = st.text_area("What are your strengths: ")
weaknesses = st.text_area ("What are your weaknesses: ")

if position and company and strengths and weaknesses:
    response = llm.invoke(prompt_template.format(position=position, company=company, strengths=strengths, weaknesses=weaknesses))
    st.write(response.content)