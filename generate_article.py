def build_article_prompt(topic: dict) -> str:
    """
    Build a detailed prompt for Gemini to generate a full Turkish article.
    The prompt enforces viral tone, structure, and SEO requirements.
    """
    title = topic["title"]
    summary = topic.get("summary", "")
    url = topic.get("url", "")

    prompt = f"""Sen Türkiye'nin en büyük teknoloji ve ekonomi haber platformunda Baş Editörsün. 
Yazım dilin profesyonel, otoriter ama aynı zamanda 'viral' etki yaratacak kadar heyecan verici olmalı.

KAYNAK BAŞLIK: {title}
KAYNAK ÖZET: {summary}
KAYNAK URL: {url}

---
⛔ KESİN YASAK — TÜRK İÇ SİYASETİ: 
Türkiye'deki siyasi partiler, politikacılar (Erdoğan, Özel, vb.) ve yerel seçimlerle ilgili hiçbir şey yazma. 
Bu kural ihlal edilirse JSON'da error: "turkish_domestic_politics" döndür.

✅ ÖNCELİKLİ KONULAR: 
Startup ekosistemi, Global Dev Şirketler (Apple, Tesla, Google, Nvidia vb.), Yapay Zeka, Fintek, Uzay Teknolojileri ve Global Ekonomi.

---
KRİTİK TALİMATLAR (KALİTE İÇİN):
1. GENELLEYİCİ OLMA: "Bir şirket", "bazı uzmanlar", "yeni bir teknoloji" gibi yuvarlak ifadeler kullanma. Kaynakta geçen marka, kişi, model ve rakamları ($, %, adet) mutlaka kullan.
2. SEKTÖREL BAĞLAM: Haberi yazarken konunun sektördeki devlerle (Örn: Apple vs Samsung, Tesla vs BYD) olan rekabetine değin. 
3. OTORİTER TON: Okuyucuya "bu haberi sadece bizden öğrenebilirsiniz" hissi ver. 
4. TÜRKİYE ETKİSİ: Bu gelişmenin Türkiye pazarına, Türk kullanıcılarına veya Türk girişimlerine olası etkisini (fiyatlar, erişilebilirlik vb.) mantıklı bir şekilde analiz et.

---
YAZIM KURALLARI:
1. BAŞLIK: En az 3 versiyon üret. En az biri "rakam" veya "zaman" vurgusu içermeli (Örn: "Sadece 24 Saat Kaldı", "10 Milyar Dolarlık İmzalar Atıldı").
2. GİRİŞ: Haberin 'neden' şimdi patladığını anlatan, pasif değil aktif cümlelerle dolu bir giriş.
3. ANA İÇERİK: 
   - Alt başlıklar (H2) sadece konu başlığı değil, merak uyandıran cümleler olsun.
   - Her paragrafta en az bir teknik terim veya spesifik veri (donanım özellikleri, borsa değeri, yatırım miktarı vb.) yer almalı.
4. SONUÇ: Okuyucuyu yorum yapmaya veya haberi paylaşmaya iten bir "Call to Action" ile bitir.

---
ÇIKTI FORMATI (Kesinlikle bu JSON formatında döndür):

{{
  "title": "Seçilen en iyi başlık",
  "title_alternatives": ["2. başlık seçeneği", "3. başlık seçeneği"],
  "content_html": "<p>Giriş...</p><h2>Alt Başlık</h2><p>Detaylar...</p><h2>Alt Başlık 2</h2><p>Analiz...</p><h2>Sonuç</h2><p>Kapanış...</p>",
  "excerpt": "150-200 karakterlik ilgi çekici özet",
  "meta_description": "SEO meta açıklama",
  "focus_keyword": "ana anahtar kelime",
  "keywords": "kelime1, kelime2, kelime3, kelime4, kelime5",
  "category": "Kategori",
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5"],
  "image_search_query": "İngilizce spesifik arama terimi (Örn: 'Tesla Model 2 budget electric car')"
}}"""

    return prompt
