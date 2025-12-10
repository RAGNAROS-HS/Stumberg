import streamlit as st
import uuid
from langgraph.checkpoint.postgres import PostgresSaver
from main import get_agent_graph, DB_URI
from langchain_core.messages import HumanMessage, AIMessage
import psycopg

st.set_page_config(page_title="Stumberg Agent", page_icon="🤖")

st.title("Stumberg Agent")

def get_available_threads():
    """Fetch distinct thread IDs from the database."""
    try:
        with psycopg.connect(DB_URI) as conn:
            with conn.cursor() as cur:
                # Check if table exists first (or just try query)
                # LangGraph checkpoint schema usually has a 'thread_id' column in 'checkpoints'
                cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
                return [row[0] for row in cur.fetchall()]
    except Exception:
        # Tables might not be created yet
        return []

# Initialize Default Thread ID if needed
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Sidebar for Thread Management
with st.sidebar:
    st.header("Session Management")
    
    # Generate New ID Button
    if st.button("New Chat", type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    # Thread Selection
    available_threads = get_available_threads()
    
    # Ensure current thread is in the list
    if st.session_state.thread_id not in available_threads:
        available_threads.insert(0, st.session_state.thread_id)
    
    selected_thread = st.selectbox(
        "Select Conversation",
        available_threads,
        index=available_threads.index(st.session_state.thread_id)
        if st.session_state.thread_id in available_threads else 0
    )

    if selected_thread != st.session_state.thread_id:
        st.session_state.thread_id = selected_thread
        st.session_state.messages = []
        st.rerun()

    st.caption(f"Current ID: \n{st.session_state.thread_id}")

# Load Chat History from DB
if "messages" not in st.session_state or not st.session_state.messages:
    try:
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            checkpointer.setup()
            agent = get_agent_graph(checkpointer)
            
            # Fetch State
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            current_state = agent.get_state(config)
            
            if current_state.values and "messages" in current_state.values:
                st.session_state.messages = current_state.values["messages"]
            else:
                st.session_state.messages = []
    except Exception as e:
        st.error(f"Failed to load history: {e}")
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
    if not isinstance(st.session_state.messages, list):
         st.session_state.messages = []
    st.session_state.messages.append(user_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with Agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
                checkpointer.setup()
                agent = get_agent_graph(checkpointer)
                
                # Invoke Agent
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                result = agent.invoke({"messages": [user_message]}, config=config)
                
                # Extract AI Response
                final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
                
                if final_msg:
                    response_content = final_msg.content
                    message_placeholder.markdown(response_content)
                    
                    # Update local state with the result (this ensures syncing)
                    # Ideally, we just reload from DB next time or append logic.
                    # Appending manually to mirror:
                    st.session_state.messages.append(final_msg)
                else:
                    message_placeholder.markdown("*No response from agent.*")

        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")
