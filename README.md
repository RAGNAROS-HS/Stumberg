# Stumberg Agent

A modular, multi-mode AI assistant built with LangGraph and LangChain. Provides intelligent, context-aware responses through a Streamlit web interface with specialized modes for personal shopping, work/study research, coding assistance, and fast information retrieval.

## Overview

Stumberg is a conversational AI agent that combines large language models with specialized tools and persistent memory. The system uses a graph-based architecture to route queries to appropriate models and tools based on user-selected modes.

## Technology Stack

### Core Frameworks
- **LangGraph**: Agent orchestration and state machine management
- **LangChain**: LLM framework and tool integration
- **Streamlit**: Web-based user interface
- **PostgreSQL**: Conversation state persistence via `langgraph.checkpoint.postgres.PostgresSaver`

### Language Models
- **GPT-4o**: Primary model for Work, Personal, and Code modes
- **GPT-4.1-nano**: Fast model for quick information retrieval

### External Services
- **OpenAI API**: Language model access
- **Pinecone**: Vector database for semantic search
- **LinkupClient**: Web search API
- **PRAW**: Reddit API wrapper for r/BuyItForLife scraping
- **Open-Meteo API**: Weather data retrieval
- **LangSmith**: Agent tracing and debugging (optional)

## Features

### Core Capabilities

**Persistent Conversations**
- PostgreSQL-backed state management
- Thread-based conversation history
- Automatic state checkpointing

**Multi-Mode Operation**
- Mode-specific system prompts and behavior
- Dynamic model selection based on mode
- Specialized tool access per mode

**File Context System**
- Per-conversation file uploads (txt, md, py, json, pdf)
- Automatic context injection into system prompts
- Persistent file storage in conversation-specific directories

**Advanced Search Integration**
- Dedicated search subagent with multiple search tools
- Web search via LinkupClient
- Reddit-specific and subreddit-targeted searches
- r/BuyItForLife product recommendation scraping

**Vector Search**
- Pinecone vector store integration
- Semantic context retrieval
- Knowledge base querying

**Weather Information**
- Real-time weather data
- Location-based queries

### Interface Features

- Thread-based conversation management
- File upload and attachment system
- Conversation sorting by recency
- Mode selection interface
- Configurable external storage paths

## Architecture

### Agent Graph Structure

The system implements a LangGraph state machine with the following flow:

1. **Streamlit Interface (app.py)**: User interaction layer
2. **Main Agent Graph (graph.py)**: Central orchestration
3. **Model Node**: Mode-based model selection and prompt generation
4. **Tool Selection**: Conditional routing to appropriate tools
5. **Tool Execution**: Direct tool calls or subagent delegation

### Subagent System

**Search Subagent**: Independent LangGraph agent handling all search operations
- General web search
- Reddit-wide search
- Subreddit-specific search
- BuyItForLife subreddit search

### State Management

Conversations are persisted using PostgreSQL with the following structure:
- Thread ID-based isolation
- Message history storage
- Checkpoint-based state recovery
- File associations per thread

## Modes

| Mode         | Model        | Purpose                                                                     |
| ------------ | ------------ | --------------------------------------------------------------------------- |
| **Personal** | GPT-4o       | Shopping & lifestyle recommendations with Reddit/r/BuyItForLife integration |
| **Work**     | GPT-4o       | Factual research & study assistance, no assumptions                         |
| **Code**     | GPT-4o       | Code creation, debugging & optimization — full output, no fluff             |
| **Fast**     | GPT-4.1-nano | Ultra-fast, minimal responses                                               |

## Architecture

The system is a LangGraph state machine:

1. **Streamlit UI** (`app.py`) → user interaction
2. **Agent Graph** (`graph.py`) → mode-based model selection + prompt injection
3. **Tool routing** → conditional edges to tools or search subagent
4. **State persistence** → PostgreSQL checkpointer with thread-based isolation

### Tools

- `get_weather` — Open-Meteo weather data
- `retrieve_context` — Pinecone vector search for RAG
- `ask_search_agent` — delegates to a **search subagent** with:
  - `general_search` (LinkupClient web search)
  - `reddit_search` (Reddit-wide)
  - `subreddit_search` (targeted subreddit)
  - `buyforlife_search` (r/BuyItForLife scraping via PRAW)

### File Context

Per-conversation file uploads (txt, md, py, json, pdf) are stored in thread-specific directories and automatically injected into the system prompt.

## Project Structure

```
Stumberg/
├── app.py                  # Streamlit interface
├── main.py                 # CLI entry point
├── graph.py                # LangGraph agent graph
├── models.py               # Model configurations
├── prompts.py              # Mode-specific system prompts
├── schema.py               # AgentState definition
├── tools/
│   ├── search.py           # Search tool implementations
│   ├── weather.py          # Weather tool
│   └── vector_search.py    # Pinecone integration
├── subagents/
│   └── search_subagent.py  # Search delegation subgraph
├── middleware/
│   └── call_wrapping.py    # Call wrapping utilities
├── RAG_building_scripts/   # Vector store build utilities
├── Dockerfile
├── requirements.txt
├── langgraph.json          # LangGraph deployment config
└── ROADMAP.md
```

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- OpenAI API key

### Install & Configure

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
# Required
OPENAI_API_KEY=your_key
DB_URI=postgresql://user:password@host:port/database

# Optional
PINECONE_API_KEY=your_key
LINKUP_API_KEY=your_key
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=your_project
CONVERSATION_DATA_PATH=/path/to/conversation/data
```

### Run

```bash
# Streamlit UI
streamlit run app.py

# CLI
python main.py
```

### Docker

```bash
docker build -t stumberg-agent .
docker run -p 8501:8501 \
  -v /path/to/data:/host_e/conversation_data \
  --env-file .env \
  stumberg-agent
```

## License

Personal use and experimentation.
