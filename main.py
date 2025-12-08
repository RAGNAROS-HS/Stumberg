from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, wrap_tool_call,dynamic_prompt, wrap_model_call
from langchain.tools import tool
from langchain.messages import ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver  



from tools.weather import get_weather
from dotenv import load_dotenv
import os
from typing import TypedDict

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "pr-whispered-density-79"


DB_URI = "postgresql://postgres:your_password@localhost:5432/langgraph_db?sslmode=disable"
checkpointer = PostgresSaver.from_conn_string(DB_URI)
checkpointer.setup()  # Creates tables (run once)


class Context(TypedDict):
    user_role: str



@dynamic_prompt
def infer_role_prompt(request: ModelRequest) -> str:
    """Infer user role from conversation history."""
    try:
        messages = request.runtime.state.get("messages", [])
        recent_content = " ".join(
            msg.content.lower() for msg in messages[-8:] 
            if hasattr(msg, 'content') and msg.content
        )
        
        base_prompt = "You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information"
        
        if any(term in recent_content for term in ["advanced", "algorithm", "ontology", "sat solver", "dl", "description logic", "evolutionary", "nash", "q-learning"]):
            return f"{base_prompt} Provide detailed technical responses."
        elif any(term in recent_content for term in ["beginner", "explain simply", "what is", "how does", "basics"]):
            return f"{base_prompt} Explain concepts simply and avoid jargon."
        
        return base_prompt
    except:
        # Fallback if no messages/state available
        return "You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information"


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
    middleware=[dynamic_model_selection, infer_role_prompt],
    checkpointer=checkpointer, 
    context_schema=Context
)#you can give much more detail here, much more data


#print(agent.invoke({"messages": [{"role": "user", "content": "what is the weather in Amsterdam?"}]}))

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Explain machine learning in a advanced manner"}]},
    config={"configurable": {"thread_id": "session_1"}}
    #context={"user_role": "expert"}
)

def print_agent_result(result):
    """Clean agent output."""
    final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
    print(final_msg.content if final_msg else "No AI response")
    print(f"Persisted state history length: {len(result['messages'])}")


print_agent_result(result)

