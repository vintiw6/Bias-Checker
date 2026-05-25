# Task Breakdown — Indian News Bias Auditor

Fully automated pipeline on Google Cloud Platform. Work in phases — each phase produces something runnable before moving to the next.

---

## Phase 0 — GCP Setup (Day 1, ~2 hours)

- [ ] Create a new GCP project (`india-bias-auditor`)
- [ ] Enable APIs: Cloud Run, Cloud Scheduler, BigQuery, Artifact Registry, Cloud Build, Secret Manager
- [ ] Install Google Cloud SDK locally (`gcloud` CLI)
- [ ] Authenticate: `gcloud auth application-default login`
- [ ] Create BigQuery dataset: `bias_auditor`
- [ ] Create BigQuery tables using schema from `techstack.md`
- [ ] Create Artifact Registry repository: `bias-auditor-images`
- [ ] Set up GitHub repo, connect to Cloud Build

---

## Phase 1 — Scraper (Days 2–4)

### 1.1 RSS Feed Scraper
- [ ] Write `src/scraper/feeds.py` — dict of outlet name → RSS URL for all 14 outlets
- [ ] Write `src/scraper/fetch.py` — use `feedparser` to pull feed entries
- [ ] Extract: headline, URL, published date, outlet name, language tag
- [ ] Write `src/scraper/article.py` — use `trafilatura` to extract full article body from URL
- [ ] Add retry logic and timeout handling (some outlets are flaky)
- [ ] Add deduplication: skip URLs already in BigQuery

### 1.2 Storage
- [ ] Write `src/common/bq_client.py` — BigQuery insert/query helper
- [ ] Write `src/common/local_db.py` — SQLite fallback for local dev
- [ ] Write `src/scraper/run.py` — entry point, reads `--dev` flag to switch storage
- [ ] Test: run locally, verify 50+ articles land in SQLite

### 1.3 Containerize
- [ ] Write `docker/scraper.Dockerfile`
- [ ] Test Docker build locally: `docker build -f docker/scraper.Dockerfile .`
- [ ] Push to Artifact Registry
- [ ] Deploy as Cloud Run Job: `gcloud run jobs create scraper ...`
- [ ] Test manual trigger: `gcloud run jobs execute scraper`
- [ ] Schedule with Cloud Scheduler: daily at 2am IST

### 1.4 Tests
- [ ] `tests/test_scraper.py` — mock feedparser, assert correct fields extracted
- [ ] `tests/test_dedup.py` — assert duplicate URLs are skipped

---

## Phase 2 — NLP Analyzers (Days 5–10)

### 2.1 Environment
- [ ] Add all model dependencies to `requirements.txt`
- [ ] Download and cache models locally (HuggingFace cache dir)
- [ ] Verify MuRIL loads correctly for Hindi headline test

### 2.2 Emotion Scorer (`src/analyzer/emotion.py`)
- [ ] Load `j-hartmann/emotion-english-distilroberta-base`
- [ ] Function: `score_emotion(text: str) -> float` (0–1)
- [ ] Batch processing: process 32 articles at a time for speed
- [ ] For Hindi articles: translate headline to English first using `deep-translator` (free, no API key)
- [ ] Test on 10 manually chosen headlines — verify scores make intuitive sense

### 2.3 NER + Entity Sentiment (`src/analyzer/entity_sentiment.py`)
- [ ] Load spaCy `en_core_web_sm`
- [ ] Build custom entity list: Indian politicians, parties, states, institutions (CSV file)
- [ ] Function: `extract_entities(text: str) -> list[dict]`
- [ ] Each entity dict: `{entity, label, sentiment_score, mentions}`
- [ ] Use `transformers` sentiment classifier for entity-in-context scoring
- [ ] Test: verify "Modi praised the initiative" scores positive for Modi

### 2.4 Clickbait Detector (`src/analyzer/clickbait.py`)
- [ ] Load `mrm8488/bert-mini-finetuned-clickbait`
- [ ] Function: `score_clickbait(headline: str) -> float` (0–100)
- [ ] Test on 20 known clickbait vs non-clickbait Indian headlines
- [ ] If accuracy < 70% on Indian headlines, fine-tune on 500 manually labeled examples in Colab

