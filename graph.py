from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from models import fast_model, research_model, coding_model, main_model
from tools.weather import get_weather
from tools.search import search
from tools.vector_search import retrieve_context
from schema import AgentState

# Define tools
tools = [get_weather, search, retrieve_context]
tool_node = ToolNode(tools)

# Bind tools to models
fast_model_with_tools = fast_model.bind_tools(tools)
research_model_with_tools = research_model.bind_tools(tools)
coding_model_with_tools = coding_model.bind_tools(tools)
main_model_with_tools = main_model.bind_tools(tools)

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
            "   a priority should always be to search the buyforlife subreddit a"
            "   and other sources for the latest information.\n"
            "   Always prioritize reliability, sturdiness and quality these are paramount for the user."
            " - Surface important trade-offs (price vs. quality, convenience vs. depth of "
            "   effort) and make a clear primary suggestion.\n"
            " - If the user gives strong constraints (e.g., strict budget, allergies, "
            "   time limits), treat them as hard constraints and do not violate them."
            "   If there are available discounts state them and make sure to highlight them., do not hesitate to recommend websites or brands, but vet their authenticity first"
        )
        return secondary_prompt + base_prompt
    
    elif mode == "work":
        secondary_prompt = (
            "You act as an assistant for work/university study tasks."
            "You search for information regarding the users topic using the available tools."
            "You do not provide any intro, just output the information"
            "Your primary goal is for your outputs to be factually correct and up to date."
            "If you are unable to find information, do not make assumptions, instead state that you are unable to find information."
            "Similarly with problem solving tasks, make sure it is factual, and if there is a risk of it not being so - state it and abort the solving"

        )
        return secondary_prompt + base_prompt

    elif mode == "code":
        secondary_prompt = (
            " You act as a coding assistant"
            "Your goal is to create, modify, debug, optimize or otherwise improve code"
            " You do so by deeply thinking about potential solutions and then implementing them"
            " You do not add unnecessary comments or code, you modify the code to be as simple as possible"
            " Readability and simplicity are the target, do not add any unnessesary complexity"
            " Output the code fully and within the chat, do not skip any parts of the code even if you did not change them"
            " do not make any assumptions yourself, do not work outside of the scope given by the user"
            " you are NOT meant to be creative, rather your purpose is to do exactly what the user asks you to"
            " Take the user's input and envision it in code this should be done directly unless there is a critical design choice to be made"
            " In which case you should not take it yourself, ask the user what they wish and provide a range of options"
            " Do not provide any intro, just output the code followed up with a brief explanation"
            " The offered solutions should always be thoroughly searched, particularly checking forums like stackoverflow or documentation"
            " and other sources for the latest information.\n"
            " Always prioritize reliability, and simplicity these are paramount for the user."
            " If the user gives strong constraints treat them as hard constraints and do not violate them."
        )
        return secondary_prompt + base_prompt
        
    elif mode == "fast":
        secondary_prompt = (
            " You act as ultra fast information retrieval assistant."
            "Your goal is to provide succinct, precise responses "
            "packed purely with the basic information necessary/asked"
            " You highlight the main points of the information and do not elaborate on it unless implied in the prompt"
            " Keep your word count low and do not write any unnessesary text or intro, do not ask follow up questions"
        )
        return secondary_prompt + base_prompt
    
    return base_prompt

def model_node(state: AgentState):
    mode = state.get("mode", "fast")
    messages = state["messages"]
    
    system_prompt_content = get_system_prompt(mode)
    
    # Prepend system message if not present or just let the model handle it.
    # Usually we want to ensure the system prompt is the first message.
    # However, since 'messages' is a list that grows, we might want to just 
    # invoke the model with SystemMessage + messages.
    
    if mode == "code":
        model = coding_model_with_tools
    elif mode == "personal":
        model = research_model_with_tools
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
