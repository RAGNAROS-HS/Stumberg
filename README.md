# Stumberg Agent

A modular, multi-mode AI assistant built with **LangGraph** and **LangChain**. Provides context-aware responses through a Streamlit web interface with specialized modes for shopping, research, coding, and fast information retrieval.

## Tech Stack

| Layer         | Technology                              |
| ------------- | --------------------------------------- |
| Orchestration | LangGraph + LangChain                   |
| UI            | Streamlit                               |
| Models        | GPT-4o (main/code), GPT-4.1-nano (fast) |
| Persistence   | PostgreSQL (conversation checkpoints)   |
| Vector Search | Pinecone                                |
| Web Search    | LinkupClient                            |
| Reddit        | PRAW                                    |
| Weather       | Open-Meteo API                          |
| Tracing       | LangSmith (optional)                    |

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
