# Task Breakdown — Indian News Bias Auditor (1-Day Build)

Goal: working prototype with live public URL by end of day.
Total time: 8–10 hours. No GCP, no Docker, no fine-tuning — just ship.

---

## Setup (Hour 1)

- [ ] Create project folder: `mkdir india-bias-auditor && cd india-bias-auditor`
- [ ] Create virtual environment: `python -m venv .venv && source .venv/bin/activate`
- [ ] Create `requirements.txt`:
  ```
  feedparser
  httpx
  trafilatura
  transformers
  torch
  sentence-transformers
  spacy
  pandas
  streamlit
  plotly
  shap
  deep-translator
  ```
- [ ] Install deps: `pip install -r requirements.txt`
- [ ] Download spaCy model: `python -m spacy download en_core_web_sm`
- [ ] Create folder structure:
  ```
  india-bias-auditor/
  ├── src/
  │   ├── scraper.py
  │   ├── emotion.py
  │   ├── clickbait.py
  │   ├── entity.py
  │   ├── aggregator.py
  │   └── db.py
  ├── dashboard/
  │   └── app.py
  ├── data/
  │   └── outlets.json
  ├── requirements.txt
  └── README.md
  ```
- [ ] Test that Python imports work: `python -c "import feedparser; import transformers; print('OK')"`

---

## Outlet Config (Hour 1, last 15 min)

- [ ] Create `data/outlets.json`:
  ```json
  {
    "The Wire":       { "rss": "https://thewire.in/feed", "lean": "left" },
    "Scroll":         { "rss": "https://scroll.in/feed", "lean": "left" },
    "The Hindu":      { "rss": "https://www.thehindu.com/feeder/default.rss", "lean": "center-left" },
    "Indian Express": { "rss": "https://indianexpress.com/feed/", "lean": "center" },
    "The Print":      { "rss": "https://theprint.in/feed/", "lean": "center" },
    "NDTV":           { "rss": "https://feeds.feedburner.com/ndtvnews-top-stories", "lean": "center" },
    "Republic World": { "rss": "https://www.republicworld.com/rss.xml", "lean": "right" },
    "OpIndia":        { "rss": "https://www.opindia.com/feed/", "lean": "right" }
  }
  ```
- [ ] Verify feeds manually: open 2–3 URLs in browser, confirm they return XML

---

## Scraper (Hour 2)

- [ ] Write `src/db.py` — SQLite helper:
  - [ ] Function: `init_db()` — create tables if not exist
  - [ ] Table `articles`: `id, outlet, headline, url, body, published_at, scraped_at, lean`
  - [ ] Function: `insert_article(row: dict)`
  - [ ] Function: `get_unscored_articles() -> list[dict]`
  - [ ] Function: `update_scores(id, emotion, clickbait, entity_json)`
  - [ ] Function: `get_all_scored() -> pd.DataFrame`

- [ ] Write `src/scraper.py`:
  - [ ] Load `data/outlets.json`
  - [ ] For each outlet, call `feedparser.parse(rss_url)`
  - [ ] For each entry: extract `title`, `link`, `published`
  - [ ] Fetch article body using `trafilatura.fetch_url()` + `trafilatura.extract()`
  - [ ] Skip if URL already in DB (dedup check)
  - [ ] Insert into SQLite via `db.insert_article()`
  - [ ] Add try/except around each outlet — one broken feed should not stop others
  - [ ] Print progress: `Scraped 12 articles from The Wire`

- [ ] Run and verify: `python src/scraper.py`
- [ ] Open SQLite and confirm rows exist: `sqlite3 data/articles.db "SELECT outlet, COUNT(*) FROM articles GROUP BY outlet;"`
- [ ] Target: 80–150 articles across 8 outlets

---

## Emotion Scorer (Hour 3)

