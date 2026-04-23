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

# Model to use — gemini-2.5-flash-lite is fast, free-tier eligible, and great for Turkish
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

    prompt = f"""
Sen magazin haber editörüsün.
Önce tek kategori seç, sonra haberi magazin diliyle yaz.

Kategoriler:
1. Ünlü Haberleri
2. Dizi / Film
3. Magazin Etkinlikleri
4. Moda
5. Sosyal Medya
6. Müzik

Birden fazla uygunsa en üsttekini seç.
Resmî haber dili kullanma.
Başlık SEO uyumlu ve dikkat çekici olsun.

KAYNAK BAŞLIK: {title}
KAYNAK ÖZET: {summary}
KAYNAK URL: {url}

---
KESİN YASAK — SİYASET / POLİSİYE / EKONOMİ / SPOR

Bu içerik sistemi yalnızca magazin odaklı içerik üretir.
İçerikler SEO uyumlu, dikkat çekici, yüksek tıklama potansiyeline sahip olmalı.
Yazılar Google Discover uyumlu olmalı ancak yanıltıcı clickbait kullanılmamalı.

Aşağıdaki konuların herhangi biri varsa içerik üretme:

• Türk iç siyaseti
• Politikacılar
• Siyasi partiler
• Seçimler
• Belediye / devlet yönetimi haberleri
• Cinayet, gözaltı, tutuklama, mahkeme, operasyon gibi polisiye olaylar
• Borsa, ekonomi, finans analizleri
• Spor karşılaşmaları ve spor kulübü haberleri

Eğer kaynak bu konularla ilgiliyse şu JSON'u döndür ve DUR:

{{
  "error": "non_magazine_content",
  "title": "",
  "content_html": ""
}}

✅ İZİN VERİLENLER:
• Ünlü haberleri
• Sanatçı projeleri
• Oyuncu röportajları
• Dizi / film dünyası
• Magazin etkinlikleri
• Moda ve kırmızı halı
• Sosyal medya gündemi
• Ünlü ilişkileri
• Müzik dünyası gelişmeleri

ÖNCELİK SIRASI:
1. Ünlü Haberleri
2. Dizi / Film Dünyası
3. Magazin Etkinlikleri
4. Moda
5. Sosyal Medya Gündemi
6. Müzik Dünyası

Üst sıradaki kategori varsa alt kategoriye geçme.

---
YAZIM KURALLARI:

1. BAŞLIK (3 seçenek üret, en iyisini seç):
   - 8-12 kelime arası olmalı
   - SEO uyumlu olmalı
   - Ana anahtar kelime başa yakın kullanılmalı
   - Güçlü merak duygusu yaratmalı
   - Doğal ve profesyonel görünmeli
   - Google Discover için tıklama potansiyeli yüksek olmalı
   - Abartılı ünlem, tamamen yanıltıcı ifade kullanma

Başlık örnek tonu:
✅ "X'in son paylaşımı sosyal medyada gündem oldu"
✅ "Y'nin yeni projesi hayranlarını heyecanlandırdı"
✅ "Ünlü oyuncunun kırmızı halı tercihi çok konuşuldu"

2. GİRİŞ PARAGRAFI (2-3 cümle):
   - İlk cümle dikkat çekici olmalı
   - Okuyucuda merak duygusu oluşturmalı
   - Haberin neden önemli olduğu net anlatılmalı
   - Magazin etkisi güçlü verilmeli

3. ANA İÇERİK (4-5 paragraf, her biri 80-120 kelime):
   - Her paragrafa H2 alt başlık koy
   - İlk paragrafta olayın özünü ver
   - Sonraki paragraflarda detaylandır
   - Somut isimler, projeler, tarih ve yer bilgileri ekle
   - Kamuoyu etkisini anlat
   - Sosyal medya veya medya yansımasını belirt
   - Gereksiz tekrar yapma
   - Genel ifadeler kullanma

4. SONUÇ:
   - Gelişmenin etkisini özetle
   - Gelecekte ne olabileceğini belirt
   - Okuyucuda merak bırakacak doğal kapanış yap

---
SEO KURALLARI:

• Ana anahtar kelime başlıkta geçmeli
• Ana anahtar kelime giriş paragrafında doğal şekilde geçmeli
• Alt başlıklarda ilgili anahtar kelimeler kullanılmalı
• Cümleler doğal olmalı, anahtar kelime doldurma yapma
• Google Discover için duygusal tetikleyici kullan:
  - şaşırttı
  - gündem oldu
  - dikkat çekti
  - olay yarattı
  - çok konuşuldu
  - hayranlarını heyecanlandırdı

Ama:
❌ "ŞOK!", "İnanamayacaksınız!", "Yok artık!" gibi düşük kalite clickbait yasak.

---
DETAY ZORUNLULUĞU:

Yüzeysel yazmak YASAK.

Kötü örnek:
"Ünlü oyuncu yeni projeye başladı."

İyi örnek:
"Başarılı oyuncu X, dijital platform Y için hazırlanan yeni dizinin başrolü için anlaşma sağladı. Çekimlerin Temmuz ayında İstanbul'da başlaması planlanırken, yapımın sezonun en çok konuşulacak projeleri arasında gösteriliyor."

Mutlaka ekle:
• kişi adları
• proje adları
• marka adları
• etkinlik adı
• tarih bilgisi
• şehir / ülke bilgisi
• medya etkisi
• sosyal medya etkisi

Kişi adı vermeden yazı yazma.
Genel ifadeler kullanma.

Yazının tonu:
• akıcı
• güçlü
• merak uyandırıcı
• SEO uyumlu
• profesyonel magazin editörü dili

Ama ASLA:
• yanıltıcı clickbait
• aşırı abartı
• boş sansasyon kullanma.

---
HUMANIZED WRITING ZORUNLULUĞU:

İçerik robot gibi görünmemeli.

Kurallar:
• İnsan editör diliyle yaz
• Doğal cümle akışı kullan
• Cümle uzunluklarını çeşitlendir
• Aynı kalıpları tekrar etme
• Yapay ve mekanik ifadeler kullanma
• Klişe haber cümlelerini azalt

YASAK KALIPLAR:
• "dikkat çekiyor"
• "öne çıkıyor"
• "önemli bir gelişme olarak değerlendiriliyor"
• "sektörde ses getirdi"

Bu tür tekrar eden kalıplar yerine doğal yaz.

Amaç:
Okuyucu içeriğin yapay zeka tarafından değil editör tarafından yazıldığını hissetsin.

---
SEO META VERİLERİ:

• Meta açıklama: 150-160 karakter
• Anahtar kelimeler: 5-8 adet
• Odak anahtar kelime: 1 adet
• Kategori: Ünlü Haberleri / Dizi-Film / Magazin Etkinlikleri / Moda / Sosyal Medya / Müzik
• Etiketler: 5-7 adet
• image_search_query: İngilizce 2-4 kelime

SEO doğal olmalı.
Anahtar kelime spam yapma.

---
ÇIKTI FORMATI
(Kesinlikle sadece JSON döndür, başka hiçbir şey yazma)

{{
  "title": "Seçilen en iyi başlık",
  "title_alternatives": [
    "Alternatif başlık 1",
    "Alternatif başlık 2"
  ],
  "content_html": "<p>Giriş paragrafı...</p><h2>Alt Başlık 1</h2><p>Paragraf...</p><h2>Alt Başlık 2</h2><p>Paragraf...</p><h2>Sonuç</h2><p>Sonuç paragrafı...</p>",
  "excerpt": "150-200 karakterlik çekici özet",
  "meta_description": "SEO meta açıklama",
  "focus_keyword": "ana anahtar kelime",
  "keywords": "kelime1, kelime2, kelime3, kelime4, kelime5",
  "category": "Ünlü Haberleri",
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5"],
  "image_search_query": "celebrity red carpet event"
}}

"""
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
                    temperature=0.85,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()

            # Strip markdown code fences if Gemini wraps in ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            article = json.loads(raw)

            # BUG FIX: catch both error codes — old politics filter + new magazine filter
            if article.get("error") in ("turkish_domestic_politics", "non_magazine_content"):
                print(f"[SKIP] Gemini refused topic (non-magazine content): {topic['title'][:60]}")
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

            # Strip everything after ":" in the title
            if ":" in article["title"]:
                article["title"] = article["title"].split(":")[0].strip()

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
            "title": "Taylor Swift announces new world tour dates",
            "summary": "Taylor Swift has revealed new dates for her Eras Tour, adding stops in Europe and Asia.",
            "url": "https://example.com/taylor-swift-tour"
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
