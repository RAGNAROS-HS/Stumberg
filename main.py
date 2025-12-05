from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, wrap_tool_call
from langchain.tools import tool
from langchain.messages import ToolMessage
from tools.weather import get_weather
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

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


@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

#this whole section is a bit useless atm, but im putting it down for potential future work on dynamic model selection depending on condition
@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    message_count = len(request.state["messages"])
    if message_count > 10:
        model = advanced_model
    else:
        model = basic_model

    return handler(request.override(model=model))


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

#instead of this I can use the direct OPENAI package, need to check how that works
agent = create_agent(
    basic_model,
    tools=[get_weather, search],
    system_prompt="You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information",
    middleware=[dynamic_model_selection]
)


print(agent.invoke({"messages": [{"role": "user", "content": "what is the weather in Amsterdam?"}]}))