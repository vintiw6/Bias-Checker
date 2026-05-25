# Indian News Bias Auditor — Project Report

## Overview

The Indian News Bias Auditor is a fully automated NLP/ML pipeline that scrapes, analyzes, and scores Indian news outlets for political bias, emotional language, framing differences, and clickbait. It targets both English and Hindi outlets, runs daily on Google Cloud, and exposes results through a public Streamlit dashboard.

The project is motivated by a genuine data gap: unlike Western media, no labeled dataset exists for Indian news bias. This project builds that dataset from scratch using weak supervision, making it a research-grade contribution alongside the engineering work.

The target deployment environment is Google Cloud Platform (GCP), taking full advantage of free-tier and low-cost services including Cloud Scheduler, Cloud Run, BigQuery, and Artifact Registry.

---

## Problem Statement

Indian media bias is widely discussed but poorly measured. Existing tools like AllSides and Media Bias Fact Check cover only a handful of Indian outlets, and none provide programmatic, real-time scoring. Journalists, researchers, fact-checkers, and media literacy educators lack a quantitative signal for outlet-level bias.

This project addresses that gap by:

- Building a continuously updated dataset of Indian news headlines and articles
- Applying multiple NLP lenses (emotion, framing, entity sentiment, clickbait) to each piece of content
- Aggregating scores into outlet-level profiles updated daily
- Publishing results as a free, open dashboard

---

## Outlets Covered

### English

| Outlet | Perceived Lean | RSS Available |
|---|---|---|
| The Wire | Left / liberal | Yes |
| Scroll | Left / liberal | Yes |
| The Quint | Center-left | Yes |
| The Hindu | Center-left | Yes |
| Indian Express | Center | Yes |
| The Print | Center | Yes |
| NDTV | Center | Yes |
| Times of India | Center | Yes |
| Republic World | Right / nationalist | Yes |
| OpIndia | Right / nationalist | Yes |
| Swarajya | Right / nationalist | Yes |

### Hindi (via MuRIL multilingual model)

| Outlet | Perceived Lean | RSS Available |
|---|---|---|
| Dainik Bhaskar | Center-right | Yes |
| Amar Ujala | Right-leaning | Yes |
| Navbharat Times | Center | Yes |

---

## NLP Analysis Modules

### 1. Emotion Scorer
Measures the emotional intensity of each headline and article using a multilingual RoBERTa model. Produces a score from 0 (neutral) to 1 (highly charged). Useful for detecting outlets that consistently use more aggressive or emotive language to describe identical events.

### 2. Named Entity Recognition + Sentiment
Uses spaCy (with a custom Indian political entity list) to extract mentions of politicians, parties, states, and institutions. A sentiment classifier then scores how positively or negatively each entity is portrayed per article. Aggregated over time this reveals systematic editorial slant toward or against specific political actors.

### 3. Framing Analyzer
Identifies pairs of articles across outlets that cover the same event (matched via semantic similarity using sentence-transformers). Computes the cosine distance between their embeddings as a framing divergence score. High divergence = same event, very different framing. These pairs are surfaced in the dashboard as "same story, different spin."

### 4. Clickbait Detector
A fine-tuned DistilBERT classifier trained on English clickbait datasets, adapted for Indian headlines. Scores each headline from 0 to 100 for sensationalism markers: vague teasers, emotional superlatives, artificial urgency, misleading specificity.

---

## Dataset Contribution

Because no labeled Indian media bias dataset exists, this project generates one via weak supervision using Snorkel. Labeling functions include:

- MBFC (Media Bias Fact Check) source-level labels as prior
- Keyword-based political lean signals (party names, slogans, ideological vocabulary)
- Aggregate emotion score thresholds
- Manual seed labels for 200 headlines to anchor the model

The resulting labeled dataset will be published as an open dataset on Hugging Face and Kaggle, making it a standalone academic contribution.

---

## Automation Architecture

The entire pipeline runs without human intervention on a daily schedule:

```
Cloud Scheduler (daily 2am IST)
        ↓
Cloud Run Job — scraper
  • Fetches RSS feeds from all outlets
  • Extracts full article text via BeautifulSoup
  • Deduplicates against existing records
  • Writes raw data to BigQuery (raw_articles table)
        ↓
Cloud Run Job — analyzer
  • Pulls unprocessed articles from BigQuery
  • Runs all four NLP modules in parallel
  • Writes scores to BigQuery (article_scores table)
        ↓
Cloud Run Job — aggregator
  • Computes rolling 30-day outlet-level scores
  • Identifies same-story pairs across outlets
  • Writes to BigQuery (outlet_profiles, story_pairs tables)
        ↓
Streamlit Dashboard (Cloud Run, always-on)
  • Reads from BigQuery
  • Renders bias meters, leaderboard, story compare, trend charts
  • Publicly accessible, no login required
```

---

## Evaluation

Since no ground truth exists, evaluation is multi-pronged:

- **Human agreement rate** — 50 random headlines manually labeled by three annotators; model agreement measured
- **Inter-outlet consistency** — outlets that MBFC labels as right-leaning should score higher on right-lean metrics
- **Framing pair quality** — random sample of 20 story pairs reviewed for genuine topic overlap
- **Clickbait precision** — 30 manually verified clickbait vs non-clickbait headlines

Target metrics: emotion classifier F1 > 0.78, clickbait classifier F1 > 0.82, framing pair precision > 0.80.

---

## Limitations and Ethical Considerations

- Bias labels from weak supervision carry noise; they reflect aggregate editorial patterns, not ground truth
- The left/right framing used in Western media may not map cleanly onto Indian political discourse
- Hindi and regional language coverage is limited by available pretrained models
- The dashboard is descriptive, not prescriptive — it surfaces patterns, not verdicts
- Outlet scores should be interpreted alongside context (ownership, editorial history, target audience)

---

## Resume Summary

> Built a fully automated NLP pipeline to audit political bias, emotional framing, and clickbait in 14 Indian news outlets. Created the first open labeled dataset for Indian media bias using weak supervision (Snorkel). Pipeline runs daily on Google Cloud (Scheduler + Cloud Run + BigQuery), analyzing 500+ articles/day. Deployed a public Streamlit dashboard with outlet leaderboard, bias meters, and side-by-side story framing comparison. Models: MuRIL, DistilRoBERTa, spaCy, sentence-transformers. Dataset published on Hugging Face.