### 2.5 Framing Analyzer (`src/analyzer/framing.py`)
- [ ] Load `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- [ ] Function: `embed(text: str) -> np.ndarray`
- [ ] Function: `find_story_pairs(articles: list) -> list[tuple]`
  - Compare all articles published within 48h of each other
  - Pair if similarity > 0.75 (same topic)
  - Compute framing divergence = 1 - cosine_similarity between pairs
- [ ] Store pairs in `story_pairs` BigQuery table
- [ ] Test: manually verify 5 pairs are genuinely about the same event

### 2.6 Analyzer Runner (`src/analyzer/run.py`)
- [ ] Pull unscored articles from BigQuery (or SQLite in dev)
- [ ] Run all four analyzers in sequence per article
- [ ] Write scores to `article_scores` table
- [ ] Log: articles processed, time taken, any failures
- [ ] Add SHAP explanation generation for top 10 articles per day (for dashboard)

### 2.7 Containerize
- [ ] Write `docker/analyzer.Dockerfile`
- [ ] Note: image will be large (~3GB with models) — use multi-stage build
- [ ] Deploy as Cloud Run Job
- [ ] Schedule: daily at 3am IST (after scraper finishes)

### 2.8 Tests
- [ ] `tests/test_emotion.py` — assert charged text scores higher than neutral
- [ ] `tests/test_clickbait.py` — assert known clickbait headlines score > 60
- [ ] `tests/test_framing.py` — assert two paraphrased headlines are paired correctly

---

## Phase 3 — Weak Supervision & Dataset (Days 11–14)

### 3.1 Snorkel Labeling Functions (`models/weak_supervision/labeling.py`)
- [ ] Install `snorkel`
- [ ] Write labeling functions:
  - `lf_mbfc_source(article)` — use MBFC source label as prior
  - `lf_right_keywords(article)` — keywords associated with right-leaning framing
  - `lf_left_keywords(article)` — keywords associated with left-leaning framing
  - `lf_emotion_high(article)` — high emotion score → likely opinionated
  - `lf_entity_sentiment(article)` — consistent positive BJP sentiment → right-lean signal
- [ ] Run `LabelModel` from Snorkel to combine functions
- [ ] Generate probabilistic labels for all articles

### 3.2 Manual Seed Labels
- [ ] Create `data/seed_labels.csv` — 200 manually labeled headlines
- [ ] Labels: `left`, `center`, `right`, `unclear`
- [ ] Use these to calibrate and validate Snorkel output

### 3.3 Fine-tune Bias Classifier (Google Colab)
- [ ] Open Colab, mount Drive, install dependencies
- [ ] Load `valurank/distilroberta-bias` as base
- [ ] Fine-tune on Snorkel-labeled Indian headlines
- [ ] Track with W&B (free tier)
- [ ] Save best checkpoint to Drive, then download and commit to `models/bias_classifier/`

### 3.4 Publish Dataset
- [ ] Export labeled dataset to CSV
- [ ] Write dataset card (README with fields, methodology, limitations)
- [ ] Upload to HuggingFace Datasets Hub (free)
- [ ] Upload to Kaggle Datasets (free)

---

## Phase 4 — Aggregator (Days 15–17)

### 4.1 Outlet Profiler (`src/aggregator/profiles.py`)
- [ ] Pull last 30 days of `article_scores` from BigQuery
- [ ] Compute per outlet:
  - `avg_emotion_score`
  - `avg_clickbait_score`
  - `avg_bias_score` (from fine-tuned classifier)
  - `entity_sentiment_summary` — top 5 entities and their average sentiment
  - `article_count` — volume of coverage
- [ ] Write to `outlet_profiles` table with date partition

### 4.2 Story Pair Aggregator (`src/aggregator/story_pairs.py`)
- [ ] Pull today's `story_pairs` from analyzer output
- [ ] Rank pairs by framing divergence (highest = most interesting)
- [ ] Keep top 20 pairs per day for dashboard
- [ ] Write to `story_pairs` table

### 4.3 Aggregator Runner (`src/aggregator/run.py`)
- [ ] Entry point combining profiler and story pair aggregator
- [ ] Containerize, deploy as Cloud Run Job
- [ ] Schedule: daily at 5am IST (after analyzer finishes)

---

## Phase 5 — Dashboard (Days 18–22)

### 5.1 BigQuery Data Layer (`dashboard/data.py`)
- [ ] Function: `get_outlet_profiles(days=30) -> pd.DataFrame`
- [ ] Function: `get_story_pairs(date=today) -> pd.DataFrame`
- [ ] Function: `get_entity_sentiment(outlet, entity) -> pd.DataFrame`
- [ ] Add `@st.cache_data(ttl=3600)` to all functions — avoid re-querying BigQuery every render

### 5.2 Bias Meter Page (`dashboard/pages/bias_meter.py`)
- [ ] Horizontal bar chart per outlet, color-coded Left→Right
- [ ] Filter by: English only / Hindi only / All
- [ ] Tooltip shows: avg score, article count, top emotional entity

### 5.3 Leaderboard Page (`dashboard/pages/leaderboard.py`)
- [ ] Table ranked by composite bias + emotion + clickbait score
- [ ] Columns: outlet, bias score, emotion score, clickbait score, articles analyzed
- [ ] Sortable by each column
- [ ] Export to CSV button

### 5.4 Story Compare Page (`dashboard/pages/story_compare.py`)
- [ ] Dropdown: pick a story pair from today's top 20
- [ ] Side-by-side view: outlet A headline + excerpt vs outlet B headline + excerpt
- [ ] Show framing divergence score
- [ ] Show SHAP-highlighted words that drove the emotion score

### 5.5 Trend Page (`dashboard/pages/trends.py`)
- [ ] Line chart: bias score over time per outlet
- [ ] Multi-select outlets to compare
- [ ] Date range picker
- [ ] Overlay toggle: show major Indian political events on timeline (e.g. election dates)

### 5.6 Main App (`dashboard/app.py`)
- [ ] Nav sidebar with four pages
- [ ] Header with project description and GitHub link
- [ ] Footer: methodology disclaimer, dataset link

### 5.7 Deploy Dashboard
- [ ] Option A (simpler): deploy to Streamlit Community Cloud (free, connect GitHub)
- [ ] Option B (GCP): containerize, deploy as Cloud Run service with `--min-instances=1`
- [ ] Set BigQuery service account credentials as Secret Manager secret
- [ ] Test public URL, verify BigQuery reads work

---

## Phase 6 — CI/CD & Automation (Days 23–25)

### 6.1 GitHub Actions (`/.github/workflows/test.yml`)
- [ ] Trigger on every push and PR
- [ ] Steps: checkout → install deps → run `ruff` linter → run `pytest`
- [ ] Badge on README showing test status

### 6.2 Cloud Build (`/cloudbuild.yaml`)
- [ ] Trigger on merge to `main`
- [ ] Build all three Docker images (scraper, analyzer, aggregator)
- [ ] Push to Artifact Registry
- [ ] Deploy updated images to Cloud Run Jobs

### 6.3 Dashboard Auto-deploy
- [ ] If using Streamlit Cloud: auto-deploys on push to main (built-in)
- [ ] If using Cloud Run: add dashboard build + deploy step to `cloudbuild.yaml`

### 6.4 Alerting
- [ ] Set up Cloud Monitoring alert if any Cloud Run Job fails
- [ ] Email notification to personal Gmail (free)
- [ ] Add simple health check endpoint to dashboard: `/health` returns last scrape timestamp

---

## Phase 7 — Polish & Launch (Days 26–28)

- [ ] Write `README.md` — project overview, architecture diagram, how to run locally
- [ ] Write methodology page on dashboard explaining how scores are computed
- [ ] Add disclaimer: scores are descriptive, not verdicts
- [ ] Post dataset to HuggingFace and Kaggle with proper documentation
- [ ] Write Medium blog post: "I built an Indian news bias auditor because the tools didn't exist"
- [ ] Share on Twitter/LinkedIn with dashboard link
- [ ] Add project to resume and portfolio

---

## Timeline Summary

| Phase | Days | Deliverable |
|---|---|---|
| 0 — GCP setup | 1 | Cloud project ready, BigQuery schema created |
| 1 — Scraper | 2–4 | Daily RSS scraping running on Cloud Scheduler |
| 2 — Analyzers | 5–10 | Four NLP modules scoring articles daily |
| 3 — Weak supervision | 11–14 | Labeled dataset published on HuggingFace |
| 4 — Aggregator | 15–17 | Outlet profiles and story pairs in BigQuery |
| 5 — Dashboard | 18–22 | Public Streamlit dashboard live |
| 6 — CI/CD | 23–25 | Fully automated deploy pipeline |
| 7 — Launch | 26–28 | Blog post, resume updated, shared publicly |

**Total: ~4 weeks of focused part-time work.**

---

## Daily Automated Schedule (Production)

```
02:00 IST — Cloud Scheduler triggers scraper job
02:30 IST — Scraper finishes, ~500 articles in BigQuery
03:00 IST — Cloud Scheduler triggers analyzer job
04:30 IST — Analyzer finishes, scores written to BigQuery
05:00 IST — Cloud Scheduler triggers aggregator job
05:15 IST — Outlet profiles and story pairs updated
05:15+ IST — Dashboard reflects fresh data for the day
```

---

## Cost Estimate (Monthly, Production)

| Service | Usage | Cost |
|---|---|---|
| Cloud Scheduler | 3 jobs | Free |
| Cloud Run Jobs | ~90 min/day compute | Free tier |
| BigQuery storage | ~5GB | Free (under 10GB) |
| BigQuery queries | ~50GB/month | Free (under 1TB) |
| Artifact Registry | ~2GB images | ~$0.20 |
| Streamlit Cloud | Dashboard hosting | Free |
| **Total** | | **~$0.20/month** |
