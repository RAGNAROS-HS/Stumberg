from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

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



def model_node(state: AgentState):
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
