from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from models import basic_model, advanced_model

#this whole section is a bit useless atm, but im putting it down for potential future work on dynamic model selection depending on condition
@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:


    try:
        messages = request.state.get("messages", [])
        human_message = " ".join(
            msg.content.lower() for msg in messages[-8:] 
            if hasattr(msg, 'type') and msg.type == "human" and hasattr(msg, "content") and msg.content
        )
        print(human_message)
        
        model = basic_model # Default
        
        if human_message:
           # first_word= human_message[-1].split()[0]
            #print(first_word)

            if "fast" in human_message:
                model = basic_model
            elif "think" in human_message:
                model = advanced_model
            
        return handler(request.override(model=model))

    except Exception as e:
        # Fallback if no messages/state available
        print(f"Selection error: {e}")
        return handler(request.override(model=basic_model))

