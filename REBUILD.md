# Stumberg V2 — Product Spec

This document defines what Stumberg V2 should be, what it should do, and how it should be structured.
It is written to be read by Claude Code at the start of a fresh implementation.

---

## What This Project Is

Stumberg is a personal AI assistant built for one person. It has two jobs:

1. **Answer questions fast** — factual lookups, quick calculations, brief explanations. Minimal output, no fluff.
2. **Give personalized recommendations** — shopping, diet, lifestyle, products. Based on what the user actually likes, not generic advice.

It is not a general-purpose chatbot. It is not a coding assistant. It is not a study tool. Scope creep into those areas should be actively resisted.

The defining feature beyond the two modes is **memory of user preferences**. The agent should get better at Personal recommendations the more it's used. It should know what you like without being told every time.

Priorities in order:
1. **Response quality** — recommendations are personalized and grounded in real sources, not generic
2. **Speed** — Fast mode responses appear immediately via streaming
3. **Memory** — preferences accumulate across conversations and visibly improve recommendations over time
4. **Reliability** — the app starts cleanly, fails loudly on missing config, degrades gracefully on missing optional services

---

## Modes

There are exactly two modes. No others.

### Fast Mode

The default. A stripped-down factual assistant.

- Answers are as short as possible — one sentence if the question allows it
- No intro, no follow-up questions, no elaboration unless the prompt implies it
- Uses a cheap, fast model
- Does not search unless the question clearly requires current information (e.g., today's price, current weather)
- Does not consult user preferences — it's a lookup tool, not a recommendation engine

**When it uses tools:** Weather queries (always), factual questions about recent events or prices (model's judgement). For everything else it answers from training data.

### Personal Mode

A recommendation and lifestyle assistant that knows the user.

- Gives ranked, opinionated recommendations — not "it depends" non-answers
- Always searches before recommending products (prices change, new options exist)
- Heavily weighted toward Reddit (real user opinions) and r/BuyItForLife (durability focus) for product queries
- Surfaces the single best option clearly, with 2–3 alternatives and a brief reason for each
- Applies known user preferences automatically — if the user dislikes synthetic fabrics, that constraint is applied without being stated
- Flags relevant discounts or cheaper alternatives when found
- Hard constraints from the user (budget, dietary restrictions, allergies) are never violated

**When it uses tools:** Almost always for product and food queries. Weather for outdoor activity recommendations. User memory for preference retrieval.

---

## User Memory — The Core New Feature

This is the most important thing V2 adds that V1 never had. The agent should **build a persistent profile of the user** across all conversations and use it automatically in Personal mode.

### What Gets Remembered

Three categories:

**Preferences** — things the user likes or dislikes, with context.
Examples: prefers natural fabrics, dislikes overly sweet food, likes minimalist design, owns a dog, is vegetarian, has a knee injury that limits certain exercises, prefers brands that are repairable.

**Constraints** — hard limits that must never be violated.
Examples: budget ceiling for a category (under €X for headphones), dietary restrictions, allergies.

**Past recommendations** — what was recommended and whether the user accepted, rejected, or expressed an opinion on it. This is the feedback signal that improves future recommendations.

### How Memory Is Stored

User memory lives in a dedicated `user_profile` table in PostgreSQL. It is separate from conversation history — it persists across thread deletions and is never overwritten by the checkpointer.

The table structure is intentionally simple: each row is a memory item with a category (`preference`, `constraint`, `feedback`), a natural-language description, and a timestamp. No complex schema — the agent reads and writes plain text entries.

### How Memory Is Used

At the start of every Personal mode invocation, the agent retrieves the full user profile and prepends it to the system prompt as a dedicated section. The agent is instructed to treat this as ground truth about the user and apply it without asking the user to repeat themselves.

### How Memory Is Updated

There are two update paths:

**Automatic extraction** — after every Personal mode conversation, a background step reviews the exchange and extracts any new preferences, constraints, or feedback signals worth storing. This runs after the response is delivered, not before (zero latency impact). The agent looks for: expressed opinions ("I hate X", "I always prefer Y"), outcomes ("I bought the one you recommended, loved it"), and corrections ("don't recommend leather, I'm vegan").

**Explicit commands** — the user can say "remember that I prefer X" or "forget my preference for Y" directly in the chat. The agent handles this immediately.

**Feedback buttons** — a thumbs up / thumbs down and an "I bought it" button appear under every Personal mode response. These are the strongest signal for memory improvement and feed directly into the feedback category of the user profile. This is more reliable than trying to infer sentiment from conversation text alone.

**Follow-up tracking** — after recommending a product, the agent can send a follow-up message (via Telegram) days or weeks later asking whether the recommendation was acted on and how it worked out. This closes the feedback loop for purchases and gives strong long-term signal.

### Budget Profiles

The user has per-category budget ceilings stored in their profile, not a single global limit. Examples: "max €80 for headphones", "max €150 for shoes". These are hard constraints the agent never violates. The user sets them via explicit commands or they are inferred from reactions to price points in past conversations.

### Seasonal Context

Memory entries are timestamped. The agent notes the season when a preference is recorded and can surface seasonally relevant preferences. "User prefers lighter meals" tagged in summer is treated differently to the same preference expressed in winter.

### Memory Transparency

The user can ask "what do you know about me?" at any time and receive a readable summary of their stored profile. They can also ask to delete specific items or clear the profile entirely.

Memory should never silently apply constraints in ways that seem wrong. If a stored preference conflicts with the user's current request, the agent should flag the conflict rather than silently ignore the request.

---

## Feature Spec

### F1 — Streaming Responses

Responses stream token by token. The user never sees a frozen UI.

- Tokens appear as generated
- During tool calls, a non-blocking status message shows what is happening (e.g., "Searching Reddit...")
- The status message is replaced by the response when streaming begins
- Errors appear inline in the chat

### F2 — Mode Switching

Mode is a toggle in the sidebar — Fast or Personal. Always visible, switchable at any point.

- Defaults to Fast for new threads
- Mode is stored in LangGraph state and restored when a thread is reopened
- A small indicator in the chat shows which mode was active for each response

### F3 — Thread Management

The sidebar shows past threads sorted by most recent activity.

- Thread titles derived from the first human message (~40 chars)
- Titles are cached, not re-queried on every render
- "New Chat" button starts a fresh thread
- Thread deletion is a nice-to-have but not required for V2

### F4 — File Attachments

Users can attach files to a thread. Content is injected into the system prompt for that thread.

- Supported types: txt, md, json, pdf
- Files are stored in the database (as text content), not on the filesystem
- PDF text is extracted at upload time
- Listed in the sidebar with individual delete buttons
- Scoped to the thread — not shared across threads

### F5 — Search (via Search Subagent)

All web search is delegated to a dedicated search subagent. The main agent calls one tool; the subagent handles everything internally.

Tools available to the search subagent:
- **General web search** — any topic, recent sources
- **Reddit search** — discussions and opinions
- **Subreddit search** — targeted search within a named subreddit
- **BuyItForLife search** — r/BuyItForLife specifically, for durable product recommendations

The search subagent has its own system prompt: find relevant information, synthesize it, include source URLs. It decides which tools to call and in what order. Results are returned to the main agent as a synthesized summary, not raw search output.

The main agent **enriches the query before delegating** — relevant user constraints (budget, material preferences, dietary restrictions) are included in the query passed to the subagent. The subagent never reads the user profile directly; it receives context from the main agent.

All search tools use Linkup. No Reddit API credentials required.

### F6 — Weather Tool

Current weather for any location, using Open-Meteo (no API key required). Used by Fast mode for weather queries and by Personal mode when making outdoor or activity-related recommendations.

### F6b — Shopping Subagent

Product recommendations are handled by a dedicated Shopping subagent, not by direct tool calls from the main agent. The main agent calls `ask_shopping_agent` with an enriched query (product type + relevant user constraints); the subagent runs the full workflow internally and returns structured recommendation JSON.

**Shopping subagent workflow:**
1. Search for options (delegates to search subagent or runs its own search)
2. Price comparison across retailers
3. Price history check — "is this actually a good deal right now?"
4. Coupon/discount lookup
5. Synthesize into ranked recommendations matching user constraints

**Tools available inside the Shopping subagent:**
- **Price comparison** — query across major retailers, ranked by value
- **Price history lookup** — historical price trend for a product/retailer pair
- **Coupon/discount finder** — active discount codes for a product or retailer
- **Barcode / product lookup** — identify a product from a barcode or name, return specs and pricing context

### F6c — Food & Diet Tools

- **Nutrition lookup** — query OpenFoodFacts (free, no API key) for nutritional data on a food item or ingredient. Enables macro-aware and diet-constraint-aware recommendations.
- **Recipe search** — find recipes matching the user's current dietary constraints, preferences, and available ingredients.
- **Restaurant finder** — find local restaurants with options matching the user's dietary preferences. Requires location context (set once in profile or provided per query).

### F6d — Lifestyle Tools

- **Activity recommendations** — suggest activities or exercises based on current weather, time of year, and stored user constraints (injuries, fitness level, equipment). Calls the weather tool internally.
- **Product ownership tracker** — the user can log items they own. The agent checks this before recommending something they already have, and can surface maintenance reminders ("you've had those boots 2 years").

### F7 — User Profile Tool

A pair of tools available only in Personal mode:

- `get_user_profile` — performs a pgvector semantic search over the user profile, returning the entries most relevant to the current query. The full profile is never injected wholesale — only what's relevant to the current request.
- `update_user_memory` — writes a new memory item (category + description + timestamp)

`get_user_profile` is called at the start of every Personal mode invocation. `update_user_memory` is called by the memory extraction background task after the response is delivered — never during the response itself.

### F8 — Conversation Continuity

All conversation history persists in PostgreSQL via LangGraph's PostgresSaver. Resuming a thread restores the full message history.

For long threads (>20 messages), older messages are compressed into a rolling summary. The summary is stored in state and prepended to the prompt in place of the raw old messages. Full history remains in Postgres.

---

## Interfaces

There are two interfaces. They share the same backend graph — no logic is duplicated between them.

### Web Frontend (Primary — Personal Mode)

A proper web application built with **Next.js** (frontend) and **FastAPI** (backend). This is where Personal mode lives. Streamlit is not used — it cannot deliver the UI quality needed for recommendation cards, smooth streaming, and responsive mobile layout.

**FastAPI backend:**
- Exposes the LangGraph graph over HTTP
- Streams token-by-token responses to the frontend via Server-Sent Events (SSE)
- Handles file uploads, thread management, and profile reads/writes
- Also serves the Telegram webhook from the same process
- All LangGraph invocations happen here — the frontend never touches the graph directly

**Next.js frontend:**
- Consumes the SSE stream and renders tokens as they arrive
- Personal mode responses render as **structured recommendation cards**: product name, price, retailer link, one-line reason, preference match indicator
- The agent outputs structured JSON for recommendations; the frontend renders it as cards
- **Feedback buttons** (thumbs up / thumbs down / "I bought it") appear beneath every Personal mode response
- Thread sidebar: scrollable history sorted by recency, cached titles, "New Chat" button
- File attachment panel: upload, list, delete — scoped per thread
- Profile viewer: read-only summary of what the agent knows about the user, with delete controls
- Mode toggle: Fast / Personal, visible at all times, switchable mid-conversation
- Responsive — works on mobile browser for when Telegram isn't convenient

### Telegram Bot (Primary — Fast Mode)

The primary interface for Fast mode. The point of Fast mode is answering a question in under 10 seconds — that requires zero friction to invoke. A Telegram message is faster than opening any browser tab.

**Scope:**
- Fast mode is the default for all Telegram messages
- Personal mode is available via a `/personal` command prefix, but the full recommendation experience (cards, feedback buttons, file uploads) belongs in the web frontend — Telegram delivers a text-only version
- The bot is the delivery channel for follow-up messages and price-watch notifications (push, not pull)

**Implementation:**
- The bot handler receives a Telegram message, calls the FastAPI backend, and sends the response back — it is a thin client, not a separate backend
- Responses stream progressively by editing the Telegram message as tokens arrive (Telegram supports message editing for this pattern)


---

## Architecture Spec

### Agent Graph

The graph splits at the top based on mode. Fast and Personal are independent execution paths — no shared branching logic inside a single agent node.

```
START → route_node ──► fast_agent_node ──► fast_tools_condition ──► fast_tool_node ──► fast_agent_node ──► END
                   │
                   └──► summarize_node (conditional) ──► personal_agent_node ──► personal_tools_condition ──► personal_tool_node ──► personal_agent_node ──► END
                                                                                                                                                          (memory extraction fires as background task after stream closes)
```

**route_node** — reads `state.mode` and directs to the appropriate branch. No logic beyond routing.

**summarize_node** — runs conditionally before `personal_agent_node` when the thread exceeds a message threshold (e.g., 20 messages) and the summary hasn't been recently updated. Compresses old messages into a rolling summary stored in state. One-time cost when the threshold is crossed; subsequent calls skip it.

**fast_agent_node** — uses `fast_model`, minimal tool set (weather + search only), tight recursion limit (4 steps max). No memory access, no profile injection.

**personal_agent_node** — uses `main_model`, full tool set, recursion limit of 10. Injects user profile via pgvector at the start of each invocation (semantically relevant entries only, not the full profile). When delegating to subagents, enriches the query with relevant user constraints before passing it.

**Recursion limits** — set explicitly at graph compile time. Fast: 4 (one tool call round then answer). Personal: 10 (enough for multi-step shopping/search loops). Without a limit, a misbehaving session can loop indefinitely and rack up unbounded cost.

**Parallel tool execution** — when the model returns multiple tool calls in a single response, `ToolNode` executes them concurrently. Explicitly verified and enabled. Tools must be stateless and independent for this to be safe — they are.

**Memory extraction** — runs as a FastAPI background task after the SSE stream closes, not as a graph node. It calls a separate lightweight graph (`extract_memories`) that reads the completed conversation and writes new entries to the user profile table. Zero impact on response latency.

### Subagent Delegation

Two subagents. The threshold for a subagent is: does the task require its own multi-step reasoning loop? If yes, delegate. If it's a single API call, keep it as a direct tool.

**Search subagent** — handles all web search. Receives an enriched query (including relevant user constraints) from the main agent. Decides internally which tools to call (general search, Reddit, subreddit, BuyItForLife) and in what order. Returns a synthesized summary with source URLs.

**Shopping subagent** — handles the full product recommendation workflow: search → price comparison → price history check → coupon lookup → synthesize. Receives `{query, budget, relevant_preferences}` from the main agent. Returns structured recommendation JSON. The main agent never sees the individual tool calls.

All other tools (weather, nutrition, restaurant finder, profile read/write, lifestyle) are called directly — they are single lookups with no multi-step loop.

### State

- `messages` — full conversation history with `add_messages` reducer
- `mode` — current mode (`"fast"` or `"personal"`), persisted in state
- `summary` — rolling summary of older messages when thread exceeds threshold
- `thread_id` — carried in config, used to look up files from `thread_files` table

`attached_files` is **not** in state. File content is stored in a dedicated `thread_files` Postgres table and looked up by `thread_id` at the start of `personal_agent_node`. Keeping large file content in state means it gets serialized into every checkpoint on every tool call — expensive and unnecessary.

### Models

Three tiers. No `max_tokens` cap.

- **fast_model** — cheap and low-latency (e.g., gpt-4.1-mini). Used for Fast mode, both subagents, and the memory extraction background task.
- **main_model** — Claude Sonnet (via `langchain-anthropic`) for Personal mode. Handles long preference-laden prompts and complex constraint satisfaction better than GPT-4o. GPT-4o is the fallback if `ANTHROPIC_API_KEY` is absent.
- **reasoning_model** — optional path for genuinely hard queries: multi-product comparisons with many competing constraints. Triggered by the agent's own judgement, not the default. Options: o3, Claude with extended thinking. Must not fire on simple lookups.

Model selection happens inside each agent node — no shared selection logic.

### Configuration

All values from environment. The app fails with a clear error at startup if required vars are missing.

Required:
- `OPENAI_API_KEY`
- `DB_URI`

Optional (graceful degradation if absent):
- `LINKUP_API_KEY` — search tools not registered, agent falls back to training knowledge
- `ANTHROPIC_API_KEY` — Personal mode falls back to GPT-4o
- `TELEGRAM_BOT_TOKEN` — Telegram bot disabled
- `REDIS_URL` — search caching disabled, all searches hit Linkup live
- `LANGCHAIN_API_KEY` + `LANGCHAIN_PROJECT` — tracing disabled

A `.env.example` listing all variables is committed to the repo.

### FastAPI Backend

- Single process serving both the HTTP API and the Telegram webhook
- Agent and checkpointer initialized once at startup via a lifespan context manager — not per-request
- DB table setup (checkpointer, user_profile, scheduler jobs) runs once in the same lifespan handler
- LangGraph invocations happen inside FastAPI route handlers
- Responses stream to the frontend via Server-Sent Events using `astream_events`
- Python `logging` throughout — no `print` statements
- All config from `config.py`, no circular imports

### Infrastructure

**pgvector** — once the user profile grows beyond a handful of entries, injecting the entire profile on every call is wasteful and eventually hits context limits. pgvector (Postgres extension) enables semantic similarity search over memory: retrieve only the entries most relevant to the current query. No external service — same Postgres instance already in use.

**Redis** — search results are cached with a short TTL (6 hours). If the user asks about the same product category twice in a day, the second query hits the cache rather than Linkup. Reduces latency and API costs. Graceful degradation: if `REDIS_URL` is absent, all queries go live.

**Scheduler (APScheduler)** — runs alongside the app to handle two jobs: (1) follow-up messages sent via Telegram after a recommendation (configurable delay, e.g., 1 week), (2) price-watch notifications when a tracked product drops below a threshold. Lightweight — no separate worker process needed for a personal assistant at this scale.

---

## What to Drop Entirely

- **Streamlit** — replaced by Next.js + FastAPI
- **Code mode** — out of scope
- **Work/study mode** — out of scope
- **RAG / vector search** — the university exam use case is gone; add a personal knowledge base later if needed
- **Pinecone** — no longer needed
- **PRAW / Reddit credentials** — Linkup handles Reddit
- **`middleware/call_wrapping.py`** — dead code from a previous architecture
- **`user_role` state field** — was never used
- **Upfront mode selection screen** — replaced by sidebar toggle
- **Hardcoded LangSmith project names and paths** — these belong in `.env`

---

## File Structure

```
stumberg/
├── backend/
│   ├── main.py               # FastAPI app, lifespan, route definitions, SSE streaming, Telegram webhook
│   ├── bot.py                # Telegram bot logic (thin client — calls FastAPI internally)
│   ├── scheduler.py          # APScheduler jobs (follow-ups, price-watch notifications)
│   ├── config.py             # Env var loading and validation (fail fast on required keys)
│   ├── graph.py              # LangGraph graph definition
│   ├── schema.py             # AgentState TypedDict
│   ├── models.py             # LLM client instances (fast, main, reasoning)
│   ├── prompts.py            # System prompts for each mode
│   ├── memory.py             # User profile read/write logic and Postgres table setup
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py         # Linkup search tools (general, reddit, subreddit, buyforlife)
│   │   ├── weather.py        # Open-Meteo weather tool
│   │   ├── shopping.py       # Price comparison, price history, coupon finder, barcode lookup
│   │   ├── food.py           # Nutrition lookup (OpenFoodFacts), recipe search, restaurant finder
│   │   ├── lifestyle.py      # Activity recommendations, product ownership tracker
│   │   └── profile.py        # get_user_profile and update_user_memory tools
│   ├── subagents/
│   │   ├── search_subagent.py    # Search subgraph — general, reddit, subreddit, buyforlife tools
│   │   ├── shopping_subagent.py  # Shopping subgraph — search → price → history → coupon → synthesize
│   │   └── memory_extractor.py   # Lightweight graph called as background task after Personal responses
│   └── requirements.txt      # Pinned Python dependencies
│
├── frontend/
│   ├── app/                  # Next.js app directory
│   │   ├── page.tsx          # Root — redirects to /chat
│   │   ├── chat/
│   │   │   └── page.tsx      # Main chat UI
│   │   └── profile/
│   │       └── page.tsx      # User profile viewer/editor
│   ├── components/
│   │   ├── ChatThread.tsx    # Message list with streaming support
│   │   ├── MessageBubble.tsx # Single message — plain text or recommendation card
│   │   ├── RecommendationCard.tsx  # Product card with price, link, reason, feedback buttons
│   │   ├── Sidebar.tsx       # Thread list, new chat, mode toggle, file panel
│   │   ├── FilePanel.tsx     # Upload, list, delete attached files
│   │   └── ToolStatus.tsx    # Non-blocking indicator during tool calls
│   ├── lib/
│   │   └── api.ts            # API client — SSE streaming, REST calls to FastAPI
│   ├── package.json
│   └── tsconfig.json
│
├── docker-compose.yml        # Local dev: backend + frontend + postgres + redis
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── .gitignore
```

---

## Constraints and Non-Negotiables

- **Two modes only.** Resist adding more until the two core modes are excellent.
- **Never truncate output.** No low `max_tokens` caps.
- **All responses stream.** No synchronous blocking invoke calls in any UI path — SSE to the frontend, progressive message editing in Telegram.
- **Memory must be transparent.** The user can always inspect and edit what is stored.
- **The frontend is Next.js. The backend is FastAPI.** Not Streamlit. The UI ceiling matters.
- **Telegram is Fast mode first.** Personal mode is available via command prefix but the full experience belongs in the web frontend.
- **The bot is a thin client.** No LangGraph calls directly from the Telegram handler — everything goes through FastAPI.
- **No dead code.** If it's not used, it's not in the repo.
- **No hardcoded secrets or paths.** Everything in `.env`.
- **Graceful degradation.** Missing optional keys reduce capability, they do not crash the app.
- **`docker-compose.yml` covers full local dev.** No manual Postgres or Redis setup required to run the project.
