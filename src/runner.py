import json
import sys
import db
import emotion
import clickbait
import entity

# Prevent Windows console encoding errors for Unicode symbols (e.g. Rupee symbol)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_pipeline():
    """Pulls unscored articles from CSV, runs the scoring analyzers, updates database & scored_articles.csv."""
    import os
    import csv
    
    os.makedirs("data", exist_ok=True)
    db.init_db()
    
    scraped_csv = os.path.join("data", "scraped_articles.csv")
    scored_csv = os.path.join("data", "scored_articles.csv")
    
    # 1. Load scraped articles
    if not os.path.exists(scraped_csv) or os.path.getsize(scraped_csv) < 50:
        print(f"Warning: {scraped_csv} not found or empty.")
        print("Live scraping failed or offline. Generating high-quality fallback scraped articles...")
        try:
            try:
                import demo_data
            except ImportError:
                import src.demo_data as demo_data
            demo_data.generate_demo_scraped()
        except Exception as e:
            print(f"Error generating fallback scraped data: {e}")
            return
            
    scraped_articles = []
    try:
        with open(scraped_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scraped_articles.append(row)
    except Exception as e:
        print(f"Error reading {scraped_csv}: {e}")
        return
        
    # 2. Load already scored IDs
    scored_ids = set()
    if os.path.exists(scored_csv):
        try:
            with open(scored_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("id"):
                        scored_ids.add(row["id"])
        except Exception as e:
            print(f"Warning: Could not read scored_articles.csv: {e}")
            
    # Filter unscored articles
    unscored = [art for art in scraped_articles if art["id"] not in scored_ids]
    
    if not unscored:
        print("No new unscored articles found in the CSV. Pipeline is up to date!")
        return
        
    print(f"Found {len(unscored)} unscored articles. Starting NLP analysis...")
    
    # Extract headlines
    headlines = [art["headline"] for art in unscored]
    
    # 3. Batch score emotion
    print("Scoring emotional intensity...")
    emotion_scores = emotion.score_emotion(headlines)
    
    # 4. Batch score clickbait
    print("Scoring clickbait levels...")
    clickbait_scores = clickbait.score_clickbait(headlines)
    
    # 5. Extract entities and context sentiment per article
    print("Performing Named Entity Recognition and sentiment analysis...")
    newly_scored_articles = []
    
    for idx, art in enumerate(unscored):
        article_id = art["id"]
        headline = art["headline"]
        body = art["body"] or ""
        
        # Use body text for entity extraction, fallback to headline if body is empty or too short
        text_to_analyze = body if len(body.strip()) > 50 else headline
        
        # Extract entities
        print(f"[{idx+1}/{len(unscored)}] Extracting entities for: {headline[:50]}...")
        entity_sentiments = entity.extract_entities(text_to_analyze)
        
        # Serialize entity sentiments to JSON string
        entity_json = json.dumps(entity_sentiments)
        
        # Get matching scores
        emo_score = emotion_scores[idx]
        cb_score = clickbait_scores[idx]
        
        # Update database (keep SQLite in sync)
        try:
            db.update_scores(article_id, emo_score, cb_score, entity_json)
        except Exception as e:
            print(f"Warning: Could not update SQLite DB for article {article_id}: {e}")
            
        # Create scored record
        scored_art = art.copy()
        scored_art["emotion"] = float(emo_score)
        scored_art["clickbait"] = float(cb_score)
        scored_art["entity_json"] = entity_json
        newly_scored_articles.append(scored_art)
        
    # 6. Append scores to data/scored_articles.csv
    file_exists = os.path.exists(scored_csv)
    try:
        with open(scored_csv, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id", "outlet", "headline", "url", "body", "published_at", "scraped_at", "lean", "emotion", "clickbait", "entity_json"
            ])
            if not file_exists:
                writer.writeheader()
            for art in newly_scored_articles:
                writer.writerow(art)
        print(f"Successfully scored and saved {len(newly_scored_articles)} articles to {scored_csv}!")
    except Exception as e:
        print(f"Error saving to scored_articles.csv: {e}")
        
    print("Successfully completed NLP analysis!")

if __name__ == "__main__":
    run_pipeline()
