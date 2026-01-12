# Project Roadmap

## Core Architecture & Memory
- [ ] **Redis Implementation**: Implement Redis for short and long-term memory (distinct from vector store).
- [ ] **Context Extension**: Implement logic to inject base setup info to avoid repetition, replacing the need for re-stating context.
- [ ] **Sub-Agent for Retrieval**: Create a dedicated sub-agent that analyzes context, picks the right tool, and retrieves information for the main agent.
- [ ] **Vector Store Strategy**: Rethink and optimize current vector store usage.

## Tools & Capabilities
- [ ] **Summary Tool**: Develop a general summarization tool.
- [ ] **Exam Prep Tool**: Create a tool that asks questions to test knowledge.
- [ ] **Concept Explanation Tool**: Build a tool for pedagogical concept explanations.
- [ ] **Recommendation Tool**: Implement a separate algorithm for analyzing user preferences and suggesting content (movies, products, etc.).
- [ ] **Search Tool Improvements**:
    - [ ] Fix "BuyForLife" search tool (investigate Devvit and Reddit API limits).
    - [ ] Analyze and optimize search tool context limits.

## User Experience & Modes
- [x] **Mode Selection**: Implement a startup prompt for mode selection (Uni/Work, Personal, General).
- [ ] **File Upload**: Add capability for users to upload files.
- [ ] **Planning Tool**: Create a "Planning" capability for pre-code preparation.
- [x] **Coding Tool/Mode**: Research and design a dedicated coding mode or tool.
- [ ] **Project Context**: Implement "Folders" or "Projects" concept to maintain persistent context.

## Infrastructure & Engineering
- [ ] **Deployment**: Research Railway free tier for personal deployment.
- [x] **Observability**: Investigate LangSmith Studio for better debugging and tracing.




fix logos and ui bugs (different button sizes upon startup)
refresh database, delete everything so far