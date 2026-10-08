"""Latest macro news via Tavily -> data/raw/news.json"""
import json, os, sys
from dotenv import load_dotenv
from src.config import RAW, ROOT

load_dotenv(ROOT / ".env")
QUERIES = [
    "US CPI inflation latest data and outlook",
    "Federal Reserve FOMC rate decision outlook",
    "US jobs report nonfarm payrolls labor market",
    "US economy macro outlook markets",
]


def fetch(days=14, max_results=5):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        sys.exit("Set TAVILY_API_KEY in .env (or run with --synthetic).")
    from tavily import TavilyClient
    client, seen, out = TavilyClient(api_key=key), set(), []
    for q in QUERIES:
        res = client.search(q, topic="news", days=days, max_results=max_results)
        for r in res.get("results", []):
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            out.append({"query": q, "title": r.get("title"), "url": r["url"],
                        "published": r.get("published_date"), "snippet": (r.get("content") or "")[:400]})
    (RAW / "news.json").write_text(json.dumps(out, indent=2))
    print(f"news.json: {len(out)} articles")
    return out


if __name__ == "__main__":
    fetch()
