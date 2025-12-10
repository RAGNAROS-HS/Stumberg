from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

basic_model = ChatOpenAI(
    model="gpt-4.1-nano",
    temperature=0.1,
    max_tokens=1000,
    timeout=30
)

advanced_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_tokens=1000,
    timeout=60
)
