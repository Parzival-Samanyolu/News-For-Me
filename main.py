"""
main.py
-------
Orchestrator for the Turkish AI News Automation System.
Runs the full pipeline: fetch → filter → generate → image → publish.
Designed to be triggered by GitHub Actions 3x/day.

Usage:
  python main.py

Required environment variables (set as GitHub Secrets):
  GEMINI_API_KEY       - Google Gemini API key (free tier)
  WP_URL               - Your WordPress site URL (e.g. https://yoursite.com)
  WP_USER              - WordPress admin username
  WP_APP_PASSWORD      - WordPress Application Password
  PEXELS_API_KEY       - Pexels API key for images (free, optional)
  GNEWS_API_KEY        - GNews API key (free tier, optional)
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

from fetch_news import fetch_top_topics, save_published_articles
from generate_article import configure_gemini, generate_article
from fetch_image import get_featured_image_id
from publish_to_wp import WordPressPublisher


# ─────────────────────────────────────────────
# CONFIG (from environment variables)
# ─────────────────────────────────────────────
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
WP_URL          = os.environ.get("WP_URL", "")
WP_USER         = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
PEXELS_API_KEY  = os.environ.get("PEXELS_API_KEY", "")
GNEWS_API_KEY   = os.environ.get("GNEWS_API_KEY", "")
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "1"))  # 1 per run × 3 runs/day = 3/day


def validate_env():
    """Fail fast if required secrets are missing."""
    missing = []
    for var in ["GEMINI_API_KEY", "WP_URL", "WP_USER", "WP_APP_PASSWORD"]:
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        print(f"[FATAL] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def log_run_summary(results: list[dict]):
    """Print and save a run summary log."""
    timestamp = datetime.now(timezone.utc).isoformat()
    print("\n" + "═" * 60)
    print(f"  RUN SUMMARY — {timestamp}")
    print("═" * 60)
    print(f"  Articles published: {len(results)}")
    for r in results:
        status = "✓" if r.get("success") else "✗"
        print(f"  {status} {r.get('title', 'Unknown')[:55]}")
        if r.get("post_url"):
            print(f"    → {r['post_url']}")
        if r.get("error"):
            print(f"    ✗ Error: {r['error']}")
    print("═" * 60 + "\n")

    # Append to run_log.json (GitHub Actions will persist this via artifact or commit)
    log_file = "run_log.json"
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = []
    logs.append({"timestamp": timestamp, "results": results})
    logs = logs[-100:]  # Keep last 100 runs
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def run():
    """Main pipeline execution."""
    print("\n" + "─" * 60)
    print(f"  AI NEWS SYSTEM — Starting run at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("─" * 60)

    # 1. Validate environment
    validate_env()

    # 2. Connect to WordPress
    wp = WordPressPublisher(WP_URL, WP_USER, WP_APP_PASSWORD)
    if not wp.test_connection():
        print("[FATAL] Cannot connect to WordPress. Aborting.")
        sys.exit(1)

    # 3. Configure Gemini (google-genai client)
    client = configure_gemini(GEMINI_API_KEY)
    print("[OK] Gemini client ready (google-genai / gemini-2.5-flash)")

    # 4. Fetch top topics (already filtered for Turkish domestic politics)
    topics = fetch_top_topics(
        count=ARTICLES_PER_RUN + 2,  # fetch extra in case some are skipped
        gnews_api_key=GNEWS_API_KEY
    )

    if not topics:
        print("[WARN] No fresh topics found. Nothing to publish today.")
        log_run_summary([])
        return

    # 5. Generate and publish articles
    results = []
    newly_published = []
    articles_published = 0

    for topic in topics:
        if articles_published >= ARTICLES_PER_RUN:
            break

        print(f"\n{'─'*50}")
        print(f"[PIPELINE] Processing topic {articles_published + 1}/{ARTICLES_PER_RUN}")

        result = {"title": topic["title"], "success": False}

        # Generate article with Gemini (google-genai client)
        article = generate_article(topic, client)
        if not article:
            result["error"] = "generation_failed_or_filtered"
            results.append(result)
            time.sleep(3)
            continue

        result["title"] = article["title"]

        # Fetch and upload featured image
        media_id = None
        if PEXELS_API_KEY:
            image_query = article.get("image_search_query", article.get("focus_keyword", "news"))
            media_id = get_featured_image_id(
                search_query=image_query,
                pexels_key=PEXELS_API_KEY,
                wp_url=WP_URL,
                wp_user=WP_USER,
                wp_app_password=WP_APP_PASSWORD
            )
        else:
            print("[INFO] No Pexels key set — skipping featured image")

        # Publish to WordPress
        pub_result = wp.publish_article(article, featured_media_id=media_id)

        if pub_result:
            result["success"] = True
            result["post_url"] = pub_result["post_url"]
            result["post_id"] = pub_result["post_id"]
            newly_published.append({
                "title": topic["title"],
                "summary": topic.get("summary", ""),
                "generated_title": article["title"],
            })
            articles_published += 1
            print(f"[✓] Published: {article['title'][:65]}")
        else:
            result["error"] = "wordpress_publish_failed"
            print(f"[✗] Failed to publish: {article['title'][:65]}")

        results.append(result)

        # Rate limit — be polite to APIs
        if articles_published < ARTICLES_PER_RUN:
            print("[INFO] Waiting 15s before next article...")
            time.sleep(15)

    # 6. Save published articles (title + summary) to avoid republishing
    if newly_published:
        save_published_articles(newly_published)

    # 7. Log summary
    log_run_summary(results)

    # Exit with error code if nothing was published
    if articles_published == 0:
        print("[WARN] No articles were successfully published this run.")
        sys.exit(1)


if __name__ == "__main__":
    run()
