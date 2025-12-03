from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
#gpt-4.1-nano

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

#instead of this I can use the direct OPENAI package, need to check how that works
agent = create_agent(
    "gpt-4.1-nano",
    tools=[get_weather]
)


print(agent.invoke({"messages": [{"role": "user", "content": "what is the weather in Amsterdam?"}]}))