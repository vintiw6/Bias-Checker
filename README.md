# 🔍 Indian News Bias Auditor — 1-Day Prototype

A fully automated NLP pipeline and premium Streamlit dashboard that scrapes, analyzes, and audits political bias, emotional intensity, clickbait levels, and news framing differences across 8 major Indian news outlets.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

---

## How It Works

1. **RSS Feed Collection**: Programmatically scrapes feeds from all 8 major outlets using custom `httpx` headers to bypass anti-scraping walls, extracting full article bodies using `trafilatura` and fallback `BeautifulSoup4` parser.
2. **Multi-Lens NLP Scoring**:
   - **Emotion Intensity**: Measures non-neutral emotional language using `j-hartmann/emotion-english-distilroberta-base` (computed as `1.0 - neutral_probability`).
   - **Sensationalism Index**: Identifies clickbait and Urgency hooks using `valurank/distilroberta-clickbait`.
   - **Entity Sentiment Context**: Extracts major political entities via spaCy (`en_core_web_sm`), locates their surrounding sentences, and scores the contextual sentiment from `-1.0` (negative) to `+1.0` (positive) using `distilbert-base-uncased-finetuned-sst-2-english`.
3. **Headline Framing Divergence**: Embeds headlines using a multilingual Sentence-Transformer model (`paraphrase-multilingual-MiniLM-L12-v2`), clusters similar cross-outlet story coverage, and computes framing differences based on the absolute variance in headline emotion.

---

## Outlets Covered

| Outlet | Perceived Editorial Lean | RSS Feed URL |
|---|---|---|
| The Wire | Left / Liberal | [Feed](https://thewire.in/feed) |
| Scroll | Left / Liberal | [Feed](https://scroll.in/feed) |
| The Hindu | Center-Left | [Feed](https://www.thehindu.com/feeder/default.rss) |
| Indian Express | Center | [Feed](https://indianexpress.com/feed/) |
| The Print | Center | [Feed](https://theprint.in/feed/) |
| NDTV | Center | [Feed](https://feeds.feedburner.com/ndtvnews-top-stories) |
| Republic World | Right / Nationalist | [Feed](https://www.republicworld.com/rss.xml) |
| OpIndia | Right / Nationalist | [Feed](https://www.opindia.com/feed/) |

---

## How to Run Locally

### 1. Set Up the Environment
Ensure Python 3.10+ is installed:
```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
source .venv/bin/activate    # On macOS/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Scrape News Feed Articles
Fetches the latest 10 news stories per feed and caches them in the SQLite DB:
```bash
python src/scraper.py
```

### 3. Execute the NLP Scoring Pipeline
Performs batch scoring across all models, generating article scores and named entity records:
```bash
python src/runner.py
```

### 4. Run the Aggregator & Dashboard
Launches the interactive Web UI and aggregates metrics:
```bash
streamlit run dashboard/app.py
```

---

## Roadmap

- **Phase 2 — GCP Scaling**: Deploy the scraper and analyzer containers as scheduled GCP Cloud Run Jobs, streaming analytics into a persistent Google BigQuery database.
- **Phase 3 — Hindi Support**: Expand analysis to Hindi media outlets (Amar Ujala, Dainik Bhaskar) using Google's MuRIL multilingual model.
- **Phase 4 — Weak Supervision Fine-Tuning**: Implement Snorkel labeling functions combining MBFC source-level metadata priors and keyword filters to fine-tune a custom domain-specific Indian media bias classifier.
