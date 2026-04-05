# Stumberg V2 — Implementation Guide for Claude Code

This document is the authoritative guide for implementing Stumberg V2 from scratch. Read it completely before writing any code. Every section is load-bearing — do not skip the workflow rules, test criteria, or non-negotiables.

---

## How to Use This Document

Work through the phases in order. Each phase has a clear goal, a list of files to create or modify, acceptance criteria you must verify before closing the PR, and the exact branch name and commit type to use. Do not start a phase until all acceptance criteria for the previous phase are met.

**Each phase must be implemented inside a git worktree.** Before writing any code for a phase, use the `EnterWorktree` tool (or invoke a sub-agent with `isolation: "worktree"`) to check out an isolated copy of the repo. This keeps `main` clean, makes the diff reviewable before merging, and allows the acceptance criteria to be verified in isolation before the PR is opened.

Workflow per phase:
1. Enter a worktree on the phase branch (e.g., `phase/1-backend-foundation`)
2. Implement everything listed in the phase's file manifest
3. Verify all acceptance criteria pass inside the worktree
4. Commit with the correct conventional commit format
5. Open the PR from the worktree branch — do not merge until criteria pass
6. Exit the worktree; squash-merge to `main`

When in doubt about scope: stop and ask. Do not add features, speculative abstractions, or "improvements" not listed here.

---

## Product Context (Read Once, Then Refer Back Only As Needed)

Stumberg is a personal AI assistant for one user. Two jobs only:

1. **Fast mode** — answer questions in one sentence. No fluff. Cheap model. Minimal tools.
2. **Personal mode** — personalized recommendations for shopping, food, lifestyle. Searches before recommending. Applies stored user preferences automatically.

The defining feature of V2 is **persistent user memory**: a profile that accumulates across conversations and visibly improves Personal mode recommendations over time.

Priorities in order: response quality → speed → memory → reliability.

---

## Git Workflow

Follow these rules on every phase.

### Worktrees (required)

Every phase is implemented in a dedicated git worktree — never directly on `main`.

```
# Claude Code: use the EnterWorktree tool before writing any code
# Or, when delegating to a sub-agent:
#   Agent(subagent_type="general-purpose", isolation="worktree", ...)
```

The worktree is created on the phase branch. All file edits, test runs, and commits happen inside it. If the phase produces no changes (e.g., the acceptance criteria already pass from a prior phase), the worktree is discarded without merging.

### Branch naming
```
phase/<N>-<short-slug>
```
Examples: `phase/1-backend-foundation`, `phase/3-fast-mode`

