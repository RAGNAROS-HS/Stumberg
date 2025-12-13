from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver
from tools.weather import get_weather
from tools.search import search
from middleware import dynamic_model_selection
from schema import Context
from models import basic_model, advanced_model
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "pr-whispered-density-79"
DB_URI = os.getenv("DB_URI", "")

def get_agent_graph(checkpointer):
    agent = create_agent(
        basic_model,
        tools=[get_weather, search],
        middleware=[dynamic_model_selection],
        checkpointer=checkpointer, 
        context_schema=Context
    )
    return agent

if __name__ == "__main__":
    #instead of this I can use the direct OPENAI package, need to check how that works
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()  # Creates tables (run once)
        
        agent = get_agent_graph(checkpointer)

        #print(agent.invoke({"messages": [{"role": "user", "content": "what is the weather in Amsterdam?"}]}))

        result = agent.invoke(
            {"messages": [{"role": "user", "content": "Explain machine learning in a basic manner"}]},
            config={"configurable": {"thread_id": "session_1"}}
            #context={"user_role": "expert"}
        )

        def print_agent_result(result):
            """Clean agent output."""
            final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
            print(final_msg.content if final_msg else "No AI response")
            print(f"Persisted state history length: {len(result['messages'])}")


        print_agent_result(result)

