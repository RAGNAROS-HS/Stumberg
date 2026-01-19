import streamlit as st
import uuid
from langgraph.checkpoint.postgres import PostgresSaver
from main import get_agent_graph, DB_URI
from langchain_core.messages import HumanMessage, AIMessage

import psycopg

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

st.set_page_config(page_title="Stumberg Agent", page_icon="misc/stumlogo.png")

st.markdown("""
<style>
    div[data-testid="stButton"] > button {
        border: none !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Stumberg Agent")

def get_available_threads():
    """Fetch distinct thread IDs from the database."""
    try:
        with psycopg.connect(DB_URI) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT thread_id FROM checkpoints GROUP BY thread_id ORDER BY MAX(checkpoint_id) DESC")
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

if "choice" not in st.session_state:
    st.session_state.choice = None

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
                st.session_state.choice = None
                st.rerun()

            st.markdown("---")
            st.markdown("### Recent conversations")

            # Thread Selection - Scrollable List
            available_threads = get_available_threads()
            
            # Container for scrollable list
            with st.container(height="stretch"):
                for tid in available_threads:
                    title = get_thread_title(tid, agent)
                    
                    # Style the button to look active if selected
                    type_ = "primary" if tid == st.session_state.thread_id else "secondary"
                    
                    if st.button(title, key=f"btn_{tid}", type=type_, use_container_width=True):
                         if tid != st.session_state.thread_id:
                            st.session_state.thread_id = tid
                            st.session_state.messages = []
                            st.session_state.choice = "loaded"
                            #not sure this should be the case, maybe I want to ask every chat switch
                            st.rerun()

            st.caption(f"Current ID: {st.session_state.thread_id}")

        if st.session_state.choice is None:
            st.markdown("""
            <style>
            section[data-testid="stMain"] div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button {
                height: 15vh;
                width: 100%;
                font-size: 1.5rem;
                margin-bottom: 10px;
            }
            </style>
                        """, unsafe_allow_html=True)
            
            # Welcome Screen Options
            st.subheader("Choose your mode")
            
            c1 = st.container()
            with c1:
                if st.button("Work", key="opt1", use_container_width=True):
                    st.session_state.choice = "work"

                    st.rerun()
            
            c2 = st.container()
            with c2:
                if st.button("Personal", key="opt2", use_container_width=True):
                    st.session_state.choice = "personal"

                    st.rerun()
            
            c3 = st.container()
            with c3:
                if st.button("Code", key="opt3", use_container_width=True):
                    st.session_state.choice = "code"

                    st.rerun()
            
            c4 = st.container()
            with c4:
                if st.button("Fast", key="opt4", use_container_width=True):
                    st.session_state.choice = "fast"

                    st.rerun()  
        
        else:
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
                    with st.chat_message("user", avatar=USER_AVATAR):
                        st.markdown(message.content)
                elif isinstance(message, AIMessage):
                    with st.chat_message("assistant", avatar=BOT_AVATAR):
                        st.markdown(message.content)

            # Handle User Input
            if prompt := st.chat_input("What's on your mind?"):
                user_message = HumanMessage(content=prompt)
                if not isinstance(st.session_state.messages, list):
                     st.session_state.messages = []
                st.session_state.messages.append(user_message)
                
                with st.chat_message("user", avatar=USER_AVATAR):
                    st.markdown(prompt)

                # Process with Agent
                with st.chat_message("assistant", avatar=BOT_AVATAR):
                    message_placeholder = st.empty()
                    message_placeholder.markdown("Thinking...")
                    
                    try:
                        mode_ = st.session_state.choice if st.session_state.choice else "fast"
                        result = agent.invoke({"messages": [user_message], "mode": mode_}, config=config)
                        final_msg = next((msg for msg in reversed(result["messages"]) if msg.type == "ai"), None)
                        
                        if final_msg:
                            response_content = final_msg.content
                            message_placeholder.markdown(response_content)
                            st.session_state.messages.append(final_msg)
                            
                            # Invalidate title cache for this thread
                            if st.session_state.thread_id in st.session_state.get("titles", {}):
                                del st.session_state.titles[st.session_state.thread_id]
                        else:
                            message_placeholder.markdown("*No response from agent.*")
                            
                    except Exception as e:
                        message_placeholder.error(f"Error invoking agent: {str(e)}")

except Exception as e:
    st.error(f"Failed to initialize agent or connect to database: {e}")
