from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def infer_role_prompt(request: ModelRequest) -> str:
    """Infer user role from conversation history."""
    try:
        messages = request.runtime.state.get("messages", [])
        recent_content = " ".join(
            msg.content.lower() for msg in messages[-8:] 
            if hasattr(msg, 'content') and msg.content
        )
        
        base_prompt = "You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information"
        
        if any(term in recent_content for term in ["advanced", "algorithm", "ontology", "sat solver", "dl", "description logic", "evolutionary", "nash", "q-learning"]):
            return f"{base_prompt} Provide detailed technical responses."
        elif any(term in recent_content for term in ["beginner", "explain simply", "what is", "how does", "basics"]):
            return f"{base_prompt} Explain concepts simply and avoid jargon."
        
        return base_prompt
    except:
        # Fallback if no messages/state available
        return "You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information"
