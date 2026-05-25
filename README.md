<div align="center">

<br/>

```
██████╗ ██╗ █████╗ ███████╗
██╔══██╗██║██╔══██╗██╔════╝
██████╔╝██║███████║███████╗
██╔══██╗██║██╔══██║╚════██║
██████╔╝██║██║  ██║███████║
╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝
     AUDITOR
```

# Indian News Bias Auditor

**A real-time NLP/ML pipeline that scrapes, scores, and surfaces political bias,<br/>emotional intensity, clickbait, and framing divergence across 8 major Indian outlets.**

<br/>

[![Live Demo](https://img.shields.io/badge/LIVE_DEMO-bias--checker--00.streamlit.app-4361EE?style=for-the-badge&logo=streamlit&logoColor=white)](https://bias-checker-00.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-4CC9F0?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-F72585?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-2DC653?style=for-the-badge)](LICENSE)

<br/>

</div>

---

<div align="center">

![Dashboard Screenshot](Screenshot.png)

*Live dashboard showing outlet bias scores, emotion intensity, and framing divergence*

</div>

---

## What This Is

No labeled dataset exists for Indian media bias. This project builds one from scratch — scraping 8 major outlets daily, running four independent NLP analyzers on every article, and surfacing the results in a public dashboard anyone can use.

It's not a fact-checker. It's a **pattern detector** — measuring *how* outlets cover the news, not whether they're right or wrong.

---

## How The Pipeline Works

```
RSS Feeds (8 outlets)
       │
       ▼
  feedparser + httpx                    ← custom headers bypass anti-scrape walls
       │
       ▼
  trafilatura + BeautifulSoup4          ← extract full article bodies
       │
       ▼
  SQLite (articles.db)                  ← deduplicated local store
       │
       ├──▶ Emotion Scorer              ← distilroberta-base (1.0 − neutral_prob)
       │
       ├──▶ Sensationalism Index        ← distilroberta-clickbait (0–100 scale)
       │
       ├──▶ Entity Sentiment            ← spaCy NER + distilbert-sst2 context scoring
       │
       └──▶ Framing Divergence          ← sentence-transformers embeddings + emotion variance
                   │
                   ▼
          Outlet Profiles (30-day rolling aggregates)
                   │
                   ▼
          Streamlit Dashboard → public URL
```

---

## Four Analysis Lenses

### 🌡️ Emotion Intensity
Measures non-neutral emotional language using `j-hartmann/emotion-english-distilroberta-base`.
Score = `1.0 − neutral_probability`. Higher = more emotionally charged coverage.

> *"Parliament passes budget"* → **0.08** &nbsp;&nbsp;&nbsp; *"Opposition stages disgraceful walkout!"* → **0.87**

### 📢 Sensationalism Index
Detects clickbait and urgency hooks using `valurank/distilroberta-clickbait`.
Scores each headline 0–100 for vague teasers, artificial urgency, and emotional superlatives.

> *"RBI raises repo rate by 25 bps"* → **8** &nbsp;&nbsp;&nbsp; *"You won't believe what this minister said"* → **91**

### 🧑‍⚖️ Entity Sentiment Context
Extracts major Indian political entities via spaCy (`en_core_web_sm`), locates surrounding sentences, and scores contextual sentiment using `distilbert-base-uncased-finetuned-sst-2-english`.
Range: `−1.0` (negative) to `+1.0` (positive). Aggregated per outlet over 30 days — reveals systematic editorial slant.

### 🪞 Headline Framing Divergence
Embeds all headlines using `paraphrase-multilingual-MiniLM-L12-v2`, clusters same-event cross-outlet coverage by semantic similarity (`> 0.75`), then computes framing divergence as absolute emotion variance between matched pairs.
High divergence = same event, radically different editorial framing.

---

## Outlets Covered

| Outlet | Editorial Lean | RSS Feed |
|---|---|---|
| The Wire | Left / Liberal | [↗](https://thewire.in/feed) |
| Scroll | Left / Liberal | [↗](https://scroll.in/feed) |
| The Hindu | Center-Left | [↗](https://www.thehindu.com/feeder/default.rss) |
| Indian Express | Center | [↗](https://indianexpress.com/feed/) |
| The Print | Center | [↗](https://theprint.in/feed/) |
| NDTV | Center | [↗](https://feeds.feedburner.com/ndtvnews-top-stories) |
| Republic World | Right / Nationalist | [↗](https://www.republicworld.com/rss.xml) |
| OpIndia | Right / Nationalist | [↗](https://www.opindia.com/feed/) |

> **Note on lean labels:** These reflect widely-cited media analysis (MBFC, academic literature) and are used as weak supervision priors — not editorial judgments.

---

## Run It Locally

**Requirements:** Python 3.10+, ~4GB RAM for transformer models, ~2GB disk

```bash
# 1. Clone and set up
git clone https://github.com/vintiw6/Bias-Checker.git
cd Bias-Checker
python -m venv .venv

source .venv/bin/activate       # macOS / Linux
.venv\Scripts\activate          # Windows

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

```bash
# 2. Scrape latest articles (hits all 8 RSS feeds, stores in SQLite)
python src/scraper.py
```

```bash
# 3. Run the NLP scoring pipeline (downloads models on first run ~2GB)
python src/runner.py
```

```bash
# 4. Launch the dashboard
streamlit run dashboard/app.py
```

Dashboard opens at `http://localhost:8501`

---

## Project Structure

```
Bias-Checker/
├── src/
│   ├── scraper.py          ← RSS fetch + article extraction
│   ├── runner.py           ← NLP scoring pipeline (all 4 analyzers)
│   ├── aggregator.py       ← outlet-level score aggregation + story pairing
│   ├── emotion.py          ← emotion intensity module
│   ├── clickbait.py        ← sensationalism detection module
│   ├── entity.py           ← NER + entity sentiment module
│   └── db.py               ← SQLite helper (read/write/dedup)
├── dashboard/
│   └── app.py              ← Streamlit multi-page dashboard
├── data/
│   ├── outlets.json        ← outlet config (name, RSS URL, lean label)
│   └── articles.db         ← SQLite database (gitignored)
├── Screenshot.png
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| **Data collection** | `feedparser`, `httpx`, `trafilatura`, `BeautifulSoup4` |
| **Storage** | `SQLite` (local), `pandas` |
| **Emotion scoring** | `j-hartmann/emotion-english-distilroberta-base` |
| **Clickbait detection** | `valurank/distilroberta-clickbait` |
| **Named entity recognition** | `spaCy en_core_web_sm` |
| **Entity sentiment** | `distilbert-base-uncased-finetuned-sst-2-english` |
| **Framing embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Dashboard** | `Streamlit`, `Plotly` |
| **Deployment** | Streamlit Community Cloud |

All models are free and run locally — **zero API costs.**

---

## Dashboard Pages

| Page | What It Shows |
|---|---|
| **Bias Meter** | Diverging bar chart — all outlets on a Left ↔ Right axis, color-coded |
| **Leaderboard** | Ranked table by composite score with inline sparkbars, exportable CSV |
| **Story Compare** | Side-by-side framing comparison for matched cross-outlet story pairs |
| **Trends** | Time-series bias and emotion scores with political event overlays |

---

## Methodology & Limitations

Scores are **descriptive statistical patterns**, not editorial verdicts.

- Bias scores are heuristic (emotion + clickbait + lean prior) — not a trained classifier
- Models were not fine-tuned on Indian news data (Phase 4 roadmap item)
- English-only analysis for now — Hindi outlets require MuRIL (Phase 3)
- Same-event pairing uses similarity threshold `> 0.75` — some pairs may not be genuine matches
- No outlet should be characterized solely based on these scores

The goal is to surface patterns worth investigating, not to declare winners and losers.

---

## Roadmap

- [x] **Phase 1 — 1-Day Prototype** · 8 outlets · 4 NLP analyzers · Streamlit dashboard · Deployed
- [ ] **Phase 2 — GCP Automation** · Cloud Scheduler + Cloud Run Jobs · BigQuery persistent storage · CI/CD via GitHub Actions
- [ ] **Phase 3 — Hindi Support** · MuRIL multilingual model · Dainik Bhaskar, Amar Ujala, Navbharat Times
- [ ] **Phase 4 — Weak Supervision** · Snorkel labeling functions · Fine-tuned Indian bias classifier · Open dataset on HuggingFace

---

## Why This Matters

There is no labeled dataset for Indian media bias. Tools like AllSides and MBFC cover only a handful of Indian outlets and none offer programmatic, real-time scoring.

This project is a step toward quantitative media literacy for the Indian news ecosystem — and a first attempt at building the infrastructure that makes systematic analysis possible.

---

<div align="center">

**Built in a day. Designed to last.**

[Live Demo](https://bias-checker-00.streamlit.app/) · [Report an Issue](https://github.com/vintiw6/Bias-Checker/issues) · [Contribute](https://github.com/vintiw6/Bias-Checker/pulls)

<br/>

*Scores are descriptive, not verdicts. Always read the original source.*

</div>
