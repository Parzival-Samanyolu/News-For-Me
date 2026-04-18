"""
fetch_image.py
--------------
Featured image module using Pexels API (free, 200 req/hour).
Downloads a relevant stock photo and uploads it to WordPress Media Library.
"""

import requests
import os
import tempfile
from pathlib import Path


def fetch_pexels_image(query: str, api_key: str) -> dict | None:
    """
    Search Pexels for a relevant stock photo.
    Returns dict with 'url', 'photographer', 'alt_text' or None.
    """
    if not api_key:
        print("[WARN] No PEXELS_API_KEY set, skipping image fetch.")
        return None

    try:
        headers = {"Authorization": api_key}
        params = {
            "query": query,
            "per_page": 5,
            "orientation": "landscape",
            "size": "large"
        }
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params=params,
            timeout=10
        )
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            print(f"[WARN] No Pexels images found for query: {query}")
            return None

        # Pick the first result
        photo = photos[0]
        return {
            "url": photo["src"]["large2x"],   # high-res version
            "photographer": photo.get("photographer", ""),
            "alt_text": query,
            "pexels_id": photo["id"]
        }
    except Exception as e:
        print(f"[ERROR] Pexels fetch failed: {e}")
        return None


def download_image(url: str) -> str | None:
    """Download image to a temp file, return local file path."""
    try:
        resp = requests.get(url, timeout=30, stream=True)
        suffix = ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()
        print(f"[INFO] Image downloaded to {tmp.name}")
        return tmp.name
    except Exception as e:
        print(f"[ERROR] Image download failed: {e}")
        return None


def upload_image_to_wordpress(
    local_path: str,
    alt_text: str,
    wp_url: str,
    wp_user: str,
    wp_app_password: str
) -> int | None:
    """
    Upload a local image file to WordPress Media Library via REST API.
    Returns the WordPress media ID on success, or None.
    """
    try:
        filename = Path(local_path).name
        with open(local_path, "rb") as f:
            image_data = f.read()

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg",
        }
        resp = requests.post(
            f"{wp_url}/wp-json/wp/v2/media",
            headers=headers,
            data=image_data,
            auth=(wp_user, wp_app_password),
            timeout=30
        )

        if resp.status_code in (200, 201):
            media_id = resp.json().get("id")
            # Set alt text
            if media_id and alt_text:
                requests.post(
                    f"{wp_url}/wp-json/wp/v2/media/{media_id}",
                    json={"alt_text": alt_text, "caption": ""},
                    auth=(wp_user, wp_app_password),
                    timeout=10
                )
            print(f"[OK] Image uploaded to WordPress, media ID: {media_id}")
            return media_id
        else:
            print(f"[ERROR] WP media upload failed: {resp.status_code} {resp.text[:200]}")
            return None

    except Exception as e:
        print(f"[ERROR] Image upload exception: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(local_path)
        except Exception:
            pass


def get_featured_image_id(
    search_query: str,
    pexels_key: str,
    wp_url: str,
    wp_user: str,
    wp_app_password: str
) -> int | None:
    """
    High-level function: search Pexels → download → upload to WP.
    Returns WordPress media ID or None.
    """
    print(f"[INFO] Fetching featured image for: '{search_query}'")

    image_info = fetch_pexels_image(search_query, pexels_key)
    if not image_info:
        return None

    local_path = download_image(image_info["url"])
    if not local_path:
        return None

    alt_text = image_info["alt_text"]
    media_id = upload_image_to_wordpress(
        local_path, alt_text, wp_url, wp_user, wp_app_password
    )
    return media_id
