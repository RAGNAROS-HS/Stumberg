from langchain.tools import tool
from linkup import LinkupClient
import os
@tool
def search(question: str) -> str:
    """Simple search for general information from recent sources"""
    LINKUP_API_KEY = os.getenv("LINKUP_API_KEY", "")

    client = LinkupClient(api_key=LINKUP_API_KEY)
    response = client.search(query=question, depth = "standard", output_type="searchResults", include_images=False)
    return response
#testing tsting