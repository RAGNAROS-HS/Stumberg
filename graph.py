from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
import os
from models import fast_model, coding_model, main_model
from tools.weather import get_weather
from tools.vector_search import retrieve_context
from subagents.search_subagent import ask_search_agent
from schema import AgentState
from prompts import get_system_prompt


# Define tools
tools = [get_weather, ask_search_agent, retrieve_context]
tool_node = ToolNode(tools)

# Bind tools to models
fast_model_with_tools = fast_model.bind_tools(tools)
#research_model_with_tools = research_model.bind_tools(tools)
coding_model_with_tools = coding_model.bind_tools(tools)
main_model_with_tools = main_model.bind_tools(tools)

 
def model_node(state: AgentState, config):
    mode = state.get("mode", "fast")
    messages = state["messages"]
    
    system_prompt_content = get_system_prompt(mode)
    
    if mode == "code":
        model = coding_model_with_tools
    elif mode == "personal":
        #model = research_model_with_tools
        model = main_model_with_tools
    elif mode == "work":
        model = main_model_with_tools
    elif mode == "fast":
        model = fast_model_with_tools

    # Inject File Context
    configurable = config.get("configurable", {})
    thread_id = configurable.get("thread_id")
    
    if thread_id:
        thread_dir = os.path.join(os.getenv("CONVERSATION_DATA_PATH", "/host_e/conversation_data"), thread_id)
        print(f"[DEBUG] Looking for files in: {thread_dir}")
        print(f"[DEBUG] Directory exists: {os.path.exists(thread_dir)}")
        
        if os.path.exists(thread_dir):
            file_context = "\n\n### ATTACHED CONTEXT FILES ###\n"
            found_files = False
            files_in_dir = os.listdir(thread_dir)
            print(f"[DEBUG] Files found in directory: {files_in_dir}")
            
            for filename in files_in_dir:
                file_path = os.path.join(thread_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            file_context += f"\n--- FILE: {filename} ---\n{content}\n"
                            found_files = True
                            print(f"[DEBUG] Successfully read file: {filename} ({len(content)} chars)")
                    except Exception as e:
                        file_context += f"\n--- FILE: {filename} (Error reading: {e}) ---\n"
                        print(f"[DEBUG] Error reading {filename}: {e}")
            
            if found_files:
                file_context += "\n### END OF CONTEXT FILES ###\n"
                system_prompt_content += file_context
                print(f"[DEBUG] Added {len(file_context)} chars of file context to system prompt")
            else:
                print(f"[DEBUG] No files found to attach")
        else:
            print(f"[DEBUG] Thread directory does not exist: {thread_dir}")
    else:
        print(f"[DEBUG] No thread_id found in config")

        
    response = model.invoke([SystemMessage(content=system_prompt_content)] + list(messages))
    
    return {"messages": [response]}

def create_graph(checkpointer=None):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", model_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(checkpointer=checkpointer)

graph = create_graph()
