from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
import os
from graph import create_graph

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "pr-whispered-density-79"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
DB_URI = os.getenv("DB_URI", "")

def get_agent_graph(checkpointer):
    return create_graph(checkpointer)

if __name__ == "__main__":
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()  # Creates tables (run once)
        
        agent = get_agent_graph(checkpointer)

        result = agent.invoke(
            {"messages": [{"role": "user", "content": "Explain machine learning in a basic manner"}]},
            config={"configurable": {"thread_id": "session_1"}}
        )

        def print_agent_result(result):
            """Clean agent output."""
            # langgraph result state uses 'messages' key
            messages = result.get("messages", [])
            final_msg = next((msg for msg in reversed(messages) if msg.type == "ai"), None)
            print(final_msg.content if final_msg else "No AI response")
            print(f"Persisted state history length: {len(messages)}")

        print_agent_result(result)
