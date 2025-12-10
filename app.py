import streamlit as st
import uuid
from langgraph.checkpoint.postgres import PostgresSaver
from main import get_agent_graph, DB_URI
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Stumberg Agent", page_icon="🤖")

st.title("Stumberg Agent")

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Handle User Input
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to state
    user_message = HumanMessage(content=prompt)
    st.session_state.messages.append(user_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with Agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Setup DB and Agent
            # Note: In a real production app, connection pooling should be handled more efficiently/globally
            # but for this script usage, opening a connection per run is acceptable if pool is managed.
            with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
                checkpointer.setup()
                agent = get_agent_graph(checkpointer)
                
                # Invoke Agent
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                result = agent.invoke({"messages": [user_message]}, config=config)
                
                # Extract AI Response
                # The agent returns the full state history in result["messages"]
                # We need the LAST AI message added.
                # However, since we are maintaining local history in session_state for display, 
                # we technically only need the new response.
                
                final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
                
                if final_msg:
                    response_content = final_msg.content
                    message_placeholder.markdown(response_content)
                    st.session_state.messages.append(final_msg)
                else:
                    message_placeholder.markdown("*No response from agent.*")

        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")
