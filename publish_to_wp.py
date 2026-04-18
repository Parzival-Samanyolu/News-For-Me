"""
publish_to_wp.py
----------------
WordPress publisher module using the REST API.
Handles post creation, category/tag management, and Yoast SEO meta injection.
"""

import requests
import json
from datetime import datetime, timezone


class WordPressPublisher:
    """Handles all WordPress REST API interactions."""

    def __init__(self, wp_url: str, username: str, app_password: str):
        """
        wp_url:       Base URL of your WordPress site (e.g. https://yoursite.com)
        username:     WordPress admin username
        app_password: Application Password (generated in WP Admin → Users → Profile)
        """
        self.wp_url = wp_url.rstrip("/")
        self.auth = (username, app_password)
        self.base = f"{self.wp_url}/wp-json/wp/v2"
        self._category_cache = {}
        self._tag_cache = {}

    def _get(self, endpoint: str, params: dict = None) -> dict | list | None:
        try:
            resp = requests.get(
                f"{self.base}{endpoint}",
                auth=self.auth,
                params=params,
                timeout=15
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ERROR] GET {endpoint}: {e}")
            return None

    def _post(self, endpoint: str, payload: dict) -> dict | None:
        try:
            resp = requests.post(
                f"{self.base}{endpoint}",
                auth=self.auth,
                json=payload,
                timeout=30
            )
            if resp.status_code not in (200, 201):
                print(f"[ERROR] POST {endpoint}: {resp.status_code} → {resp.text[:300]}")
                return None
            return resp.json()
        except Exception as e:
            print(f"[ERROR] POST {endpoint}: {e}")
            return None

    def get_or_create_category(self, name: str) -> int | None:
        """Return category ID by name, creating it if it doesn't exist."""
        name = name.strip()
        if name in self._category_cache:
            return self._category_cache[name]

        # Search for existing
        results = self._get("/categories", {"search": name, "per_page": 5})
        if results:
            for cat in results:
                if cat["name"].lower() == name.lower():
                    self._category_cache[name] = cat["id"]
                    return cat["id"]

        # Create new
        result = self._post("/categories", {"name": name})
        if result:
            self._category_cache[name] = result["id"]
            print(f"[INFO] Created category: {name} (ID: {result['id']})")
            return result["id"]
        return None

    def get_or_create_tags(self, tag_names: list[str]) -> list[int]:
        """Return list of tag IDs, creating any that don't exist."""
        tag_ids = []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            if name in self._tag_cache:
                tag_ids.append(self._tag_cache[name])
                continue

            # Search for existing tag
            results = self._get("/tags", {"search": name, "per_page": 5})
            found = False
            if results:
                for tag in results:
                    if tag["name"].lower() == name.lower():
                        self._tag_cache[name] = tag["id"]
                        tag_ids.append(tag["id"])
                        found = True
                        break

            if not found:
                result = self._post("/tags", {"name": name})
                if result:
                    self._tag_cache[name] = result["id"]
                    tag_ids.append(result["id"])

        return tag_ids

    def set_yoast_meta(self, post_id: int, article: dict) -> bool:
        """
        Inject Yoast SEO metadata via REST API.
        Requires Yoast SEO plugin with REST API support enabled.
        """
        try:
            meta_payload = {
                "yoast_head_json": {},
                "meta": {
                    "_yoast_wpseo_title": article.get("title", ""),
                    "_yoast_wpseo_metadesc": article.get("meta_description", ""),
                    "_yoast_wpseo_focuskw": article.get("focus_keyword", ""),
                    "_yoast_wpseo_canonical": "",
                    "_yoast_wpseo_opengraph-title": article.get("title", ""),
                    "_yoast_wpseo_opengraph-description": article.get("meta_description", ""),
                }
            }
            resp = requests.post(
                f"{self.base}/posts/{post_id}",
                auth=self.auth,
                json=meta_payload,
                timeout=15
            )
            if resp.status_code in (200, 201):
                print(f"[OK] Yoast meta set for post {post_id}")
                return True
            else:
                print(f"[WARN] Yoast meta update failed: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[WARN] Yoast meta exception: {e}")
            return False

    def publish_article(
        self,
        article: dict,
        featured_media_id: int | None = None,
        status: str = "publish"
    ) -> dict | None:
        """
        Publish a complete article to WordPress.

        article dict must contain:
          - title
          - content_html
          - excerpt
          - meta_description
          - focus_keyword
          - category
          - tags (list)
          - image_search_query (optional)

        Returns the created post dict or None on failure.
        """
        print(f"\n[INFO] Publishing: {article['title'][:70]}")

        # Resolve category ID
        category_id = self.get_or_create_category(article.get("category", "Gündem"))

        # Resolve tag IDs
        tags = article.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        tag_ids = self.get_or_create_tags(tags)

        # Build post payload
        payload = {
            "title": article["title"],
            "content": article["content_html"],
            "excerpt": article.get("excerpt", ""),
            "status": status,
            "categories": [category_id] if category_id else [],
            "tags": tag_ids,
            "comment_status": "open",
            "ping_status": "open",
            "format": "standard",
        }

        if featured_media_id:
            payload["featured_media"] = featured_media_id

        # Create the post
        result = self._post("/posts", payload)

        if not result:
            print("[FAIL] Post creation failed.")
            return None

        post_id = result["id"]
        post_url = result.get("link", "")
        print(f"[OK] Post created: ID={post_id}, URL={post_url}")

        # Set Yoast SEO metadata
        self.set_yoast_meta(post_id, article)

        return {
            "post_id": post_id,
            "post_url": post_url,
            "title": article["title"],
            "category": article.get("category"),
            "tags": tags,
            "published_at": datetime.now(timezone.utc).isoformat()
        }

    def test_connection(self) -> bool:
        """Verify WordPress REST API connectivity and authentication."""
        result = self._get("/users/me")
        if result and "id" in result:
            print(f"[OK] Connected to WordPress as: {result.get('name', 'unknown')}")
            return True
        print("[ERROR] WordPress connection failed. Check URL, username, and app password.")
        return False


if __name__ == "__main__":
    import os
    wp = WordPressPublisher(
        wp_url=os.environ.get("WP_URL", ""),
        username=os.environ.get("WP_USER", ""),
        app_password=os.environ.get("WP_APP_PASSWORD", "")
    )
    wp.test_connection()
