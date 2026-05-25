# Tech Stack — Indian News Bias Auditor

All tools are free or have a free tier sufficient for this project. GCP services stay within free-tier limits at the expected data volume (~500 articles/day).

---

## Google Cloud Platform Services

| Service | Role | Free Tier |
|---|---|---|
| Cloud Scheduler | Triggers daily pipeline at 2am IST | 3 jobs free |
| Cloud Run Jobs | Runs scraper, analyzer, aggregator as containers | 180,000 vCPU-seconds/month free |
| Cloud Run (service) | Hosts Streamlit dashboard, always-on | 2M requests/month free |
| BigQuery | Stores all raw and processed data | 10GB storage + 1TB queries/month free |
| Artifact Registry | Stores Docker images for Cloud Run | 0.5GB free |
| Cloud Build | Builds Docker images on push | 120 build-minutes/day free |
| Secret Manager | Stores any API keys securely | 6 active secrets free |

Estimated monthly GCP cost at full scale: $0–$3.

---

## Data Collection

| Tool | Version | Purpose |
|---|---|---|
| `feedparser` | 6.x | Parse RSS feeds from all outlets |
| `httpx` | 0.27 | Async HTTP requests for article fetching |
| `BeautifulSoup4` | 4.12 | Extract article body text from HTML |
| `trafilatura` | 1.x | Fallback article extractor (better than BS4 for paywalls) |
| `sqlite3` | stdlib | Local dev storage before BigQuery |
| `google-cloud-bigquery` | 3.x | Write/read data from BigQuery in production |

---

## NLP Models (all free, all on Hugging Face)

| Model | Task | Language |
|---|---|---|
| `google/muril-base-cased` | Base model for Hindi/Indian language tasks | Hindi, Bengali, Tamil, Telugu + more |
| `valurank/distilroberta-bias` | Political bias classification | English |
| `j-hartmann/emotion-english-distilroberta-base` | Emotion intensity scoring | English |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Framing similarity, story matching | Multilingual |
| `mrm8488/bert-mini-finetuned-clickbait` | Clickbait detection | English |
| `en_core_web_sm` (spaCy) | Named entity recognition | English |

All models run via `transformers` or `sentence-transformers` and can be fine-tuned on Colab free tier.

---

## NLP Libraries

| Library | Purpose |
|---|---|
| `transformers` (HuggingFace) | Load and run pretrained models |
| `sentence-transformers` | Compute semantic embeddings for framing |
| `spacy` | NER, dependency parsing |
| `snorkel` | Weak supervision — generate labels without manual annotation |
| `shap` | Explain model predictions (which words drove the score) |
| `torch` | Backend for transformer models |
| `datasets` (HuggingFace) | Load and process training datasets |

---

## Data & Storage

| Tool | Purpose |
|---|---|
| BigQuery | Production data warehouse — raw articles, scores, outlet profiles |
| SQLite | Local development database |
| Parquet (via `pyarrow`) | Efficient batch data transfer between pipeline stages |
| Pandas | Data wrangling and aggregation |

### BigQuery Schema

```
raw_articles
  id STRING, outlet STRING, url STRING, headline STRING,
  body TEXT, published_at TIMESTAMP, scraped_at TIMESTAMP,
  language STRING

article_scores
  id STRING, outlet STRING, emotion_score FLOAT,
  clickbait_score FLOAT, entity_sentiment JSON,
  framing_embedding BYTES, scored_at TIMESTAMP

outlet_profiles
  outlet STRING, date DATE, avg_emotion FLOAT,
  avg_clickbait FLOAT, bias_score FLOAT,
  entity_sentiment_summary JSON

story_pairs
  article_id_a STRING, article_id_b STRING,
  outlet_a STRING, outlet_b STRING,
  similarity_score FLOAT, framing_divergence FLOAT,
  topic STRING, date DATE
```

---

## Experiment Tracking

| Tool | Purpose |
|---|---|
| Weights & Biases (W&B) | Track fine-tuning runs, metrics, model versions — free tier |
| MLflow (optional local) | Alternative if W&B not preferred |

---

## Dashboard

| Tool | Purpose |
|---|---|
| Streamlit | Main dashboard framework |
| Plotly | Interactive charts (bias trend lines, leaderboard bars) |
| `google-cloud-bigquery` | Read outlet profiles and story pairs at render time |
| Streamlit Community Cloud | Free hosting (alternative to Cloud Run for dashboard) |

---

## CI/CD

| Tool | Purpose |
|---|---|
| GitHub Actions | Run tests, lint, build Docker images on push |
| Cloud Build | Build and push images to Artifact Registry |
| Cloud Run deploy | Auto-deploy new image on merge to main |

### Pipeline: push to main → tests pass → Cloud Build builds image → Cloud Run updated → done.

---

## Dev Environment

| Tool | Purpose |
|---|---|
| Python 3.11 | Primary language |
| Docker | Containerize each pipeline stage |
| `uv` | Fast Python package manager (replaces pip) |
| `ruff` | Linting and formatting |
| `pytest` | Unit tests for scrapers and scoring functions |
| Google Colab | Fine-tune models (free T4 GPU) |
| VS Code + Cloud Code extension | Local dev with GCP integration |

---

## Useful Free Datasets

| Dataset | Use |
|---|---|
| `mediabiasgroup/mbib` (HuggingFace) | Baseline bias labels for English articles |
| LIAR dataset | Misinformation labels (supplementary) |
| HC3 dataset | Human vs AI text (supplementary for framing) |
| MBFC India entries | Source-level weak supervision labels |
| Clickbait Challenge dataset | Fine-tune clickbait detector |

---

## Installation (local dev)

```bash
# Clone and set up
git clone https://github.com/yourusername/india-bias-auditor
cd india-bias-auditor
pip install uv
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run scraper locally
python src/scraper/run.py --dev  # writes to local SQLite

# Run analyzer locally
python src/analyzer/run.py --dev

# Launch dashboard locally
streamlit run dashboard/app.py
```

---

## Folder Structure

```
india-bias-auditor/
├── src/
│   ├── scraper/          # RSS fetching, article extraction
│   ├── analyzer/         # Four NLP modules
│   ├── aggregator/       # Outlet scoring, story pairing
│   └── common/           # BigQuery client, config, utils
├── dashboard/            # Streamlit app
├── models/               # Fine-tuning scripts and saved weights
├── data/                 # Local dev SQLite, sample CSVs
├── tests/                # Unit tests
├── docker/               # Dockerfiles per pipeline stage
├── .github/workflows/    # CI/CD
├── cloudbuild.yaml        # Cloud Build config
└── requirements.txt
```
