from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from models import basic_model, advanced_model

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    try:
        #first I try to get the first 8 letters   
        messages = request.state.get("messages", [])
        human_message = " ".join(
            msg.content.lower() for msg in messages[-8:] 
            if hasattr(msg, 'type') and msg.type == "human" and hasattr(msg, "content") and msg.content
        )
        print(human_message)
        
        model = basic_model # Default
        base_prompt = "You are a information assistant. Be concise, accurate and non-compliant. Do not be afraid to counter the users opinion or statement, your primary goal should be presenting factual information"
        final_prompt = ""
        if human_message:
            #then I check for keywords and select model and extended system promptbased on that
            if "fast" in human_message:
                model = basic_model
                final_prompt = base_prompt + " Provide detailed technical responses."
            elif "think" in human_message:
                model = advanced_model
                final_prompt = base_prompt + " Explain concepts simply and avoid jargon."

        updated_request = request.override(
            model=model,
            system_prompt=final_prompt
        )
            
        return handler(updated_request)

    except Exception as e:
        # Fallback if no messages/state available
        print(f"Selection error: {e}")
        return handler(request.override(model=basic_model, system_prompt=base_prompt))

