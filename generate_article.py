"""
generate_article.py
-------------------
AI content generation module using Google Gen AI SDK (google-genai).
Takes a news topic and generates a full Turkish viral-style article
with SEO metadata, clickbait title variants, and structured HTML content.
"""

from google import genai
from google.genai import types
import json
import re
import time

# Model to use — gemini-2.5-flash is fast, free-tier eligible, and great for Turkish
GEMINI_MODEL = "gemini-2.5-flash-lite"


def configure_gemini(api_key: str) -> genai.Client:
    """Initialize and return a Google Gen AI client."""
    return genai.Client(api_key=api_key)


def build_article_prompt(topic: dict) -> str:
    """
    Build a detailed prompt for Gemini to generate a full Turkish article.
    The prompt enforces viral tone, structure, and SEO requirements.
    """
    title = topic["title"]
    summary = topic.get("summary", "")
    url = topic.get("url", "")

    prompt = f"""Sen Türkiye'nin en popüler haber sitelerinden birinin baş editörüsün.
Görevin: Aşağıdaki konuyu viral, clickbait tarzında, Türkçe olarak haberleştirmek.

KAYNAK BAŞLIK: {title}
KAYNAK ÖZET: {summary}
KAYNAK URL: {url}

---
⛔ KESİN YASAK — TÜRK İÇ SİYASETİ: Bu haber sitesi Türk iç siyaseti YAZMAZ. 
Aşağıdakilerden herhangi birini içeren konuları kesinlikle haberleştirme ve içerikte hiç bahsetme:
 •⁠ ⁠Türk siyasi partileri (AKP, CHP, MHP, HDP, İYİ Parti vb.)
 •⁠ ⁠Türk politikacılar (Erdoğan, Kılıçdaroğlu, Özel, Bahçeli, İmamoğlu vb.)
 •⁠ ⁠TBMM, Türkiye seçimleri, Türkiye muhalefeti, koalisyon, kabine değişiklikleri
 •⁠ ⁠Türkiye yerel seçimleri veya belediye başkanlığı haberleri Siyaset haberleri, Polisiye haberler,  

Eğer kaynak konu Türk iç siyasetiyle ilgiliyse, şu JSON'u döndür ve DUR:
{{"error": "turkish_domestic_politics", "title": "", "content_html": ""}}
✅ İZİN VERİLENLER: Yazman gereken haberler; Teknoloji, oyunlar, spor, startup habeleri, Uluslararası haberler, Türkiye'nin dış politikası, ekonomisi, turizmi ve diğer global gelişmeler tamamen serbesttir.
Her Zaman Startup ve teknoloji odaklı haberlere öncelik ver
---
YAZIM KURALLARI:
1. BAŞLIK (3 seçenek üret, en iyisini seç):
   - Merak uyandırıcı, soru işareti veya ünlem içermeli
   - 8-12 kelime arası olmalı
   - Sayılar, güçlü sıfatlar, "İşte", "Ortaya Çıktı", "Şok Eden", "Tarihi" gibi güçlü ifadeler kullan
   - SEO dostu: Ana anahtar kelimeyi başa koy

2. GİRİŞ PARAGRAFI (2-3 cümle):
   - Okuyucuyu hemen çekecek çarpıcı bir açılış
   - Neden önemli olduğunu hemen anlat
   - Merak yaratacak bir cümleyle bitir

3. ANA İÇERİK (4-5 paragraf, her biri 80-120 kelime):
   - Her paragrafa güçlü bir alt başlık koy (H2 formatında)
   - Konuyu derinlemesine açıkla
   - İstatistikler, alıntılar veya gerçekler ekle (gerçekçi ve mantıklı olmalı)
   - Okuyucuyu meşgul edecek aktif bir ses tonu kullan
   - Türkiye bağlantısı kur (mümkünse)

4. SONUÇ:
   - Gelecekteki gelişmelere işaret et
   - Okuyucuya ne yapması gerektiğini söyle veya soru sor

5. SEO META VERİLERİ:
   - Meta açıklama (150-160 karakter)
   - Anahtar kelimeler (5-8 adet, virgülle ayrılmış)
   - Odak anahtar kelime (1 adet)
   - Kategori (Teknoloji/Dünya/Ekonomi/Spor/Sağlık/Bilim/Gündem'den biri)
   - Etiketler (5-7 etiket, virgülle ayrılmış)

---
ÇIKTI FORMATI (kesinlikle bu JSON formatında döndür, başka hiçbir şey yazma):

{{
  "title": "Seçilen en iyi başlık",
  "title_alternatives": ["2. başlık seçeneği", "3. başlık seçeneği"],
  "content_html": "<p>Giriş paragrafı...</p><h2>Alt Başlık 1</h2><p>Paragraf...</p><h2>Alt Başlık 2</h2><p>Paragraf...</p><h2>Alt Başlık 3</h2><p>Paragraf...</p><h2>Alt Başlık 4</h2><p>Paragraf...</p><h2>Sonuç</h2><p>Sonuç paragrafı...</p>",
  "excerpt": "150-200 karakterlik çekici özet",
  "meta_description": "SEO meta açıklama (150-160 karakter)",
  "focus_keyword": "ana anahtar kelime",
  "keywords": "kelime1, kelime2, kelime3, kelime4, kelime5",
  "category": "Kategori adı",
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5"],
  "image_search_query": "Pexels için İngilizce arama terimi (2-4 kelime)"
}}"""

    return prompt


