import streamlit as st
import uuid
from langgraph.checkpoint.postgres import PostgresSaver
from main import get_agent_graph, DB_URI
from langchain_core.messages import HumanMessage, AIMessage
import psycopg

st.set_page_config(page_title="Stumberg Agent", page_icon="🤖")

st.title("Stumberg Agent")

# Define helper functions
def get_available_threads():
    """Fetch distinct thread IDs from the database."""
    try:
        with psycopg.connect(DB_URI) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
                return [row[0] for row in cur.fetchall()]
    except Exception:
        # this will run if tables don't exist
        return []

def get_thread_title(thread_id, agent):
    """Derive a title for the thread based on its content."""
    # Use session state cache if available
    if "titles" not in st.session_state:
        st.session_state.titles = {}
    
    if thread_id in st.session_state.titles:
        return st.session_state.titles[thread_id]
        
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent.get_state(config)
        
        title = "New Chat"
        if state.values and "messages" in state.values:
            messages = state.values["messages"]
            if messages:
                # Find the first human message
                first_human = next((m for m in messages if isinstance(m, HumanMessage)), None)
                if first_human:
                    title = first_human.content[:30] + "..." if len(first_human.content) > 30 else first_human.content
        
        st.session_state.titles[thread_id] = title
        return title
    except Exception:
        return f"Conversation {thread_id[:4]}"

# Initialize Default Thread ID if needed
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Main Chat Logic with Single Agent Initialization
try:
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        agent = get_agent_graph(checkpointer)
        
        # Sidebar for Thread Management
        with st.sidebar:
            st.header("Session Management")
            
            # Generate New ID Button
            if st.button("New Chat", type="primary", use_container_width=True):
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.rerun()

            st.markdown("---")
            st.markdown("### Recent conversations")

            # Thread Selection - Scrollable List
            available_threads = get_available_threads()
            
            # Container for scrollable list (requires streamlit >= 1.30)
            # If using older streamlit, this will just be a linear list which is also fine for now
            # but st.container(height=...) is the way to go.
            with st.container(height=400):
                for tid in available_threads:
                    title = get_thread_title(tid, agent)
                    
                    # Style the button to look active if selected
                    type_ = "primary" if tid == st.session_state.thread_id else "secondary"
                    
                    if st.button(title, key=f"btn_{tid}", type=type_, use_container_width=True):
                         if tid != st.session_state.thread_id:
                            st.session_state.thread_id = tid
                            st.session_state.messages = []
                            st.rerun()

            st.caption(f"Current ID: {st.session_state.thread_id}")

        # Load Chat History from DB (syncing)
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        current_state = agent.get_state(config)
        
        if current_state.values and "messages" in current_state.values:
            st.session_state.messages = current_state.values["messages"]
        elif "messages" not in st.session_state:
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
            user_message = HumanMessage(content=prompt)
            if not isinstance(st.session_state.messages, list):
                 st.session_state.messages = []
            st.session_state.messages.append(user_message)
            
            with st.chat_message("user"):
                st.markdown(prompt)

            # Process with Agent
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                try:
                    result = agent.invoke({"messages": [user_message]}, config=config)
                    final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
                    
                    if final_msg:
                        response_content = final_msg.content
                        message_placeholder.markdown(response_content)
                        st.session_state.messages.append(final_msg)
                        
                        # Invalidate title cache for this thread if it was "New Chat" or different
                        # (simple optimization: just always clear it to force refresh next sidebar render)
                        if st.session_state.thread_id in st.session_state.get("titles", {}):
                            del st.session_state.titles[st.session_state.thread_id]
                    else:
                        message_placeholder.markdown("*No response from agent.*")
                        
                except Exception as e:
                    message_placeholder.error(f"Error invoking agent: {str(e)}")

except Exception as e:
    st.error(f"Failed to initialize agent or connect to database: {e}")
