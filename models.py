from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


fast_model = ChatOpenAI(
    model="gpt-4.1-nano",
    temperature=0.1,
    max_tokens=1000,
    timeout=30
)


# research_model = ChatOpenAI(
#     model="o4-mini-deep-research",
#     temperature=0.1,
#     max_tokens=1000,
#     timeout=60
# )


coding_model = ChatOpenAI(
    model="gpt-5-codex",
    temperature=0.1,
    max_tokens=1000,
    timeout=60
)

main_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_tokens=1000,
    timeout=60
)