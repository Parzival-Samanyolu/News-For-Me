# Autonomous AI News System — Complete Setup Guide
### Turkish Viral News Site · Gemini 2.0 Flash · GitHub Actions · WordPress

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                  FULL PIPELINE (runs 3x/day)                     │
│                                                                  │
│  [GitHub Actions Scheduler]                                      │
│         │  07:00 / 13:00 / 20:00 Turkey time                    │
│         ▼                                                        │
│  [fetch_news.py]                                                 │
│  • Google News RSS (Turkish + World + Tech + Business)           │
│  • GNews API free tier (optional)                                │
│  • Reddit RSS (r/worldnews, r/Turkey)                            │
│  • Score by viral keywords → Deduplicate → Filter TR politics    │
│         │                                                        │
│         ▼                                                        │
│  [generate_article.py]                                           │
│  • Google Gen AI (gemini-2.0-flash)                              │
│  • Turkish viral/clickbait tone                                  │
│  • Full HTML article + SEO metadata                              │
│  • Blocks Turkish domestic politics at prompt level              │
│         │                                                        │
│         ▼                                                        │
│  [fetch_image.py]                                                │
│  • Pexels API free tier → Download → Upload to WP Media          │
│         │                                                        │
│         ▼                                                        │
│  [publish_to_wp.py]                                              │
│  • WordPress REST API                                            │
│  • Auto-create categories & tags                                 │
│  • Inject Yoast SEO meta                                         │
│  • Publish immediately (fully autonomous)                        │
│         │                                                        │
│         ▼                                                        │
│  [published_hashes.json]  ← committed back to repo              │
│  Prevents republishing same story across runs                    │
└──────────────────────────────────────────────────────────────────┘
```

**Cost:** ~$0/month (Gemini free tier + GitHub Actions free tier + Pexels free)  
**Posts:** 3 articles/day (1 per run × 3 scheduled runs)  
**Language:** Turkish  
**Politics filter:** Turkish domestic politics blocked at two layers (fetch + prompt)

---

## STEP 1 — WordPress Setup (Shared Hosting)

### 1.1 Install Required Plugins

Install all of these from **WP Admin → Plugins → Add New**:

| Plugin | Purpose |
|--------|---------|
| **Yoast SEO** | Auto meta titles, descriptions, sitemaps |
| **WP REST API** | Already built into WP 5.0+, just ensure it's active |
| **Google AdSense** (Site Kit by Google) | AdSense integration |
| **Related Posts by Taxonomy** | Inline related posts shortcode `[related_posts_by_tax]` |
| **WP Super Cache** or **LiteSpeed Cache** | Speed — critical for SEO |
| **Smush** | Auto image compression on upload |

### 1.2 Create a WordPress Application Password

This allows the Python script to publish posts without exposing your main password.

1. Go to **WP Admin → Users → Your Profile**
2. Scroll to **Application Passwords**
3. Enter name: `AI News Bot`
4. Click **Add New Application Password**
5. **Copy the generated password immediately** — you won't see it again
6. Format will be: `xxxx xxxx xxxx xxxx xxxx xxxx` (spaces are fine, keep them)

### 1.3 Enable REST API Write Access

The REST API is on by default. Verify it works:
```
https://yoursite.com/wp-json/wp/v2/posts
```
You should see a JSON list of posts.

### 1.4 Recommended WordPress Theme

Use a fast, news-optimised theme for better Core Web Vitals:
- **Newsmag** (paid, ~$59) — best for Turkish news sites
- **Newspaper** (paid, ~$59) — very popular
- **Newsup** (free) — solid free option
- **GeneratePress** (free/paid) — ultra-fast, good for SEO

### 1.5 Configure Yoast SEO

1. Go to **SEO → General → Features**
2. Enable: XML sitemaps, SEO analysis, Readability analysis
3. Go to **SEO → Search Appearance**
4. Set title separator to `|`
5. Submit sitemap to Google Search Console: `https://yoursite.com/sitemap_index.xml`

