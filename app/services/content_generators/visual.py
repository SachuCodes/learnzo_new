"""Visual content generator. Uses Gemini AI for visual learning guides and YouTube search.
Images are fetched from Wikipedia's public API - no API key required.
"""
import sys
import requests
from app.services.ai_service import generate_text

WIKIPEDIA_HEADERS = {
    "User-Agent": "Learnzo-Edu-App/1.0 (contact: demo@learnzo.ai)"
}


def fetch_wikipedia_images(topic: str, max_images: int = 5) -> list[str]:
    """
    Fetch image URLs from Wikipedia for a given topic.
    Strategy:
      1. Use Wikipedia's REST summary API to get the main page image.
      2. Use the search API to find related pages and grab their main images too.
    Returns a list of image URLs (may be empty if none found).
    """
    print(f"[visual] Fetching Wikipedia images for: {topic}", flush=True, file=sys.stderr)

    urls = []

    # Step 1: Try the REST summary endpoint - gives the hero image for the best matching article
    try:
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
        resp = requests.get(summary_url, headers=WIKIPEDIA_HEADERS, timeout=5)
        print(f"[visual] REST summary status: {resp.status_code}", flush=True, file=sys.stderr)
        if resp.status_code == 200:
            data = resp.json()
            # originalimage is higher resolution than thumbnail
            img = data.get("originalimage") or data.get("thumbnail")
            if img and img.get("source"):
                urls.append(img["source"])
                print(f"[visual] STEP 1: Got main image: {img['source']}", flush=True, file=sys.stderr)
    except Exception as e:
        print(f"[visual] STEP 1 FAILED: {e}", flush=True, file=sys.stderr)

    # Step 2: Search for up to 4 related pages and grab their main images
    if len(urls) < max_images:
        try:
            search_resp = requests.get("https://en.wikipedia.org/w/api.php", params={
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": 6,
                "format": "json",
            }, headers=WIKIPEDIA_HEADERS, timeout=5)
            search_resp.raise_for_status()
            results = search_resp.json().get("query", {}).get("search", [])
            page_titles = [r["title"] for r in results]
            print(f"[visual] STEP 2: Related pages: {page_titles}", flush=True, file=sys.stderr)

            for title in page_titles:
                if len(urls) >= max_images:
                    break
                try:
                    s_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
                    s_resp = requests.get(s_url, headers=WIKIPEDIA_HEADERS, timeout=5)
                    if s_resp.status_code == 200:
                        data = s_resp.json()
                        img = data.get("originalimage") or data.get("thumbnail")
                        if img and img.get("source") and img["source"] not in urls:
                            urls.append(img["source"])
                            print(f"[visual] STEP 2: Got image from '{title}': {img['source']}", flush=True, file=sys.stderr)
                except Exception as e:
                    print(f"[visual] STEP 2: Failed for '{title}': {e}", flush=True, file=sys.stderr)
                    continue
        except Exception as e:
            print(f"[visual] STEP 2 search FAILED: {e}", flush=True, file=sys.stderr)

    print(f"[visual] Final URLs ({len(urls)}): {urls}", flush=True, file=sys.stderr)
    return urls[:max_images]


def generate_visual(topic: str, rules: dict):
    """
    Generate visual learning guidance for a topic using Gemini.
    Images are sourced from Wikipedia's public REST API.
    """
    tone = rules.get("tone", "friendly and educational")

    prompt = f"""
    You are an expert educator. Create a 'Visual Learning Guide' for the topic: "{topic}".
    
    Target Student Profile:
    - Tone: {tone}
    - Describe the topic using vivid, visual language.
    - Provide 3-4 'Mental Imagery' exercises where the student imagines specific visual aspects of {topic}.
    - Format as a descriptive guide.
    
    Output only the visual guide text.
    """

    instruction = generate_text(prompt)

    if not instruction:
        instruction = (
            f"Observe and imagine the different parts of {topic}. "
            f"Visualize how it looks, its colors, and its shapes."
        )

    images = fetch_wikipedia_images(topic, max_images=5)

    return {
        "type": "visual",
        "topic": topic,
        "instruction": instruction,
        "images": images,
        "youtube_search_url": f"https://www.youtube.com/results?search_query={topic}",
        "rules_applied": rules,
        "source": "gemini-ai + wikipedia",
    }