from langchain.tools import tool
from langchain.chat_models import init_chat_model
from perplexity import Perplexity
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize client with explicit API key
client = Perplexity(api_key=os.environ.get("PERPLEXITY_KEY"))

completion = client.chat.completions.create(
    model="sonar-pro",
    messages=[
        {"role": "user", "content": "What were the results of the 2025 French Open Finals?"}
    ]
)

print(completion.choices[0].message.content)