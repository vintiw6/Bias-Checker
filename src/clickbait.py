import sys
from transformers import pipeline
from tqdm import tqdm

MODEL_NAME = "valurank/distilroberta-clickbait"
_clickbait_pipeline = None

def get_pipeline():
    """Lazy loader for the clickbait pipeline."""
    global _clickbait_pipeline
    if _clickbait_pipeline is None:
        print(f"Loading clickbait model: {MODEL_NAME}...")
        _clickbait_pipeline = pipeline(
            "text-classification",
            model=MODEL_NAME,
            device=-1 # CPU for compatibility
        )
    return _clickbait_pipeline

def score_clickbait(texts: list[str]) -> list[float]:
    """Scores the clickbait probability of a list of headlines.
    
    Returns a list of floats (0 to 100) representing clickbait probability.
    """
    if not texts:
        return []
        
    nlp = get_pipeline()
    scores = []
    
    # Process in batches of 32
    batch_size = 32
    for i in tqdm(range(0, len(texts), batch_size), desc="Scoring clickbait"):
        batch = texts[i:i+batch_size]
        try:
            results = nlp(batch)
            for res in results:
                # res is a dict like {'label': 'clickbait', 'score': 0.95} or {'label': 'not clickbait', 'score': 0.05}
                label = res["label"].lower()
                prob = res["score"]
                
                # Check label names or fallback to standard binary classification indices
                if "not" in label or "non" in label or label == "label_0":
                    clickbait_score = (1.0 - prob) * 100
                else:
                    clickbait_score = prob * 100
                    
                scores.append(float(clickbait_score))
        except Exception as e:
            print(f"Error scoring clickbait batch: {e}")
            scores.extend([0.0] * len(batch))
            
    return scores

if __name__ == "__main__":
    # Test standalone
    test_headlines = [
        "You won't believe what this top Bollywood actor said about his co-star!",
        "RBI raises repo rate by 25 basis points to curb rising inflation",
        "10 shocking secrets the government doesn't want you to know about taxes",
        "Supreme Court issues notice to Central Government on new environment guidelines",
        "Is this the end of smartphones? What happens next will shock you!"
    ]
    print("Testing clickbait detector...")
    results = score_clickbait(test_headlines)
    for text, score in zip(test_headlines, results):
        print(f"Score: {score:.2f} | Text: {text}")
