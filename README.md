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

### Personal Mode
**Purpose**: Shopping and lifestyle recommendations
**Model**: GPT-4o
**Capabilities**:
- Product recommendations prioritizing durability and quality
- Reddit and r/BuyItForLife integration for community insights
- Trade-off analysis between price, quality, and convenience
- Preference inference from user context

### Work Mode
**Purpose**: Research and study assistance
**Model**: GPT-4o
**Capabilities**:
- Factual, up-to-date information retrieval
- Academic and professional research support
- Explicit handling of information gaps (no assumptions)
- Concise, direct responses

### Code Mode
**Purpose**: Programming assistance
**Model**: GPT-4o
**Capabilities**:
- Code creation, modification, debugging, and optimization
- Emphasis on simplicity and readability
- Complete code output (no partial snippets)
- Integration with StackOverflow and documentation searches
- Minimal comments, maximum clarity

### Fast Mode
**Purpose**: Quick information retrieval
**Model**: GPT-4.1-nano
**Capabilities**:
- Ultra-fast response generation
- Succinct, high-density information
- No elaboration or follow-up questions
- Minimal word count

## Tools

### Search Tools (via Search Subagent)

**general_search**: Web search using LinkupClient API
- Standard depth search
- Configurable domain inclusion/exclusion
- Search result format

**reddit_search**: Reddit-wide discussion search
- Domain-limited to reddit.com
- Excludes r/BuyItForLife (handled separately)

**subreddit_search**: Targeted subreddit queries
- User-specified subreddit parameter
- Refined query construction

**buyforlife_search**: r/BuyItForLife scraping via PRAW
- Configurable result limit and sorting
- Post metadata extraction (title, score, comments, timestamp)
- Self-text snippet retrieval

### Direct Tools

**get_weather**: Weather information retrieval
- Open-Meteo API integration
- Location-based queries

**retrieve_context**: Vector database search
- Pinecone semantic search
- Context retrieval for RAG applications

## Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- OpenAI API key

### Optional Dependencies

- Pinecone API key (for vector search)
- LinkupClient API key (for web search)
- Reddit API credentials (for PRAW)
- LangChain API key (for tracing)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
# Required
OPENAI_API_KEY=your_openai_api_key
DB_URI=postgresql://user:password@host:port/database

# Optional
PINECONE_API_KEY=your_pinecone_api_key
LINKUP_API_KEY=your_linkup_api_key
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=your_project_name
CONVERSATION_DATA_PATH=/path/to/conversation/data
```

3. Initialize database:
```bash
python main.py
```

### Docker Deployment

```bash
docker build -t stumberg-agent .
docker run -p 8501:8501 \
  -v /path/to/data:/host_e/conversation_data \
  --env-file .env \
  stumberg-agent
```

## Usage

### Streamlit Interface

Start the web application:
```bash
streamlit run app.py
```

Access at `http://localhost:8501`

### CLI Interface

Run directly via CLI:
```bash
python main.py
```

Edit `main.py` to modify queries.

## Project Structure

```
Stumberg/
├── app.py                  # Streamlit interface
├── main.py                 # CLI entry point
├── graph.py                # LangGraph agent definition
├── models.py               # Model configurations
├── prompts.py              # Mode-specific system prompts
├── schema.py               # AgentState type definition
├── langgraph.json          # LangGraph deployment config
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── tools/
│   ├── search.py           # Search tool implementations
│   ├── weather.py          # Weather tool
│   └── vector_search.py    # Pinecone integration
├── subagents/
│   └── search_subagent.py  # Search delegation graph
├── RAG_building_scripts/   # Vector store utilities
├── ROADMAP.md              # Development roadmap
└── CAPABILITIES.md         # Detailed capabilities
```

## Configuration

### Model Settings (models.py)

- **fast_model**: gpt-4.1-nano, max_tokens=1000, temperature=0.1, timeout=30s
- **main_model**: gpt-4o, max_tokens=1000, temperature=0.1, timeout=60s
- **coding_model**: gpt-4o, max_tokens=1000, temperature=0.1, timeout=60s

### Search Configuration (tools/search.py)

- **LinkupClient**: Standard depth, searchResults output, no images
- **PRAW**: Configurable limit and sort parameters

### Vector Store (tools/vector_search.py)

- Pinecone index-based semantic search
- Requires PINECONE_API_KEY environment variable

## Development

### Design Patterns

**Subagent Architecture**: Specialized subgraphs for complex operations (e.g., search delegation)

**Mode-Based Prompting**: Dynamic system prompt generation based on selected mode

**File Context Injection**: Automatic file content inclusion in system prompts

**State Persistence**: PostgreSQL checkpointer for conversation continuity

### Adding Tools

1. Create tool function in `tools/` directory
2. Decorate with `@tool` from `langchain_core.tools`
3. Add to `tools` list in `graph.py`
4. Bind to model in appropriate mode

### Adding Modes

1. Define mode prompt in `prompts.py` (`get_system_prompt`)
2. Add mode logic in `graph.py` (`model_node`)
3. Create UI button in `app.py`

### LangSmith Tracing

Enabled by default for debugging. Configure via:
- `LANGCHAIN_TRACING=true` (set in main.py)
- `LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com`
- `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT` in .env

## Dependencies

Key packages from requirements.txt:

- langchain >= 1.1.0
- langgraph >= 1.0.4
- langgraph-checkpoint-postgres
- langchain-openai >= 1.1.0
- langchain-pinecone >= 0.2.13
- streamlit >= 1.51.0
- psycopg[binary,pool] >= 3.2.0
- pinecone >= 7.3.0
- linkup-sdk >= 0.9.0
- praw >= 7.8.0
- beautifulsoup4 == 4.12.3
- pypdf >= 6.4.0
- playwright >= 1.56.0

## Acknowledgments

Built with: LangGraph, LangChain, Streamlit, OpenAI, Pinecone, LinkupClient, PRAW, PostgreSQL

## License

Personal use and experimentation.
