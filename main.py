from langchain.tools import tool
from langchain.chat_models import init_chat_model
from perplexityai import Perplexity


model = init_chat_model(

    temperature = 0
)