---

## STEP 2 — Get Your API Keys

### 2.1 Google Gemini API Key (Free)

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Select a Google Cloud project (or create one)
4. Copy the key — starts with `AIza...`

**Free tier limits:**
- gemini-2.0-flash: 15 requests/minute, 1,500/day, 1M tokens/day
- More than enough for 3 articles/day

### 2.2 Pexels API Key (Free, Recommended)

1. Go to [https://www.pexels.com/api/](https://www.pexels.com/api/)
2. Create a free account
3. Click **Your API Key** in the dashboard
4. Free tier: 200 requests/hour, 20,000/month — plenty

### 2.3 GNews API Key (Optional, Free)

1. Go to [https://gnews.io](https://gnews.io)
2. Register for free
3. Free tier: 100 requests/day
4. Adds more fresh Turkish news sources

---

## STEP 3 — GitHub Repository Setup

### 3.1 Create the Repository

```bash
# On your local machine
git init ai-news-site
cd ai-news-site

# Copy all project files here:
# main.py, fetch_news.py, generate_article.py
# fetch_image.py, publish_to_wp.py, requirements.txt
# .github/workflows/publish.yml

git add .
git commit -m "Initial: AI news automation system"

# Create repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/ai-news-site.git
git push -u origin main
```

### 3.2 Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets one by one:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `GEMINI_API_KEY` | Your Gemini API key | ✅ Yes |
| `WP_URL` | `https://yoursite.com` (no trailing slash) | ✅ Yes |
| `WP_USER` | Your WordPress username | ✅ Yes |
| `WP_APP_PASSWORD` | The Application Password from Step 1.2 | ✅ Yes |
| `PEXELS_API_KEY` | Your Pexels API key | Recommended |
| `GNEWS_API_KEY` | Your GNews API key | Optional |

### 3.3 Give GitHub Actions Write Permission

1. Go to repo → **Settings → Actions → General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Click **Save**

This allows the workflow to commit `published_hashes.json` back to the repo.

### 3.4 Test the Pipeline Manually

1. Go to **Actions** tab in your GitHub repo
2. Click **AI News Publisher**
3. Click **Run workflow** → **Run workflow**
4. Watch the logs in real time
5. Check your WordPress site — you should see a new published post

---

## STEP 4 — Google AdSense Setup

### 4.1 Apply for AdSense

1. Go to [https://adsense.google.com](https://adsense.google.com)
2. Add your site URL
3. You need at least 20-30 published articles before applying
4. Approval typically takes 1-2 weeks

### 4.2 Add AdSense to WordPress

Using **Site Kit by Google** plugin:
1. Install & activate Site Kit
2. Go to **Site Kit → Dashboard**
3. Connect Google AdSense
4. Enable **Auto Ads** — Google places ads automatically in optimal positions

Manual placement alternative — add this to your theme's `single.php` after the post content:
```html
<!-- AI News AdSense Block -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
```

---

## STEP 5 — SEO Strategy for Google News

### 5.1 Get Listed on Google News

1. Go to [https://publishercenter.google.com](https://publishercenter.google.com)
2. Add your publication
3. Requirements:
   - Original content (AI-generated + curated is acceptable)
   - Clear author attribution (set AI as "Haber Masası" or similar)
   - About, Contact, Privacy Policy pages
   - Consistent publishing schedule

### 5.2 Technical SEO Checklist

- ✅ Submit sitemap: `https://yoursite.com/sitemap_index.xml` to Google Search Console
- ✅ Ensure each post has a unique meta description (handled by the system)
- ✅ Use HTTPS (free SSL via cPanel Let's Encrypt)
- ✅ Enable Yoast's news sitemap: **SEO → Search Appearance → News SEO**
- ✅ Add Schema markup — Yoast handles `Article` and `NewsArticle` schema automatically
- ✅ Ensure mobile responsiveness (use a mobile-first theme)
- ✅ Page speed target: >70 on PageSpeed Insights

### 5.3 Content Categories to Maximize Traffic

Based on Turkish internet search trends, prioritize these topics:
1. **Teknoloji** — AI, smartphones, Tesla, crypto → highest CTR with viral titles
2. **Dünya** — International breaking news → fastest indexing in Google News
3. **Ekonomi** — Dollar/Euro rates, inflation, global markets → daily search volume
4. **Spor** — International football (Champions League, transfers) → massive Turkish audience
5. **Bilim** — Space, health discoveries → sharable, low competition

### 5.4 Viral Title Formulas That Work in Turkish

The system uses these patterns — they consistently outperform neutral titles:

```
"[Sayı] Şok Eden Gerçek: [Konu] Hakkında Kimsenin Bilmediği Detaylar"
"[Ülke/Şirket] Tarihi Kararını Açıkladı! İşte Dünyayı Sarsacak Gelişme"
"[Konu] İçin Son Dakika! [Etki] Olacak mı?"
"Uzmanlar Uyardı: [Konu]'nda Büyük Tehlike Kapıda"
"[X] Yıl Sonra İlk Kez: [Olay] Yaşandı"
```

---

## STEP 6 — Monitoring & Maintenance

### 6.1 Check Runs Daily (First Week)

- Go to **GitHub → Actions** to see each run's logs
- Run artifacts contain `run_log.json` with publish results
- Check your WordPress admin → Posts for newly published articles

### 6.2 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` from WordPress | Wrong app password | Regenerate Application Password in WP |
| `JSON parse error` from Gemini | Model returned markdown wrapping | Already handled by code; if persists, check API quota |
| No articles found | All topics filtered as TR politics | Check `TR_POLITICS_BLACKLIST_TR` in `fetch_news.py` — may be too aggressive |
| Posts published but no image | Pexels key missing or quota hit | Add `PEXELS_API_KEY` secret or check Pexels dashboard |
| GitHub Actions not triggering | Cron syntax issue | Verify timezone — cron uses UTC, not Turkey time |

### 6.3 Scaling Up (When Ready)

When your site gains traction and you want to scale:

1. **More articles:** Change `ARTICLES_PER_RUN` secret from `1` to `2` → 6 articles/day
2. **More sources:** Add RSS feeds to `RSS_SOURCES` list in `fetch_news.py`
3. **Better hosting:** Migrate to a VPS (DigitalOcean $6/mo) for persistent cron jobs
4. **Upgrade model:** Switch `GEMINI_MODEL` in `generate_article.py` to `gemini-2.0-pro` for longer, deeper articles
5. **Add social sharing:** Use a WP plugin to auto-post to Twitter/X and Facebook when articles publish

---

## File Structure

```
ai-news-site/
├── main.py                          # Pipeline orchestrator
├── fetch_news.py                    # News ingestion + TR politics filter
├── generate_article.py              # Gemini content generation (google-genai)
├── fetch_image.py                   # Pexels image fetcher + WP uploader
├── publish_to_wp.py                 # WordPress REST API publisher
├── requirements.txt                 # Python dependencies
├── published_hashes.json            # Auto-generated: tracks published articles
├── run_log.json                     # Auto-generated: run history
└── .github/
    └── workflows/
        └── publish.yml              # GitHub Actions scheduler (3x/day)
```

---

## Quick Reference — Environment Variables

```bash
# Required
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
WP_URL=https://yoursite.com
WP_USER=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Optional but recommended
PEXELS_API_KEY=your_pexels_key
GNEWS_API_KEY=your_gnews_key
ARTICLES_PER_RUN=1
```

---

*System designed for fully autonomous operation. No human review required.*  
*Turkish domestic politics blocked at both the ingestion layer and AI prompt layer.*  
*Total monthly cost: ~$0 (all free tiers)*
