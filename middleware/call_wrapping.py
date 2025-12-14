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
        base_prompt = (
            "You serve as an information assistant. Your responses should be "
            "succinct, precise, and assertive. Do not hesitate to challenge the "
            "user's opinions or assertions; your primary objective is to convey "
            "recent and factual information."
        )
        final_prompt = ""
        if human_message:
            #then I check for keywords and select model and extended system promptbased on that
            if "think" in human_message:
                model = advanced_model
                final_prompt = base_prompt + " Provide detailed technical responses."
            elif "fast" in human_message:
                model = basic_model
                final_prompt = base_prompt + " Explain concepts simply and avoid jargon. In case of information retrieval, provide the answer straight away with no extra fluff, use tools where possible"
            elif "code" in human_message:
                model = advanced_model
                final_prompt = base_prompt + (
                    " Provide comprehensive and detailed code that strictly adheres to established "
                    "best coding practices, ensuring that all segments of the code that remain "
                    "unchanged are included in their entirety. It is essential to maintain clarity "
                    "and organization throughout the code without introducing any unnecessary "
                    "complexity or alterations that could detract from its readability. Avoid adding "
                    "any superfluous imports or extraneous lines that do not contribute to the "
                    "functionality of the code; the final result should be a well-structured piece "
                    "of work that is easily comprehensible. Additionally, the code must demonstrate "
                    "proper use of comments and thorough documentation to facilitate understanding. "
                    "Ensure that variable names are meaningful and descriptive, reflecting their "
                    "purpose within the code. Furthermore, the code should be efficient and "
                    "maintainable, allowing for easy updates and modifications in the future without "
                    "compromising its integrity."
                )

        updated_request = request.override(
            model=model,
            system_prompt=final_prompt
        )
            
        return handler(updated_request)

    except Exception as e:
        # Fallback if no messages/state available
        print(f"Selection error: {e}")
        return handler(request.override(model=basic_model, system_prompt=base_prompt))

