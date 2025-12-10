# System Capabilities & Implementation Status

## Core Agent
- **Framework**: Built on `LangGraph` and `LangChain`.
- **Persistence**: Uses `PostgresSaver` for state persistence (requires PostgreSQL).
- **Graph Structure**: Standard message-passing agent.

## Interfaces
- **Web UI**: Streamlit application (`app.py`) for interactive chat.
  - Features: Session management, unique thread generation.
- **CLI**: Legacy command-line execution support via `main.py` (if run directly).

## Tools
- **Weather**: Fetches current weather using Open-Meteo API (`tools/weather.py`).
- **Search**: Basic placeholder for information retrieval (`tools/search.py`).

## Middleware
Located in `middleware/`:
1.  **Role Inference** (`role.py`): Dynamically adjusts the system prompt based on user query complexity (e.g., "explain simply" vs. "advanced").
2.  **Model Selection** (`selection.py`): Routes requests to different models (`gpt-4.1-nano` vs `gpt-4o`) based on context length (currently set to switch after 10 messages).
3.  **Error Handling** (`error.py`): Catches tool execution errors and feeds them back to the model as observations.

## Configuration
- **Models** (`models.py`): 
  - Basic: `gpt-4.1-nano`
  - Advanced: `gpt-4o`
- **Schema** (`schema.py`): Type definitions for agent state context.
- **Environment**: Managed via `.env` (API keys, DB URI).

## Infrastructure
- **Docker**: Containerized environment for reproducible runs.
- **Dependencies**: Managed via `requirements.txt`.
