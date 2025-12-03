from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["PPLX_API_KEY"] = os.getenv("PERPLEXITY_KEY", "")

model = init_chat_model(
    "sonar",
    model_provider="perplexity",
    temperature=0.0,
)

print(model.invoke("Why do parrots talk?"))
