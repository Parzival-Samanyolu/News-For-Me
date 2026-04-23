"""
fetch_news.py
-------------
News ingestion module for the Turkish AI News Automation System.
Fetches trending news from Google News RSS, GNews API, and Reddit RSS.
Scores, deduplicates, and returns the top N topics for the day.
"""

import feedparser
import requests
import hashlib
import json
import os
from datetime import datetime, timezone
from difflib import SequenceMatcher


# ─────────────────────────────────────────────
# MAGAZINE RSS FEED SOURCES
# ─────────────────────────────────────────────
RSS_SOURCES = [
    # Google News - Entertainment (Turkish)
    "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=tr&gl=TR&ceid=TR:tr",

    # Google News - Entertainment (Global English)
    "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en",

    # Google News - Celebrities
    "https://news.google.com/rss/search?q=celebrity+news&hl=en-US&gl=US&ceid=US:en",

    # Google News - Turkish celebrity news
    "https://news.google.com/rss/search?q=magazin+haberleri&hl=tr&gl=TR&ceid=TR:tr",

    # Reddit Pop Culture
    "https://www.reddit.com/r/popculture/.rss",

    # Reddit Entertainment
    "https://www.reddit.com/r/entertainment/.rss",

    # Reddit Movies
    "https://www.reddit.com/r/movies/.rss",

    # Reddit Television
    "https://www.reddit.com/r/television/.rss",

    # Reddit Music
    "https://www.reddit.com/r/music/.rss",
]

# Turkish news keywords that boost virality score
VIRAL_KEYWORDS_TR = [
    "şok", "bomba", "flaş", "son dakika", "inanılmaz", "skandal",
    "tarihi", "dev", "büyük", "kritik", "gizli", "ifşa", "ortaya çıktı",
    "açıkladı", "duyurdu", "uyardı", "tehlike", "kriz", "çöktü",
    "rekor", "ilk kez", "dünyayı sarstı", "herkes konuşuyor"
]

VIRAL_KEYWORDS_EN = [
    "breaking", "urgent", "exclusive", "shocking", "scandal",
    "historic", "massive", "critical", "secret", "revealed",
    "exposed", "record", "first ever", "world shaking", "everyone talking",
    "crisis", "collapse", "warning", "emergency", "major"
]

# ─────────────────────────────────────────────
# TURKISH DOMESTIC POLITICS FILTER
# Articles matching these will be SKIPPED.
# International politics (US, EU, etc.) is allowed.
# ─────────────────────────────────────────────
TR_POLITICS_BLACKLIST_TR = [
    # Parties
    "akp", "chp", "mhp", "hdp", "deva", "iyi parti", "gelecek partisi",
    "yeniden refah", "saadet", "yeşil sol", "tem parti",
    # Politicians (Turkish domestic)
    "erdoğan", "kılıçdaroğlu", "özel", "bahçeli", "perçin", "akşener",
    "imamoğlu", "yavaş", "özdağ", "demirtaş", "kavala",
    # Institutions / domestic political terms
    "meclis", "tbmm", "büyük millet meclisi", "anayasa mahkemesi",
    "cumhurbaşkanlığı hükümet sistemi", "seçim", "milletvekili",
    "iktidar", "muhalefet", "koalisyon", "kabine değişikliği",
    "bakan değişikliği", "bakanlık atama", "parti kongresi",
    "belediye başkanı seçim", "yerel seçim", "genel seçim",
    "oy oranı", "anket sonuç", "sandık",
]

TR_POLITICS_BLACKLIST_EN = [
    # English-language Turkish politics keywords
    "turkish parliament", "turkish election", "turkish opposition",
    "turkish ruling party", "turkish government coalition",
    "erdogan party", "akp party", "chp party", "turkish domestic",
    "turkish interior minister", "turkey election", "turkey vote",
    "turkey opposition", "turkey ruling", "turkish politics",
    "turkish mayor", "istanbul mayor", "ankara mayor",
]


def is_turkish_domestic_politics(article: dict) -> bool:
    """
    Returns True if the article is about Turkish domestic politics.
    International news about Turkey (economy, tourism, war, etc.) is allowed.
    """
    combined = (
        article.get("title", "") + " " +
        article.get("summary", "")
    ).lower()

    for term in TR_POLITICS_BLACKLIST_TR:
        if term in combined:
            return True
    for term in TR_POLITICS_BLACKLIST_EN:
        if term in combined:
            return True
    return False


def fetch_rss_feed(url: str) -> list[dict]:
    """Fetch and parse a single RSS feed, return list of article dicts."""
    articles = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
        feed = feedparser.parse(url, request_headers=headers)
        for entry in feed.entries[:15]:  # cap at 15 per source
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            published = entry.get("published", "")
            # Clean HTML tags from summary
            import re
            summary = re.sub(r"<[^>]+>", "", summary)

            if title and link:
                articles.append({
                    "title": title,
                    "url": link,
                    "summary": summary[:500],
                    "published": published,
                    "source": url,
                    "score": 0
                })
    except Exception as e:
        print(f"[WARN] RSS fetch failed for {url}: {e}")
    return articles


