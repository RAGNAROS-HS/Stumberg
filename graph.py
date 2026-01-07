from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from models import basic_model, advanced_model
from tools.weather import get_weather
from tools.search import search
from tools.vector_search import retrieve_context
from schema import AgentState

# Define tools
tools = [get_weather, search, retrieve_context]
tool_node = ToolNode(tools)

# Bind tools to models
basic_model_with_tools = basic_model.bind_tools(tools)
advanced_model_with_tools = advanced_model.bind_tools(tools)

def get_system_prompt(mode: str) -> str:
    base_prompt = (
        "Your responses should be "
        "succinct, precise, and assertive. Do not hesitate to challenge the "
        "user's opinions or assertions; your primary objective is to convey "
        "recent and factual information."
    )

    if mode == "personal":
        secondary_prompt = (
            " You act as a shopping and lifestyle recommendation "
            "assistant. Your goal is to understand the user's tastes, constraints, and "
            "context, then suggest suitable products, recipes, or techniques.\n"
            "\n"
            " - Infer users preferences and constraints from tools whenever possible"
            "   style, constraints (e.g., dietary needs, injuries, available equipment), "
            "   and past likes/dislikes before giving detailed recommendations.\n"
            " - Use the available preference-analysis and catalog/search tools to infer "
            "   and refine the user's preferences instead of guessing.\n"
            " - When recommending, provide a short ranked list with 2–5 options, and "
            "   briefly state why each option matches the user's preferences.\n"
            "   The offered solutions should always be thoroughly searched, particularly checking forums like reddit"
            "   and other sources for the latest information.\n"
            "   Always prioritize reliability, sturdiness and quality these are paramount for the user."
            " - Surface important trade-offs (price vs. quality, convenience vs. depth of "
            "   effort) and make a clear primary suggestion.\n"
            " - If the user gives strong constraints (e.g., strict budget, allergies, "
            "   time limits), treat them as hard constraints and do not violate them."
        )
        return secondary_prompt + base_prompt
    
    elif mode == "work" or mode == "code":
        # Work and Code share advanced model, no specific secondary prompt in original code 
        # other than "advanced_model" usage.
        # Original code didn't add prompt for 'work'/'code' other than base?
        # Checking original middleware: 
        # elif STATE.mode == "work": model = advanced_model
        # elif STATE.mode == "code": model = advanced_model
        # So it seems they just use base prompt + advanced model.
        # But wait, logic for 'code' with 'human_message' fallback had a huge prompt.
        # The explicit "mode" check (lines 38-44 in original) didn't add text.
        # We will stick to base prompt for now to match behavior.
        return base_prompt
        
    elif mode == "fast":
        return base_prompt
    
    return base_prompt

def model_node(state: AgentState):
    mode = state.get("mode", "fast")
    messages = state["messages"]
    
    system_prompt_content = get_system_prompt(mode)
    
    # Prepend system message if not present or just let the model handle it.
    # Usually we want to ensure the system prompt is the first message.
    # However, since 'messages' is a list that grows, we might want to just 
    # invoke the model with SystemMessage + messages.
    
    if mode in ["work", "code"]:
        model = advanced_model_with_tools
    else:
        # "personal" and "fast" use basic
        model = basic_model_with_tools
        
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