- [ ] Write `src/emotion.py`:
  - [ ] Load model: `j-hartmann/emotion-english-distilroberta-base`
  - [ ] Function: `score_emotion(texts: list[str]) -> list[float]`
    - [ ] Run inference in batches of 16
    - [ ] Return a single float 0–1 (max emotion probability across all emotion classes)
  - [ ] Add progress bar using `tqdm`
  - [ ] Test standalone: `python src/emotion.py` on 5 hardcoded headlines
  - [ ] Verify: "Modi launches brutal crackdown" scores higher than "Parliament session begins"

- [ ] Integrate into runner:
  - [ ] Write `src/runner.py` — pulls unscored articles, runs all analyzers, saves scores
  - [ ] Call `score_emotion()` on all unscored article headlines
  - [ ] Write scores back to SQLite

---

## Clickbait Detector (Hour 4)

- [ ] Write `src/clickbait.py`:
  - [ ] Load model: `mrm8488/bert-mini-finetuned-clickbait`
  - [ ] Function: `score_clickbait(texts: list[str]) -> list[float]`
    - [ ] Run in batches of 32 (smaller model, faster)
    - [ ] Return float 0–100
  - [ ] Test standalone: `python src/clickbait.py`
  - [ ] Verify: "You won't believe what this minister said!" scores > 70
  - [ ] Verify: "RBI raises repo rate by 25 basis points" scores < 30

- [ ] Add to `src/runner.py` — score all unscored articles, save to SQLite

---

## Entity NER (Hour 5)

- [ ] Write `src/entity.py`:
  - [ ] Load spaCy `en_core_web_sm`
  - [ ] Create `data/indian_entities.json` — list of key Indian political entities:
    ```json
    ["Modi", "BJP", "Congress", "Rahul Gandhi", "Amit Shah", "AAP",
     "Kejriwal", "Yogi", "RSS", "TMC", "Mamata", "Opposition"]
    ```
  - [ ] Function: `extract_entities(text: str) -> dict`
    - [ ] Find all spaCy entities (PERSON, ORG, GPE)
    - [ ] Cross-reference with `indian_entities.json`
    - [ ] For each matched entity, score surrounding sentence sentiment
      using `transformers` pipeline `sentiment-analysis`
    - [ ] Return: `{entity_name: sentiment_score}` dict
  - [ ] Function: `top_entities(articles: list[dict]) -> dict`
    - [ ] Aggregate entity sentiment across all articles from one outlet
  - [ ] Test standalone: `python src/entity.py`
  - [ ] Verify: article praising BJP returns positive score for "BJP"

- [ ] Add to `src/runner.py` — store entity JSON in SQLite `entity_json` column

---

## Aggregator (Hour 6)

