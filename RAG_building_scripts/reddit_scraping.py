import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



@dataclass
class PostData:
    """Structured post data for vector store prep."""
    post_id: str
    title: str
    selftext: str
    score: int
    num_comments: int
    url: str
    author: str
    comments: List[Dict[str, str]]  # List of {"author": str, "body": str, "score": int}


#SUBREDDIT = "BuyItForLife"
OUTPUT_DIR = Path("reddit_files")
STATE_FILE = OUTPUT_DIR / "scrape_state.json"
POSTS_FILE = OUTPUT_DIR / "posts.jsonl"



async def init_output_dir():
    """Create output directory and ensure files exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_FILE.parent.mkdir(exist_ok=True)
    if not POSTS_FILE.exists():
        POSTS_FILE.touch()



async def load_state() -> Dict:
    """Load last scrape state (last post ID, total posts)."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_post_id": None, "total_posts": 0}


async def save_state(state: Dict):
    """Save scrape state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


async def save_post(post: PostData):
    """Append post to JSONL file."""
    with open(POSTS_FILE, 'a') as f:
        f.write(json.dumps(asdict(post)) + '\n')
    logger.info(f"Saved post {post.post_id}: {post.title[:50]}...")


async def extract_post_data(page, post_element, index: int) -> Optional[PostData]:
    """Grabs ANY text + links - works regardless of selectors."""
    try:
        # GRAB ALL VISIBLE TEXT (titles, previews guaranteed)
        all_text = await post_element.inner_text()
        title = all_text[:150].strip()  # First 150 chars = title + preview
       
        if not title:
            logger.warning(f"No text in post {index}")
            return None
       
        # FIND COMMENTS LINK (most reliable ID source)
        link_elements = await post_element.locator('a[href*="/comments/"]').all()
        post_id = ""
        url = ""
        if link_elements:
            href = await link_elements[0].get_attribute('href')
            if '/comments/' in href:
                post_id = href.split('/comments/')[1].split('/')[0].split('?')[0]
                url = f"https://www.reddit.com{href}"
       
        # Fake score/comments (fill later from API if needed)
        score = len(title)  # Proxy for relevance
        num_comments = len(all_text.split('\n'))
       
        logger.info(f"✅ Post {index}: '{title[:60]}...' ID={post_id}")
        return PostData(
            post_id or f"post_{index}",
            title,
            all_text,
            score,
            num_comments,
            url,
            "unknown",
            []
        )
    except:
        return None



async def scrape_comments(page, post_url: str) -> List[Dict[str, str]]:
    """Navigate to post and scrape ALL comments."""
    comments = []
    try:
        await page.goto(post_url, wait_until="networkidle")
        await page.wait_for_selector('article', timeout=10000)
       
        # Scroll comments thread
        comment_threads = page.locator('[data-testid="comment"]')
        async for _ in range(10):  # Scroll 10x for deep comments
            await page.keyboard.press("End")
            await page.wait_for_timeout(2000)
       
        # Extract comments
        comment_elements = await comment_threads.all()
        for el in comment_elements[:50]:  # Limit per post to avoid overload
            try:
                author = await el.locator('[data-testid="comment_author"]').inner_text()
                body = await el.locator('[data-testid="comment"]').inner_text()
                score_str = await el.locator('[aria-label*="upvote"]').inner_text()
                score = int(score_str.replace(',', '')) if score_str.isdigit() else 0
                comments.append({"author": author, "body": body, "score": score})
            except:
                continue
       
        logger.info(f"Extracted {len(comments)} comments from {post_url}")
    except Exception as e:
        logger.warning(f"Failed to scrape comments for {post_url}: {e}")
   
    return comments





async def scrape_subreddit():
    """Main scraping loop with infinite scroll."""
    await init_output_dir()
    state = await load_state()
   
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process'  # Optional: lighter in Docker
        ]
    )


        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
       
        subreddit_url = f"https://www.reddit.com/r/BuyItForLife/new/"
        await page.goto(subreddit_url, wait_until="networkidle")
       
        previous_height = 0
        consecutive_no_change = 0
        max_no_change = 5
       
        while consecutive_no_change < max_no_change:
            # Extract current posts
            post_locator = page.locator('[data-testid="post-container"], div[data-testid*="placeagg"], article')
            post_elements = await post_locator.all()


            for i, post_el in enumerate(post_elements):  # <- FIXED: adds i
                post_data = await extract_post_data(page, post_el, i)
                if not post_data or post_data.post_id == state["last_post_id"]:
                    continue
               
                # SKIP comments for now - too slow + breaks scroll
                post_data.comments = []
               
                await save_post(post_data)
                state["total_posts"] += 1
                state["last_post_id"] = post_data.post_id
                await save_state(state)
           
            # Infinite scroll
            prev_height = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)  # Wait for load
           
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                consecutive_no_change += 1
            else:
                consecutive_no_change = 0
           
            logger.info(f"Scrolled. Height: {prev_height} -> {new_height}. No change streak: {consecutive_no_change}")
       
        await browser.close()
        logger.info(f"Scraping complete. Total posts: {state['total_posts']}")


if __name__ == "__main__":
    asyncio.run(scrape_subreddit())