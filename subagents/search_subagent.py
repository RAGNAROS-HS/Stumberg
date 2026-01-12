from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool

from models import fast_model
from tools.search import general_search, reddit_search, subreddit_search, buyforlife_search

# Define the state for the search subagent
class SearchAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Define the tools the subagent can use
search_tools = [general_search, reddit_search, subreddit_search, buyforlife_search]
search_tool_node = ToolNode(search_tools)

# Bind tools to the model
model_with_tools = fast_model.bind_tools(search_tools)

def search_model_node(state: SearchAgentState):
    messages = state["messages"]
    # We can add a specialized system prompt for the search agent here if needed
    # For now, we'll just let it run as a helpful search assistant
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# Define the graph
workflow = StateGraph(SearchAgentState)
workflow.add_node("search_agent", search_model_node)
workflow.add_node("search_tools", search_tool_node)

workflow.add_edge(START, "search_agent")
workflow.add_conditional_edges("search_agent", tools_condition, {"tools": "search_tools", END: END})
workflow.add_edge("search_tools", "search_agent")

search_graph = workflow.compile()

@tool
def ask_search_agent(query: str) -> str:
    """
    Delegates a search task to a specialized search agent. 
    Use this tool for ANY search-related queries, including general info, Reddit discussions, or product recommendations.
    
    Args:
        query: The search query or question to ask the search agent.
    """
    # Invoke the search graph
    result = search_graph.invoke({"messages": [HumanMessage(content=query)]})
    
    # Extract the final response
    messages = result["messages"]
    if messages and isinstance(messages[-1], AIMessage):
        return messages[-1].content
    return "No response from search agent."