def fetch_gnews(api_key: str, language: str = "tr", country: str = "tr", max_results: int = 10) -> list[dict]:
    """
    Fetch from GNews API (free tier: 100 req/day).
    Set GNEWS_API_KEY in GitHub Secrets.
    """
    if not api_key:
        return []
    articles = []
    try:
        url = (
            f"https://gnews.io/api/v4/top-headlines"
            f"?lang={language}&country={country}&max={max_results}"
            f"&apikey={api_key}"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "summary": item.get("description", "")[:500],
                "published": item.get("publishedAt", ""),
                "source": "gnews",
                "score": 0
            })
    except Exception as e:
        print(f"[WARN] GNews fetch failed: {e}")
    return articles


def score_article(article: dict) -> int:
    """
    Score an article based on recency and viral keyword presence.
    Higher score = better candidate for generation.
    """
    score = 0
    title_lower = article["title"].lower()
    summary_lower = article["summary"].lower()
    combined = title_lower + " " + summary_lower

    # Viral keyword bonuses
    for kw in VIRAL_KEYWORDS_TR:
        if kw in combined:
            score += 10
    for kw in VIRAL_KEYWORDS_EN:
        if kw in combined:
            score += 5

    # Length bonus (longer summary = more content to work with)
    if len(article["summary"]) > 200:
        score += 5
    if len(article["summary"]) > 400:
        score += 5

    # Has a proper URL
    if article["url"].startswith("http"):
        score += 3

    return score


def deduplicate(articles: list[dict], title_threshold: float = 0.65, summary_threshold: float = 0.50) -> list[dict]:
    """
    Remove near-duplicate articles by title AND summary similarity.
    Keeps the highest-scored article when duplicates are found.
    """
    unique = []
    for article in articles:
        is_duplicate = False
        for kept in unique:
            title_ratio = SequenceMatcher(
                None,
                article["title"].lower(),
                kept["title"].lower()
            ).ratio()
            summary_ratio = SequenceMatcher(
                None,
                article.get("summary", "").lower(),
                kept.get("summary", "").lower()
            ).ratio()
            if title_ratio >= title_threshold or summary_ratio >= summary_threshold:
                is_duplicate = True
                # Keep higher-scored one
                if article["score"] > kept["score"]:
                    unique.remove(kept)
                    unique.append(article)
                break
        if not is_duplicate:
            unique.append(article)
    return unique


def get_content_hash(title: str) -> str:
    """Generate a short hash to track published titles and avoid repeats."""
    return hashlib.md5(title.lower().encode()).hexdigest()[:12]


def load_published_hashes(filepath: str = "published_hashes.json") -> set:
    """Load previously published article hashes to avoid republishing."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            return set(data.get("hashes", []))
    return set()


def save_published_hashes(hashes: set, filepath: str = "published_hashes.json"):
    """Persist published hashes so duplicates are avoided across runs."""
    existing = load_published_hashes(filepath)
    all_hashes = list(existing | hashes)
    # Keep only last 500 to prevent file bloat
    all_hashes = all_hashes[-500:]
    with open(filepath, "w") as f:
        json.dump({"hashes": all_hashes, "updated": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def fetch_top_topics(count: int = 3, gnews_api_key: str = "") -> list[dict]:
    """
    Main entry point. Fetches all sources, scores, deduplicates,
    filters out already-published articles, and returns top N topics.
    """
    print("[INFO] Fetching news from all sources...")
    all_articles = []

    # RSS sources
    for source in RSS_SOURCES:
        articles = fetch_rss_feed(source)
        print(f"  → {len(articles)} articles from {source[:60]}")
        all_articles.extend(articles)

    # GNews API (if key provided)
    if gnews_api_key:
        gnews_articles = fetch_gnews(gnews_api_key)
        print(f"  → {len(gnews_articles)} articles from GNews API")
        all_articles.extend(gnews_articles)

    # Score all articles
    for article in all_articles:
        article["score"] = score_article(article)

    # Sort by score descending
    all_articles.sort(key=lambda x: x["score"], reverse=True)

    # ── FILTER: Remove Turkish domestic politics ──────────────────────────────
    before_filter = len(all_articles)
    all_articles = [a for a in all_articles if not is_turkish_domestic_politics(a)]
    removed = before_filter - len(all_articles)
    if removed:
        print(f"[FILTER] Removed {removed} Turkish domestic politics articles")
    # ─────────────────────────────────────────────────────────────────────────

    # Deduplicate
    unique_articles = deduplicate(all_articles)
    print(f"[INFO] {len(unique_articles)} unique articles after deduplication")

    # Filter already-published
    published_hashes = load_published_hashes()
    fresh_articles = [
        a for a in unique_articles
        if get_content_hash(a["title"]) not in published_hashes
    ]
    print(f"[INFO] {len(fresh_articles)} fresh articles (not yet published)")

    # Return top N
    top = fresh_articles[:count]
    print(f"[INFO] Selected top {len(top)} topics for generation:")
    for i, a in enumerate(top, 1):
        print(f"  {i}. [{a['score']}pts] {a['title'][:80]}")

    return top


if __name__ == "__main__":
    topics = fetch_top_topics(count=3)
    print("\n--- TOP TOPICS ---")
    for t in topics:
        print(f"\nTitle:   {t['title']}")
        print(f"URL:     {t['url']}")
        print(f"Summary: {t['summary'][:150]}...")
        print(f"Score:   {t['score']}")
