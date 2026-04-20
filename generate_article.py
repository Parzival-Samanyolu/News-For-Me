```python
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
GEMINI_MODEL = "gemini-2.5-flash"


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
KONTROL NOKTASI (İÇ SİYASET FİLTRESİ):
Eğer bu haber konusu Türk iç siyaseti, Türk siyasi partileri (AKP, CHP vb.), Türk siyasiler, seçimler veya Türk polisiye olayları ile ilgiliyse, haberi YAZMA ve sadece şu JSON'u döndür:
{{"error": "turkish_domestic_politics", "title": "", "content_html": ""}}

✅ İZİN VERİLENLER: Teknoloji, oyun, spor, startup, uluslararası haberler, küresel ekonomi, bilim ve genel dünyadan gelişmeler tamamen serbesttir. (Startup ve teknoloji odaklı haberlere öncelik ver).

---
YAZIM KURALLARI (Haberi yazıyorsan bu kurallara KESİNLİKLE uy):

1. ÖZEL İSİMLERİ VE DETAYLARI KULLAN (ÇOK ÖNEMLİ!):
   - Metni asla jenerikleştirme! Kaynakta geçen şirket isimlerini, CEO'ları, ürün adlarını, araştırmacıları ve ülkeleri cesurca kullan.
   - Rakamları, istatistikleri ve spesifik verileri mutlaka habere dahil et.

2. BAŞLIK (3 seçenek üret, en iyisini seç):
   - Merak uyandırıcı, soru işareti veya ünlem içermeli (8-12 kelime arası).
   - Sayılar, "İşte", "Ortaya Çıktı", "Şok Eden", "Tarihi" gibi güçlü ifadeler kullan.
   - SEO dostu: Ana anahtar kelimeyi başa koy.

3. GİRİŞ PARAGRAFI (2-3 cümle):
   - Okuyucuyu hemen çekecek çarpıcı bir açılış yap.
   - Konunun (ve bahsi geçen şirket/kişilerin) neden önemli olduğunu hemen anlat.

4. ANA İÇERİK (4-5 paragraf, her biri 80-120 kelime):
   - Her paragrafa güçlü bir alt başlık koy (H2 formatında).
   - Konuyu detaylarıyla, isimler vererek açıkla.
   - Gerçekçi alıntılar veya istatistikler ekle. 
   - Mümkünse teknoloji/ekonomi bağlamında Türkiye'deki kullanıcıları nasıl etkileyeceğine dair mantıklı bir bağlantı kur.

5. SONUÇ:
   - Bu gelişmenin (şirketin, teknolojinin vs.) gelecekte ne anlama geleceğini özetle.
   - Okuyucuya soru sorarak bitir.

6. SEO META VERİLERİ:
   - Meta açıklama (150-160 karakter), Anahtar kelimeler (5-8 adet), Odak anahtar kelime (1 adet).
   - Kategori (Teknoloji/Dünya/Ekonomi/Spor/Sağlık/Bilim/Gündem'den biri).
   - Etiketler (5-7 etiket).

---
ÇIKTI FORMATI (kesinlikle sadece aşağıdaki JSON formatında döndür, başka hiçbir açıklama yazma):

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
                    temperature=0.85,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()

            # Clean JSON formatting
            raw = re.sub(r"^

```