- [ ] Write `src/aggregator.py`:
  - [ ] Function: `compute_outlet_profiles() -> pd.DataFrame`
    - [ ] Load all scored articles from SQLite
    - [ ] Group by outlet, compute:
      - [ ] `avg_emotion` — mean emotion score
      - [ ] `avg_clickbait` — mean clickbait score
      - [ ] `article_count` — total articles analyzed
      - [ ] `lean` — from outlets.json (ground-truth label)
      - [ ] `top_entities` — most mentioned entity per outlet + its avg sentiment
    - [ ] Add `bias_score`:
      - Simple heuristic for now: `(avg_emotion * 0.5) + (avg_clickbait * 0.3) + lean_offset`
      - `lean_offset`: left = -0.2, center-left = -0.1, center = 0, right = +0.2
      - This gives a -1 to +1 continuous bias score
  - [ ] Function: `get_story_pairs(articles: pd.DataFrame) -> pd.DataFrame`
    - [ ] Load `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
    - [ ] Compute embeddings for all headlines
    - [ ] Find pairs with cosine similarity > 0.75 (same story, different outlet)
    - [ ] Compute framing divergence = emotion_score_A - emotion_score_B
    - [ ] Return top 10 pairs sorted by highest divergence
  - [ ] Test: `python src/aggregator.py` — print outlet profiles table

---

## Streamlit Dashboard (Hour 7)

- [ ] Write `dashboard/app.py` with four sections:

  ### Sidebar
  - [ ] Title: "Indian News Bias Auditor"
  - [ ] Last updated timestamp (from SQLite latest scraped_at)
  - [ ] Nav: Bias Meter | Leaderboard | Story Compare | About

  ### Page 1 — Bias Meter
  - [ ] Horizontal bar chart (Plotly) — one bar per outlet
  - [ ] X-axis: bias_score (-1 to +1), center line at 0
  - [ ] Color: left = blue, center = gray, right = saffron
  - [ ] Tooltip: avg_emotion, avg_clickbait, article_count

  ### Page 2 — Leaderboard
  - [ ] `st.dataframe()` table with columns:
    - Outlet, Bias Score, Emotion Score, Clickbait Score, Articles Analyzed
  - [ ] Sortable by clicking column headers
  - [ ] Download as CSV button: `st.download_button()`

  ### Page 3 — Story Compare
  - [ ] Dropdown: select a story pair from top 10
  - [ ] Side-by-side columns: outlet A vs outlet B
  - [ ] Show: headline, emotion score, clickbait score, top entity sentiment
  - [ ] Framing divergence score shown as a colored badge

  ### Page 4 — About
  - [ ] Short methodology explanation
  - [ ] Links to GitHub and dataset
  - [ ] Disclaimer: scores are descriptive, not verdicts

- [ ] Run locally: `streamlit run dashboard/app.py`
- [ ] Verify all four pages load without errors
- [ ] Verify charts render with real data

---

## Deploy (Hour 8)

- [ ] Create GitHub repo: `india-bias-auditor`
- [ ] Push all code: `git init && git add . && git commit -m "initial commit" && git push`
- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
  - [ ] Sign in with GitHub
  - [ ] Click "New app"
  - [ ] Select repo, branch `main`, main file `dashboard/app.py`
  - [ ] Click Deploy
- [ ] Wait ~3 min for deployment
- [ ] Open public URL, verify dashboard loads
- [ ] Copy URL — this goes on your resume

---

## Buffer / Polish (Hours 9–10)

- [ ] Write `README.md`:
  - [ ] One-line description
  - [ ] Live dashboard link (badge)
  - [ ] How it works (3 bullet points)
  - [ ] How to run locally (4 commands)
  - [ ] Outlets covered (table)
  - [ ] Roadmap (what you'll add next week)
- [ ] Add GitHub topics: `nlp`, `machine-learning`, `india`, `media-bias`, `streamlit`
- [ ] Screenshot the dashboard, add to README
- [ ] Fix any broken charts or layout issues
- [ ] Test on mobile — Streamlit is responsive but check anyway

---

## Definition of Done

By end of day you have:

- [ ] Public URL with live dashboard anyone can visit
- [ ] 80+ real Indian news articles analyzed
- [ ] Bias meter showing all 8 outlets
- [ ] Leaderboard with downloadable CSV
- [ ] Story compare showing real headline pairs
- [ ] GitHub repo with clean README
- [ ] Resume bullet ready:

> Built a live NLP pipeline analyzing political bias, emotional language, and clickbait across 8 Indian news outlets. Scraped 100+ real articles via RSS, scored using HuggingFace transformers (emotion, clickbait, NER), and deployed a public Streamlit dashboard with bias meter, outlet leaderboard, and side-by-side story framing comparison. [link]

---

## What to Build Next (Week 2+)

- [ ] Add GCP automation (Cloud Scheduler + Cloud Run Jobs)
- [ ] Add BigQuery for persistent storage across runs
- [ ] Add Hindi outlets via MuRIL
- [ ] Fine-tune bias classifier on Indian headlines using Snorkel
- [ ] Add trend charts (bias over time)
- [ ] Publish labeled dataset on HuggingFace
- [ ] Write Medium blog post
