```python
"""
generate_article.py
-------------------
AI content generation module using Google Gen AI SDK (google-genai).
"""

from google import genai
from google.genai import types
import json
import re
import time

GEMINI_MODEL = "gemini-2.5-flash"

def configure_gemini(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)

def build_article_prompt(topic: dict) -> str:
    title = topic["title"]
    summary = topic.get("summary", "")
    url = topic.get("url", "")

    prompt = f"""Sen Türkiye'nin en popüler haber sitelerinden birinin baş editörüsün.
Görevin: Aşağıdaki konuyu viral, clickbait tarzında, Türkçe olarak haberleştirmek.

KAYNAK BAŞLIK: {title}
KAYNAK ÖZET: {summary}
KAYNAK URL: {url}

---
KONTROL NOKTASI (İÇ SİYASET FİLTRESİ):
Eğer bu haber konusu Türk iç siyaseti, Türk siyasi partileri (AKP, CHP vb.), Türk siyasiler, seçimler veya Türk polisiye olayları ile ilgiliyse, haberi YAZMA ve sadece şu JSON'u döndür:
{{"error": "turkish_domestic_politics", "title": "", "content_html": ""}}

✅ İZİN VERİLENLER: Teknoloji, oyun, spor, startup, uluslararası haberler, küresel ekonomi, bilim ve genel dünyadan gelişmeler tamamen serbesttir. (Startup ve teknoloji odaklı haberlere öncelik ver).

---
YAZIM KURALLARI:
1. ÖZEL İSİMLERİ VE DETAYLARI KULLAN: Metni jenerikleştirme! Şirket isimlerini, CEO'ları, ürün adlarını ve rakamları cesurca kullan.
2. BAŞLIK: Merak uyandırıcı, clickbait tarzı 3 seçenek üret, en iyisini seç.
3. İÇERİK: 4-5 paragraf, H2 alt başlıklar, ilgi çekici ton.
4. SEO: Meta açıklama, odak anahtar kelime, kategori ve etiketleri ekle.

---
ÇIKTI FORMATI (Sadece JSON döndür):
{{
  "title": "Seçilen en iyi başlık",
  "title_alternatives": ["2. başlık", "3. başlık"],
  "content_html": "<p>Giriş...</p><h2>Başlık</h2><p>İçerik...</p>",
  "excerpt": "Özet",
  "meta_description": "SEO açıklama",
  "focus_keyword": "anahtar kelime",
  "keywords": "k1, k2, k3",
  "category": "Kategori",
  "tags": ["t1", "t2"],
  "image_search_query": "English search term"
}}"""
    return prompt

def generate_article(topic: dict, client: genai.Client, retries: int = 3) -> dict | None:
    prompt = build_article_prompt(topic)

    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Generating article (attempt {attempt})")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            
            # JSON temizleme (Regex yerine daha güvenli yöntem)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            article = json.loads(raw)

            if article.get("error") == "turkish_domestic_politics":
                return None

            article["content_html"] = add_internal_link_hooks(article["content_html"])

            if topic.get("url"):
                article["content_html"] += f'\n<p class="news-source"><small><em>Kaynak: <a href="{topic["url"]}" target="_blank">orijinal haber</a></em></small></p>'

            return article

        except Exception as e:
            print(f"[ERROR] Attempt {attempt} failed: {str(e)}")
            time.sleep(5)

    return None

def add_internal_link_hooks(html: str) -> str:
    paragraphs = html.split("</p>")
    if len(paragraphs) > 2:
        paragraphs[1] += '\n<div class="related-posts-inline">[related_posts_by_tax]</div>'
    return "</p>".join(paragraphs)

def estimate_word_count(html: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", html).split())

if __name__ == "__main__":
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        client = configure_gemini(api_key)
        print("Client configured.")

```