### Commit messages
Use [Conventional Commits](https://www.conventionalcommits.org/). Type prefix required. Subject ≤72 chars. Body only when the why is non-obvious.

```
feat: add SSE streaming endpoint for chat
fix: handle missing ANTHROPIC_API_KEY gracefully
chore: add docker-compose with postgres and redis
refactor: move config loading to config.py
test: add smoke test for fast agent graph
```

### Pull requests
One PR per phase. PR title mirrors the phase goal. PR body must include:
- **What this adds** (bullet list of deliverables)
- **How to test** (exact commands or manual steps)
- **Non-obvious decisions** (anything a reviewer would question)

Never open a PR for a phase until all acceptance criteria pass locally.

### Merging
Squash-merge to `main`. The squash commit message is the PR title in conventional commit format.

### What never goes in a commit
- Secrets, API keys, tokens, `.env` files
- Dead code, commented-out blocks, unused imports
- `print()` statements (use `logging`)
- Files not listed in the phase's file manifest

---

## Architecture Reference

Keep this in mind throughout all phases. Do not deviate from it.

### Stack
- **Backend**: FastAPI + LangGraph (Python)
- **Frontend**: Next.js (TypeScript)
- **DB**: PostgreSQL with pgvector extension
- **Cache**: Redis (optional, graceful degradation)
- **Telegram**: thin bot client, all logic in FastAPI

### Graph topology
```
START
  └─► route_node
        ├─► fast_agent_node ──► [tools_condition] ──► fast_tool_node ──► fast_agent_node ──► END
        └─► summarize_node (conditional) ──► personal_agent_node ──► [tools_condition] ──► personal_tool_node ──► personal_agent_node ──► END
                                                                                                                    ↑
                                                                                              memory extraction fires as FastAPI background task after stream closes
```

### State schema (`AgentState`)
| Field | Type | Notes |
|---|---|---|
| `messages` | `Annotated[list, add_messages]` | Full conversation history |
| `mode` | `Literal["fast", "personal"]` | Persisted per thread |
| `summary` | `str` | Rolling summary of old messages; empty string when unused |

`attached_files` is NOT in state — loaded from `thread_files` table by `thread_id` at invocation time.

### Models
| Name | Model | Used by |
|---|---|---|
| `fast_model` | `gpt-4.1-mini` | Fast agent, both subagents, memory extractor |
| `main_model` | Claude Sonnet (fallback: `gpt-4o`) | Personal agent |
| `reasoning_model` | `o3` or Claude extended thinking | Optional; personal agent only, on judgement |

No `max_tokens` cap on any model. Ever.

### Subagents
Two subagents, each compiled as a standalone LangGraph graph and exposed as a `@tool` wrapper:
- **Search subagent** — receives enriched query, decides which search tools to call, returns synthesized summary + source URLs
- **Shopping subagent** — receives `{query, budget, relevant_preferences}`, runs full workflow (search → price comparison → price history → coupons → synthesize), returns structured recommendation JSON

Single-call tools (weather, nutrition, restaurant, profile read/write, lifestyle) are direct tool calls on the main agent — no subagent.

### Databases
| Table | Purpose |
|---|---|
| LangGraph checkpointer tables | Conversation state per `thread_id` |
| `user_profile` | Memory entries: `(id, category, description, embedding vector, created_at, season)` |
| `thread_files` | Attached file content per thread: `(thread_id, filename, content, uploaded_at)` |

### Config
Load from environment. Fail fast with clear error on missing required vars. Gracefully degrade on missing optional vars. All config lives in `backend/config.py`. No other file reads `os.environ` directly.

Required: `OPENAI_API_KEY`, `DB_URI`  
Optional: `ANTHROPIC_API_KEY`, `LINKUP_API_KEY`, `TELEGRAM_BOT_TOKEN`, `REDIS_URL`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`

---

## File Structure (Target State)

```
stumberg/
├── backend/
│   ├── main.py               # FastAPI app, lifespan, routes, SSE, Telegram webhook
│   ├── bot.py                # Telegram bot logic (thin client)
│   ├── scheduler.py          # APScheduler jobs
│   ├── config.py             # Env var loading and validation
│   ├── graph.py              # LangGraph graph definition
│   ├── schema.py             # AgentState TypedDict
│   ├── models.py             # LLM client instances
│   ├── prompts.py            # System prompts per mode
│   ├── memory.py             # User profile table setup, read/write helpers
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py         # Linkup: general, reddit, subreddit, buyforlife
│   │   ├── weather.py        # Open-Meteo (no API key)
│   │   ├── shopping.py       # Price comparison, price history, coupons, barcode lookup
│   │   ├── food.py           # OpenFoodFacts nutrition, recipe search, restaurant finder
│   │   ├── lifestyle.py      # Activity recommendations, product ownership tracker
│   │   └── profile.py        # get_user_profile, update_user_memory
│   ├── subagents/
│   │   ├── search_subagent.py
│   │   ├── shopping_subagent.py
│   │   └── memory_extractor.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Redirects to /chat
│   │   ├── chat/page.tsx     # Main chat UI
│   │   └── profile/page.tsx  # Profile viewer/editor
│   ├── components/
│   │   ├── ChatThread.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── RecommendationCard.tsx
│   │   ├── Sidebar.tsx
│   │   ├── FilePanel.tsx
│   │   └── ToolStatus.tsx
│   ├── lib/api.ts
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── .gitignore
```

---

## Implementation Phases

---

### Phase 0 — Repo Scaffold & Infrastructure

**Goal**: A runnable local environment with Postgres + Redis, a committed `.env.example`, and the target directory structure in place. No application logic yet.

**Branch**: `phase/0-scaffold`

**Files to create**:
- `docker-compose.yml` — services: `postgres` (with pgvector), `redis`, `backend` (stub), `frontend` (stub)
- `Dockerfile.backend` — Python 3.12 slim, install requirements
- `Dockerfile.frontend` — Node 20 alpine, install deps
- `.env.example` — all env vars listed with placeholder values, comments on which are required vs optional
- `.gitignore` — ignore `.env`, `__pycache__`, `node_modules`, `.next`, `*.pyc`
- `backend/requirements.txt` — pinned dependencies: `fastapi`, `uvicorn`, `langgraph`, `langchain`, `langchain-openai`, `langchain-anthropic`, `psycopg[binary,pool]`, `langgraph-checkpoint-postgres`, `pgvector`, `redis`, `apscheduler`, `python-telegram-bot`, `linkup-sdk`, `pypdf2`, `python-dotenv`
- `backend/config.py` — load env vars, validate required keys at import time, raise `RuntimeError` with clear message if missing
- `backend/__init__.py`, `backend/tools/__init__.py`, `backend/subagents/__init__.py`
- `frontend/package.json` — Next.js 14, TypeScript, Tailwind
- `frontend/tsconfig.json`

**Acceptance criteria**:
- `docker-compose up` starts all four services without errors
- Postgres is reachable at `DB_URI` from outside the container
- Redis is reachable at `REDIS_URL`
- `python -c "from backend.config import config"` exits 0 when all required vars are set
- `python -c "from backend.config import config"` raises `RuntimeError` with the missing var name when `OPENAI_API_KEY` is unset
- `.env` is not tracked by git (`git status` shows clean after adding a `.env` file)

**PR title**: `chore: scaffold project structure and local dev infrastructure`

---

### Phase 1 — Backend Foundation

**Goal**: A FastAPI application that starts, connects to Postgres, and has the DB tables initialized. No agent logic yet — just the server skeleton.

**Branch**: `phase/1-backend-foundation`

**Files to create/modify**:
- `backend/main.py` — FastAPI app with lifespan context manager. In lifespan: initialize DB connection pool, run `checkpointer.setup()`, create `user_profile` and `thread_files` tables (via `memory.py`). Log startup completion.
- `backend/memory.py` — `setup_tables(conn)` that creates `user_profile` (id, category, description, embedding vector(1536), created_at, season) and `thread_files` (thread_id, filename, content, uploaded_at). Also `get_profile_entries(conn, query_embedding, limit)` and `write_profile_entry(conn, category, description, embedding)` stubs (full logic in Phase 4).
- `backend/schema.py` — `AgentState` TypedDict: `messages`, `mode`, `summary`
- `backend/models.py` — instantiate `fast_model`, `main_model`, `reasoning_model`. `main_model` uses Anthropic if `ANTHROPIC_API_KEY` is present, otherwise falls back to GPT-4o. Log which model is used for `main_model` at startup.

**Acceptance criteria**:
- `uvicorn backend.main:app --reload` starts without errors when all required env vars are set
- `GET /health` returns `{"status": "ok"}`
- `user_profile` and `thread_files` tables exist in Postgres after startup (verify with `psql`)
- Starting without `ANTHROPIC_API_KEY` logs "Anthropic key absent, Personal mode using GPT-4o" and continues
- Starting without `OPENAI_API_KEY` raises `RuntimeError` before the server binds

**PR title**: `feat: FastAPI app skeleton with DB initialization and model setup`

---

### Phase 2 — Core Graph (Routing + Fast Agent)

**Goal**: The LangGraph graph with `route_node`, `fast_agent_node`, and the state schema wired up. Fast mode works end-to-end for simple factual questions with no tools. Personal mode stub routes correctly but returns a placeholder.

**Branch**: `phase/2-core-graph`

**Files to create/modify**:
- `backend/graph.py` — define `StateGraph(AgentState)`. Add `route_node` (reads `state["mode"]`, routes to `fast_agent_node` or `personal_agent_node`). Add `fast_agent_node` (uses `fast_model`, no tools yet, recursion limit 4). Add `personal_agent_node` stub (returns placeholder message). Compile with `PostgresSaver`. Export `graph`.
- `backend/prompts.py` — `get_system_prompt(mode: str) -> str`. Fast mode: terse factual assistant, one sentence if possible, no intro. Personal mode: recommendation assistant with user memory injection placeholder.
- `backend/main.py` — add `POST /chat` route that invokes `graph.ainvoke()` and returns the last AI message. (Streaming added in Phase 5.)

**Acceptance criteria**:
- `POST /chat` with `{"thread_id": "t1", "mode": "fast", "message": "What is 2+2?"}` returns a short answer containing "4"
- `POST /chat` with `mode: "personal"` returns the placeholder string "Personal mode not yet implemented"
- Thread state persists: sending a follow-up in the same `thread_id` includes prior messages in context (verify by asking "what did I just ask?" after an initial question)
- `graph.py` has no `max_tokens` on any model call
- No `print()` statements; logging only

**PR title**: `feat: LangGraph graph with routing and functional fast agent node`

---

### Phase 3 — Fast Mode: Tools

**Goal**: Fast mode has its full tool set — weather and search subagent. The search subagent is a standalone graph delegating to Linkup tools.

**Branch**: `phase/3-fast-tools`

**Files to create/modify**:
- `backend/tools/weather.py` — `get_weather(location: str) -> str` tool using Open-Meteo API (no key required). Returns current conditions and temperature.
- `backend/tools/search.py` — four Linkup-backed tools: `general_search(query)`, `reddit_search(query)`, `subreddit_search(query, subreddit)`, `buyforlife_search(query)`. If `LINKUP_API_KEY` is absent, each tool returns `"Search unavailable: LINKUP_API_KEY not set"` — do not raise.
- `backend/subagents/search_subagent.py` — `SearchAgentState` (messages only). Graph: `search_agent_node` (fast_model + all four search tools) → tools_condition → tool_node → back to agent. Compile. Expose as `ask_search_agent(query: str) -> str` tool that invokes the subgraph and returns the last AI message.
- `backend/graph.py` — bind `get_weather` and `ask_search_agent` to `fast_agent_node`. Apply recursion limit of 4. Fast agent system prompt instructs: use search only when question requires current information; use training knowledge otherwise.

**Acceptance criteria**:
- `POST /chat` with `mode: fast`, message `"What's the weather in Oslo?"` calls `get_weather` and returns current conditions
- `POST /chat` with `mode: fast`, message `"What year was the Eiffel Tower built?"` answers from training data without calling any tool (verify via LangSmith trace or log)
- `POST /chat` with `mode: fast`, message `"Find Reddit opinions on Uniqlo merino wool"` calls `ask_search_agent`, which internally calls `reddit_search`, and returns a synthesized response
- When `LINKUP_API_KEY` is absent, Fast mode still answers factual questions; search queries return the degraded message and the agent states it cannot search
- All four Linkup tools are registered on the search subagent only — not directly on the fast agent

**PR title**: `feat: fast mode tools — weather, search subagent with Linkup`

---

### Phase 4 — User Memory System

**Goal**: The `user_profile` table is live with pgvector similarity search. `get_user_profile` and `update_user_memory` tools work. A user can read and write profile entries via the API.

**Branch**: `phase/4-user-memory`

**Files to create/modify**:
- `backend/memory.py` — implement `get_profile_entries(conn, query_embedding, limit=10)` using pgvector `<=>` operator for cosine similarity. Implement `write_profile_entry(conn, category, description, embedding, season)`. Embeddings generated via OpenAI `text-embedding-3-small`.
- `backend/tools/profile.py` — `get_user_profile(query: str) -> str` tool: generates embedding from query, calls `get_profile_entries`, formats results as readable text. `update_user_memory(category: str, description: str) -> str` tool: generates embedding, calls `write_profile_entry`. Categories must be one of `preference`, `constraint`, `feedback`.
- `backend/main.py` — add `GET /profile` (returns all profile entries, sorted by `created_at` desc) and `DELETE /profile/{entry_id}` routes.

**Acceptance criteria**:
- `POST /profile/entry` with `{"category": "preference", "description": "prefers merino wool over synthetic fabrics"}` inserts a row in `user_profile` with a non-null embedding vector
- `GET /profile` returns the inserted entry
- `GET /profile/search?q=fabric preferences` returns the merino entry ranked first (cosine similarity)
- `DELETE /profile/{id}` removes the entry
- Querying with a semantically unrelated string (e.g., `q=weather in Oslo`) does not return the merino entry in position 1
- `update_user_memory` called with an invalid category raises a `ValueError` before writing

**PR title**: `feat: user memory system with pgvector semantic search`

---

### Phase 5 — Personal Mode: Agent + Streaming

**Goal**: Personal mode is fully functional. The personal agent node injects relevant user profile entries, has the full tool set, and responses stream via SSE. The summarization node fires correctly on long threads.

**Branch**: `phase/5-personal-mode`

**Files to create/modify**:
- `backend/graph.py`:
  - Add `summarize_node`: runs when `len(state["messages"]) > 20` and `state["summary"]` is stale. Uses `fast_model` to compress old messages into a rolling summary. Stores result in `state["summary"]`. Old messages truncated to the summary + last 5 messages.
  - Implement `personal_agent_node`: loads relevant profile entries via `get_user_profile` (semantic search against the current query), prepends to system prompt, uses `main_model`, recursion limit 10. Binds tools: `get_user_profile`, `update_user_memory`, `get_weather`, `ask_search_agent`.
  - Wire `summarize_node` → `personal_agent_node` in the graph with correct conditional edge.
- `backend/main.py` — replace `POST /chat` synchronous invoke with SSE streaming via `astream_events`. Stream `on_chat_model_stream` events as `data: {"token": "..."}`. Stream `on_tool_start` events as `data: {"tool_status": "Searching Reddit..."}`. End stream with `data: {"done": true}`.

**Tool status messages** (shown during tool calls):
- `ask_search_agent` → `"Searching..."`
- `ask_shopping_agent` → `"Comparing prices..."`
- `get_weather` → `"Checking weather..."`
- `get_user_profile` → `"Reading your profile..."`

**Acceptance criteria**:
- `POST /chat` (SSE) with `mode: personal`, `"recommend a durable winter jacket under €200"` streams tokens progressively — first token arrives before full response is ready
- After inserting a preference entry (`"prefers merino wool"`), a fresh personal mode query about clothing applies that constraint without the user stating it (visible in the response text)
- After 21+ messages in a thread, `summarize_node` fires once and stores a non-empty `state["summary"]`; subsequent messages use the summary and the last 5 messages
- Tool status SSE events appear before the token stream begins
- Fast mode path does not call `summarize_node` or `get_user_profile`

**PR title**: `feat: personal agent node with profile injection, summarization, and SSE streaming`

---

### Phase 6 — Shopping & Lifestyle Tools + Shopping Subagent

**Goal**: Personal mode has the full specialized tool set: Shopping subagent (price comparison, history, coupons), food tools, and lifestyle tools.

**Branch**: `phase/6-specialized-tools`

**Files to create/modify**:
- `backend/tools/shopping.py`:
  - `compare_prices(product: str) -> str` — query major retailers via Linkup, return ranked price list
  - `price_history(product: str, retailer: str) -> str` — return historical price trend summary
  - `find_coupons(product_or_retailer: str) -> str` — return active discount codes
  - `barcode_lookup(barcode: str) -> str` — return product name, specs, pricing context
- `backend/subagents/shopping_subagent.py` — `ShoppingAgentState` (messages only). Graph runs: search → price_comparison → price_history → coupon_finder → synthesize. Expose as `ask_shopping_agent(query: str, budget: str, preferences: str) -> str` tool returning structured JSON: `{best_pick: {...}, alternatives: [{...}], deal_quality: "..."}`.
- `backend/tools/food.py`:
  - `nutrition_lookup(food_item: str) -> str` — OpenFoodFacts API, no key required
  - `recipe_search(ingredients: str, dietary_constraints: str) -> str` — Linkup-based
  - `restaurant_finder(location: str, dietary_preferences: str) -> str` — Linkup-based
- `backend/tools/lifestyle.py`:
  - `activity_recommendations(constraints: str) -> str` — calls weather tool internally, returns activity suggestions
  - `log_owned_product(product_name: str, purchase_date: str) -> str` — writes to `user_profile` as `feedback` category entry
  - `get_owned_products() -> str` — returns list of logged owned products
- `backend/graph.py` — bind all new tools to `personal_agent_node`. Add `ask_shopping_agent` to personal tools.

**Acceptance criteria**:
- `POST /chat` (SSE), `mode: personal`, `"find me a good mechanical keyboard under €100"` invokes `ask_shopping_agent`, which internally runs the full shopping workflow, and the response includes a ranked recommendation with price and retailer
- `POST /chat`, `"nutrition info for Greek yogurt"` calls `nutrition_lookup` and returns macro data
- `POST /chat`, `"log that I own a Bellroy wallet, bought last month"` calls `log_owned_product` and confirms storage
- A follow-up `"what products do I own?"` calls `get_owned_products` and lists the Bellroy wallet
- Shopping subagent tools are not directly accessible from the fast agent

**PR title**: `feat: shopping subagent, food tools, and lifestyle tools for personal mode`

---

### Phase 7 — Memory Extraction Background Task

**Goal**: After every Personal mode response, a lightweight background task reviews the exchange and writes any new preference/constraint/feedback entries to `user_profile` automatically.

**Branch**: `phase/7-memory-extraction`

**Files to create/modify**:
- `backend/subagents/memory_extractor.py` — `extract_memories(conversation: list[dict]) -> list[dict]` function (not a graph — a direct LLM call). Uses `fast_model`. Prompt: given the conversation excerpt, identify any new preferences, constraints, or feedback signals. Return as JSON array `[{category, description}]`. Empty array if nothing worth storing.
- `backend/main.py` — after the SSE stream closes, schedule `extract_and_store_memories(thread_id, conversation)` as a FastAPI `BackgroundTask`. This calls `extract_memories`, then calls `write_profile_entry` for each result. Runs after response delivery — zero latency impact.

**Test cases to verify extraction logic** (manual, via curl or Python script):
| Conversation excerpt | Expected extracted entry |
|---|---|
| User: "I hate synthetic fabrics, always give me natural materials" | `{category: "preference", description: "dislikes synthetic fabrics, prefers natural materials"}` |
| User: "I bought the jacket you recommended, loved it" | `{category: "feedback", description: "bought and loved recommended jacket"}` |
| User: "my budget for headphones is max €80" | `{category: "constraint", description: "budget ceiling for headphones: €80"}` |
| User: "what's 2+2?" (Fast mode conversation) | `[]` — extractor not called for Fast mode |

**Acceptance criteria**:
- A Personal mode conversation containing `"I'm vegetarian"` results in a new `user_profile` entry with `category=constraint` and description mentioning vegetarian within 5 seconds of the response ending
- The background task does not block the SSE stream — the stream closes normally and the extraction runs after
- Fast mode conversations do not trigger extraction
- Extractor runs once per response, not per token

**PR title**: `feat: background memory extraction after personal mode responses`

---

### Phase 8 — Next.js Frontend: Chat + Streaming

**Goal**: A functional web UI with a chat thread, SSE streaming rendering, mode toggle, and thread sidebar. No recommendation cards yet — plain text rendering only.

**Branch**: `phase/8-frontend-core`

**Files to create/modify**:
- `frontend/lib/api.ts` — `streamChat(params): AsyncGenerator` consuming the SSE stream. `getThreads()`, `createThread()` REST calls.
- `frontend/components/ChatThread.tsx` — renders message list. New tokens appended in real-time during streaming. Displays tool status messages while tools run.
- `frontend/components/MessageBubble.tsx` — single message: user bubble (right-aligned) or assistant bubble (left-aligned). Plain text for now.
- `frontend/components/ToolStatus.tsx` — inline indicator showing tool status text during tool calls (e.g., "Searching Reddit..."). Disappears when streaming begins.
- `frontend/components/Sidebar.tsx` — thread list sorted by most recent activity, thread titles from first message (≤40 chars), "New Chat" button, mode toggle (Fast / Personal).
- `frontend/app/chat/page.tsx` — assembles all components. Handles `thread_id` in URL params.
- `frontend/app/page.tsx` — redirects to `/chat`.

**Acceptance criteria**:
- Loading `/chat` shows an empty thread with a text input
- Sending "What is the capital of France?" in Fast mode streams the response token by token — text visibly appears progressively
- Mode toggle switches between Fast and Personal; the active mode is visually indicated
- Starting a new chat creates a new thread; the old thread appears in the sidebar
- Refreshing the page and clicking a past thread restores its message history
- Tool status text (e.g., "Searching...") appears and then is replaced by the streaming response

**PR title**: `feat: Next.js chat frontend with SSE streaming and thread sidebar`

---

### Phase 9 — Frontend: Recommendation Cards, Feedback Buttons, File Attachments, Profile Viewer

**Goal**: Personal mode renders structured recommendation cards. Feedback buttons appear on every Personal response. File uploads work. The profile page shows stored memories.

**Branch**: `phase/9-frontend-complete`

**Files to create/modify**:
- `backend/main.py` — add `POST /files/{thread_id}` (upload file, extract PDF text, store in `thread_files`), `GET /files/{thread_id}` (list files), `DELETE /files/{thread_id}/{filename}`. Inject file content into personal agent's system prompt at invocation time (load from `thread_files` by `thread_id`).
- `frontend/components/RecommendationCard.tsx` — renders the structured JSON from `ask_shopping_agent`: product name, price, retailer link, one-line reason, preference match indicator. Thumbs up / thumbs down / "I bought it" buttons below the card. Clicking a button sends `POST /feedback` with `{thread_id, message_id, signal: "up"|"down"|"purchased"}`.
- `backend/main.py` — add `POST /feedback` route that calls `write_profile_entry` with the appropriate feedback category.
- `frontend/components/MessageBubble.tsx` — detect if message content is recommendation JSON (starts with `{`), render as `RecommendationCard` if so, otherwise plain text.
- `frontend/components/FilePanel.tsx` — upload button (accepts txt, md, json, pdf), list of uploaded files with delete buttons. Integrated into `Sidebar.tsx`.
- `frontend/app/profile/page.tsx` — fetches `GET /profile`, renders grouped by category (Preferences, Constraints, Feedback). Each entry has a delete button (`DELETE /profile/{id}`).

**Acceptance criteria**:
- A Personal mode recommendation response (from shopping subagent) renders as a card with product name, price, and clickable retailer link
- Thumbs down button on a card sends a feedback entry visible in `/profile`
- Uploading a `.txt` file to a thread and then asking a question about its content produces an answer that uses the file content
- Uploading a `.pdf` extracts text and behaves the same as `.txt`
- `/profile` page lists all stored entries grouped by category
- Deleting an entry on `/profile` removes it from the list without a page refresh

**PR title**: `feat: recommendation cards, feedback buttons, file attachments, profile viewer`

---

### Phase 10 — Telegram Bot

**Goal**: A working Telegram bot that handles Fast mode as the default and Personal mode via `/personal` prefix. All logic goes through FastAPI — the bot is a thin relay.

**Branch**: `phase/10-telegram`

**Files to create/modify**:
- `backend/bot.py` — `python-telegram-bot` application. On receiving a message: strip `/personal` prefix to determine mode, call `POST /chat` (SSE stream), edit the Telegram message progressively as tokens arrive (Telegram's `editMessageText` pattern). Handle `/start` with a brief description. Handle `/forget` as a shortcut to clear profile.
- `backend/main.py` — register `POST /webhook/telegram` endpoint. In lifespan, set Telegram webhook URL if `TELEGRAM_BOT_TOKEN` is present; skip silently if absent.

**Acceptance criteria**:
- Sending "what is 2+2?" in Telegram returns a correct Fast mode answer in under 5 seconds
- Sending `/personal recommend a durable leather belt` triggers Personal mode and returns a recommendation (may be slower)
- Messages stream progressively via Telegram message edits (send, then edit as tokens arrive)
- Without `TELEGRAM_BOT_TOKEN`, the backend starts normally and `/webhook/telegram` returns 404

**PR title**: `feat: Telegram bot as thin client for fast and personal mode`

---

### Phase 11 — Scheduler: Follow-ups and Price Watching

**Goal**: APScheduler runs inside the FastAPI process. Two jobs: follow-up messages (send a Telegram message N days after a recommendation) and price-watch notifications.

**Branch**: `phase/11-scheduler`

**Files to create/modify**:
- `backend/scheduler.py` — `AsyncIOScheduler` initialized in the FastAPI lifespan. Two job types:
  - `schedule_followup(thread_id, product_name, delay_days)` — sends a Telegram message after `delay_days` asking how the recommendation worked out. Writes result to `user_profile` as feedback.
  - `schedule_price_watch(product_name, target_price, chat_id)` — polls price comparison tool on a configurable interval; sends Telegram alert if price drops below threshold.
- `backend/main.py` — `POST /scheduler/followup` and `POST /scheduler/pricewatch` routes. Both require `TELEGRAM_BOT_TOKEN` to be set.

**Acceptance criteria**:
- `POST /scheduler/followup` with `delay_days: 0` (immediate) sends a Telegram message within 10 seconds
- `POST /scheduler/pricewatch` creates a job visible in APScheduler job list
- Without `TELEGRAM_BOT_TOKEN`, both routes return `503 Service Unavailable` with `{"error": "Telegram not configured"}`
- Scheduler does not prevent clean server shutdown

**PR title**: `feat: APScheduler jobs for follow-up messages and price watch notifications`

---

### Phase 12 — Hardening & Cleanup

**Goal**: The app is production-ready. All graceful degradation paths tested. No dead code. Docker build is clean. `.env.example` is complete.

**Branch**: `phase/12-hardening`

**Checklist** (all must pass before PR):

**Startup tests** (run each with the env var absent or set to an invalid value):
- [ ] `OPENAI_API_KEY` missing → server refuses to start with clear error
- [ ] `DB_URI` missing → server refuses to start with clear error
- [ ] `ANTHROPIC_API_KEY` missing → Personal mode uses GPT-4o, logs warning at startup
- [ ] `LINKUP_API_KEY` missing → search tools return degraded message, app continues
- [ ] `REDIS_URL` missing → search caching disabled, app continues
- [ ] `TELEGRAM_BOT_TOKEN` missing → bot disabled, webhook route returns 404

**Functional smoke tests** (via curl or pytest):
- [ ] Fast mode: factual question answered correctly
- [ ] Fast mode: weather query calls Open-Meteo
- [ ] Fast mode: search query calls search subagent (requires `LINKUP_API_KEY`)
- [ ] Personal mode: recommendation query injects profile, calls shopping subagent
- [ ] Personal mode: memory is extracted and stored after a conversation containing a preference statement
- [ ] Profile: write, read, semantic search, delete all work
- [ ] Thread: history persists across server restart

**Code quality**:
- [ ] Zero `print()` statements in Python code
- [ ] Zero hardcoded secrets, paths, or model names outside `config.py` and `models.py`
- [ ] Zero dead code (unused functions, commented-out blocks, unused imports)
- [ ] `requirements.txt` has pinned versions for all dependencies
- [ ] `docker-compose up --build` produces a working stack from a clean clone with only a `.env` file

**PR title**: `chore: hardening, graceful degradation tests, and cleanup`

---

## Non-Negotiables

These are constraints that cannot be traded off against delivery speed. If implementing something would require violating one of these, stop and flag it before proceeding.

- **Two modes only.** No Work mode, no Code mode, no Study mode. Do not add them.
- **Never truncate output.** No `max_tokens` cap anywhere.
- **All responses stream.** No blocking `.invoke()` in any UI-facing code path.
- **Memory is transparent.** The user can always see, edit, and delete what is stored.
- **The bot is a thin client.** No graph calls from `bot.py` — everything through FastAPI.
- **No dead code.** If it is not used, delete it.
- **No hardcoded secrets.** Every key, path, and model name lives in `.env`.
- **Graceful degradation.** Missing optional keys reduce capability, they do not crash the app.
- **`docker-compose up` is the only setup step.** No manual DB or Redis setup.
- **Conventional Commits on every commit.** No exceptions.
- **No Streamlit.** It is gone. Do not reference it.
