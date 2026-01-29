# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Stumberg is a multi-mode conversational AI agent built with LangGraph and LangChain. The system uses a graph-based architecture to route queries to specialized modes (Personal, Work, Code, Fast), each with unique prompts and model configurations. State persistence is handled via PostgreSQL, and the primary interface is a Streamlit web application.

## Commands

### Running the Application

**Streamlit Web Interface** (primary):
```bash
streamlit run app.py
```
Access at `http://localhost:8501`

**CLI Mode** (for testing):
```bash
python main.py
```
Edit the query in `main.py` before running.

### Database Setup

Initialize PostgreSQL tables (run once):
```bash
python main.py
```
The `checkpointer.setup()` call creates necessary tables.

### Docker

Build and run:
```bash
docker build -t stumberg-agent .
docker run -p 8501:8501 --env-file .env -v /path/to/data:/host_e/conversation_data stumberg-agent
```

### LangGraph Server (Optional)

Deploy as LangGraph server:
```bash
langgraph serve --config langgraph.json
```

## Architecture

### Graph Flow (graph.py)

The main agent follows this execution flow:

1. **START** → **agent** node (model_node function)
2. **agent** → conditional routing via `tools_condition`:
   - If tool calls → **tools** node
   - If no tool calls → **END**
3. **tools** → back to **agent** (loop until completion)

**Key Design Pattern**: The `model_node` function dynamically selects the model based on `state["mode"]` and injects file context from the thread-specific directory before invoking the LLM.

### State Management (schema.py)

**AgentState** contains:
- `messages`: Annotated list of messages with `add_messages` reducer
- `mode`: Literal type selecting "personal" | "work" | "code" | "fast"
- `user_role`: String for user context

State is persisted per `thread_id` using `PostgresSaver` from `langgraph-checkpoint-postgres`.

### Subagent Architecture (subagents/search_subagent.py)

Search operations are delegated to an independent LangGraph subagent:
- **SearchAgentState**: Simple message-only state
- **Tools**: `general_search`, `reddit_search`, `subreddit_search`, `buyforlife_search`
- **Model**: Uses `fast_model` (gpt-4.1-nano) for efficiency
- **Entry Point**: `ask_search_agent` tool wraps the subgraph invocation

This delegation pattern isolates search logic and allows the search agent to orchestrate multiple search tools independently.

### Mode System (prompts.py)

Each mode has a specialized system prompt retrieved via `get_system_prompt(mode)`:

- **personal**: Shopping/lifestyle assistant emphasizing durability, quality, and r/BuyItForLife recommendations
- **work**: Research assistant prioritizing factual accuracy and explicit handling of information gaps
- **code**: Programming assistant focused on simplicity, readability, and complete code output
- **fast**: Ultra-concise information retrieval with minimal elaboration

Mode selection happens in the Streamlit UI and is passed through `state["mode"]`.

### File Context Injection (graph.py:42-79)

Files uploaded via Streamlit are stored in `{CONVERSATION_DATA_PATH}/{thread_id}/`. The `model_node` function:
1. Reads all files from the thread directory
2. Concatenates file contents with headers
3. Appends to the system prompt as `### ATTACHED CONTEXT FILES ###`

This enables per-conversation file-based context without modifying the state schema.

### Tool Binding

Tools are bound to models in `graph.py`:
- **Main tools**: `get_weather`, `ask_search_agent`, `retrieve_context`
- **Search subagent tools**: `general_search`, `reddit_search`, `subreddit_search`, `buyforlife_search`

All modes have access to all main tools; the search subagent has access only to search tools.

## Models (models.py)

- **fast_model**: `gpt-4.1-nano` (timeout=30s, temp=0.1, max_tokens=1000)
- **main_model**: `gpt-4o` (timeout=60s, temp=0.1, max_tokens=1000)
- **coding_model**: `gpt-4o` (timeout=60s, temp=0.1, max_tokens=1000)

Mode-to-model mapping:
- `fast` → fast_model
- `personal` → main_model
- `work` → main_model
- `code` → coding_model

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=<key>
DB_URI=postgresql://user:password@host:port/database
```

Optional:
```
PINECONE_API_KEY=<key>
LINKUP_API_KEY=<key>
LANGCHAIN_API_KEY=<key>
LANGCHAIN_PROJECT=<project_name>
CONVERSATION_DATA_PATH=/path/to/conversation/data
```

**Note**: LangSmith tracing is hardcoded to `true` in `main.py` with endpoint `https://eu.api.smith.langchain.com`.

## Project Structure

- **app.py**: Streamlit UI with thread management, file uploads, mode selection
- **main.py**: CLI entry point, database initialization, LangSmith configuration
- **graph.py**: LangGraph agent definition, model selection, file context injection
- **prompts.py**: Mode-specific system prompts
- **models.py**: Model configurations
- **schema.py**: AgentState type definition
- **tools/**: Individual tool implementations (search.py, weather.py, vector_search.py)
- **subagents/**: Independent subgraphs (search_subagent.py)
- **RAG_building_scripts/**: Utilities for creating vector stores (exam_scraping.py, reddit_scraping.py, create_pdf_vector_store.py)

## Adding New Features

### Adding a New Tool

1. Create tool function in `tools/<name>.py` decorated with `@tool`
2. Import and add to `tools` list in `graph.py:16`
3. Bind to model(s) in `graph.py:20-23`

### Adding a New Mode

1. Add prompt logic to `prompts.py:get_system_prompt()`
2. Add model selection branch in `graph.py:model_node()`
3. Add UI button in `app.py` (around line 214-237)

### Adding a New Subagent

Follow the pattern in `subagents/search_subagent.py`:
1. Define state class (TypedDict with messages)
2. Create StateGraph with model node and tool node
3. Compile graph and expose via `@tool` wrapper function
4. Import and add wrapper to main tools list

## Important Notes

- **Thread-based isolation**: Each conversation has a unique `thread_id` for state persistence and file storage
- **No tests**: The `tests/` directory is empty; testing is done manually via CLI or Streamlit
- **Reddit API credentials**: `tools/search.py:buyforlife_search()` contains placeholder credentials ("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET") that must be replaced
- **PostgreSQL required**: The agent will not function without a valid `DB_URI`
- **File uploads persist**: Uploaded files are stored on disk in `CONVERSATION_DATA_PATH/{thread_id}/` and injected into every subsequent message in that thread
