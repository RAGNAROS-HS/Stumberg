
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    print(f"PostgresSaver loaded: {PostgresSaver}")
    print(f"from_conn_string type: {type(PostgresSaver.from_conn_string)}")
except ImportError as e:
    print(f"ImportError PostgresSaver: {e}")

try:
    from langchain.agents import create_agent
    import inspect
    print(f"create_agent loaded: {create_agent}")
    print(f"create_agent signature: {inspect.signature(create_agent)}")
except ImportError as e:
    print(f"ImportError create_agent: {e}")
except Exception as e:
    print(f"Error inspecting create_agent: {e}")
