from langchain.tools import tool
from linkup import LinkupClient
import os
import praw
from typing import Optional, List

def _get_linkup_client() -> LinkupClient:
    api_key = os.getenv("LINKUP_API_KEY", "")
    return LinkupClient(api_key=api_key)

def _perform_search(query: str, include_domains: Optional[List[str]] = None, exclude_domains: Optional[List[str]] = None) -> str:
    client = _get_linkup_client()
    # Using 'standard' depth for efficiency, default output_type='searchResults'
    response = client.search(
        query=query, 
        depth="standard", 
        output_type="searchResults", 
        include_images=False,
        include_domains=include_domains,
        exclude_domains=exclude_domains
    )
    return str(response)

@tool
def general_search(question: str) -> str:
    """Search for general information from recent sources."""
    return _perform_search(query=question)

@tool
def reddit_search(question: str) -> str:
    """Search specifically on Reddit for discussions and opinions."""
    return _perform_search(query=question, include_domains=["reddit.com"], exclude_domains=["https://www.reddit.com/r/BuyItForLife/"])

@tool
def subreddit_search(question: str, subreddit: str) -> str:
    """Search within a specific subreddit.
    
    Args:
        question: The search query.
        subreddit: The name of the subreddit to search in (e.g., 'python', 'learnprogramming').
    """
    refined_query = f"{question} https://www.reddit.com/r/{subreddit}"
    return _perform_search(query=refined_query, include_domains=["reddit.com"], exclude_domains=["https://www.reddit.com/r/BuyItForLife/"])


@tool
def buyforlife_search(question: str, limit: int = 50, sort: str = "relevance") -> str:
    """
    Search r/BuyItForLife for product recommendations and reviews using official Reddit API.
    Args:
        question: Search query (e.g., "best durable backpack")
        limit: Max posts to retrieve (default 50; None for all)
        sort: 'relevance', 'new', 'hot', 'top', 'comments'
    """
    # Configure with your Reddit app credentials (create at https://www.reddit.com/prefs/apps)
    reddit = praw.Reddit(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        user_agent="buyforlife-tool:v1.0 (by /u/yourusername)"
    )
    
    subreddit = reddit.subreddit("BuyItForLife")
    posts = []
    
    # Paginate search
    generator = subreddit.search(question, sort=sort, limit=limit)
    for post in generator:
        posts.append({
            "title": post.title,
            "url": post.url,
            "score": post.score,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "selftext_snippet": post.selftext[:200] + "..." if post.selftext else ""
        })
    
    return str(posts)  # Or format as JSON/dict for LLM parsing

