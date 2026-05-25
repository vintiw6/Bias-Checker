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
    """Pulls unscored articles, runs the scoring analyzers, and updates the database."""
    # Initialize database
    db.init_db()
    
    # 1. Fetch all unscored articles
    unscored = db.get_unscored_articles()
    if not unscored:
        print("No new unscored articles found in the database. Pipeline is up to date!")
        return
        
    print(f"Found {len(unscored)} unscored articles. Starting NLP analysis...")
    
    # Extract headlines
    headlines = [art["headline"] for art in unscored]
    
    # 2. Batch score emotion
    print("Scoring emotional intensity...")
    emotion_scores = emotion.score_emotion(headlines)
    
    # 3. Batch score clickbait
    print("Scoring clickbait levels...")
    clickbait_scores = clickbait.score_clickbait(headlines)
    
    # 4. Extract entities and context sentiment per article
    print("Performing Named Entity Recognition and sentiment analysis...")
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
        
        # 5. Update database
        db.update_scores(article_id, emo_score, cb_score, entity_json)
        
    print("Successfully completed NLP analysis and updated the database!")

if __name__ == "__main__":
    run_pipeline()