def generate_article(topic: dict, client: genai.Client, retries: int = 3) -> dict | None:
    """
    Generate a full article from a topic using the Google Gen AI client.
    Returns parsed JSON dict or None on failure.
    """
    prompt = build_article_prompt(topic)

    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Generating article (attempt {attempt}): {topic['title'][:60]}")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,       # creative but not hallucinating
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()

            # Strip markdown code fences if Gemini wraps in ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            article = json.loads(raw)

            # Hard stop: Gemini itself flagged this as Turkish domestic politics
            if article.get("error") == "turkish_domestic_politics":
                print(f"[SKIP] Gemini refused topic (Turkish domestic politics): {topic['title'][:60]}")
                return None

            # Validate required fields
            required = ["title", "content_html", "excerpt", "meta_description",
                        "focus_keyword", "category", "tags"]
            missing = [k for k in required if k not in article]
            if missing:
                print(f"[WARN] Missing fields in response: {missing}")
                if attempt < retries:
                    time.sleep(5)
                    continue

            # Add internal linking placeholder comments
            article["content_html"] = add_internal_link_hooks(article["content_html"])

            # Add source reference at bottom
            if topic.get("url"):
                article["content_html"] += (
                    f'\n<p class="news-source"><small>'
                    f'<em>Kaynak bilgi için: '
                    f'<a href="{topic["url"]}" target="_blank" rel="noopener">orijinal haber</a>'
                    f'</em></small></p>'
                )

            print(f"[OK] Article generated: {article['title'][:70]}")
            return article

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse failed (attempt {attempt}): {e}")
            print(f"[DEBUG] Raw response snippet: {raw[:300]}")
            if attempt < retries:
                time.sleep(8)
        except Exception as e:
            print(f"[ERROR] Gemini API error (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(10)

    print(f"[FAIL] Could not generate article after {retries} attempts.")
    return None


def add_internal_link_hooks(html: str) -> str:
    """
    Add WordPress internal link shortcode hooks after every 2nd paragraph.
    These will be processed by a WordPress plugin to inject related posts.
    """
    # Insert a related posts shortcode after the 2nd <p> tag
    paragraphs_seen = 0
    result = []
    for line in html.split("\n"):
        result.append(line)
        if "<p>" in line or line.strip().startswith("<p"):
            paragraphs_seen += 1
            if paragraphs_seen == 2:
                result.append(
                    '\n<div class="related-posts-inline">'
                    '[related_posts_by_tax]'
                    '</div>\n'
                )
    return "\n".join(result)


def estimate_word_count(html: str) -> int:
    """Estimate word count of HTML content (strips tags first)."""
    text = re.sub(r"<[^>]+>", " ", html)
    words = text.split()
    return len(words)


if __name__ == "__main__":
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Set GEMINI_API_KEY environment variable to test.")
    else:
        client = configure_gemini(api_key)
        test_topic = {
            "title": "Tesla reveals new affordable electric car for global markets",
            "summary": "Tesla has announced a new budget-friendly electric vehicle targeting emerging markets with a price point under $25,000.",
            "url": "https://example.com/tesla-new-car"
        }
        result = generate_article(test_topic, client)
        if result:
            print("\n--- GENERATED ARTICLE ---")
            print(f"Title: {result['title']}")
            print(f"Category: {result['category']}")
            print(f"Tags: {result['tags']}")
            print(f"Focus KW: {result['focus_keyword']}")
            print(f"Word count: {estimate_word_count(result['content_html'])}")
            print(f"Meta desc: {result['meta_description']}")


