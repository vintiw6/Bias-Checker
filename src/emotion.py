import sys
from transformers import pipeline
from tqdm import tqdm

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
_emotion_pipeline = None

def get_pipeline():
    """Lazy loader for the emotion pipeline."""
    global _emotion_pipeline
    if _emotion_pipeline is None:
        print(f"Loading emotion model: {MODEL_NAME}...")
        # Load pipeline on GPU if available, else CPU
        _emotion_pipeline = pipeline(
            "text-classification",
            model=MODEL_NAME,
            return_all_scores=True,
            device=-1 # Set to 0 if CUDA is available, but for compatibility we use CPU (-1)
        )
    return _emotion_pipeline

def score_emotion(texts: list[str]) -> list[float]:
    """Scores the emotional intensity of a list of headlines/texts.
    
    Returns a list of floats (0 to 1) representing the emotional charge 
    (computed as 1.0 - neutral_probability).
    """
    if not texts:
        return []
        
    nlp = get_pipeline()
    scores = []
    
    # Process in batches of 16
    batch_size = 16
    for i in tqdm(range(0, len(texts), batch_size), desc="Scoring emotion"):
        batch = texts[i:i+batch_size]
        try:
            results = nlp(batch)
            for res in results:
                # Handle both all_scores list format and top_score dict format
                if isinstance(res, dict):
                    # Single dict top label format
                    label = res["label"].lower()
                    score = res["score"]
                    if label == "neutral":
                        emotion_score = 1.0 - score
                    else:
                        emotion_score = score
                elif isinstance(res, list):
                    # List of dicts format (return_all_scores=True)
                    neutral_prob = 0.0
                    max_other_prob = 0.0
                    for label_score in res:
                        label = label_score["label"].lower()
                        score = label_score["score"]
                        if label == "neutral":
                            neutral_prob = score
                        else:
                            if score > max_other_prob:
                                max_other_prob = score
                    emotion_score = 1.0 - neutral_prob if neutral_prob > 0.0 else max_other_prob
                else:
                    emotion_score = 0.0
                    
                scores.append(float(emotion_score))
        except Exception as e:
            print(f"Error scoring batch: {e}")
            # Fallback to 0.0 for the batch elements
            scores.extend([0.0] * len(batch))
            
    return scores

if __name__ == "__main__":
    # Test standalone
    test_headlines = [
        "Parliament session begins to discuss new budget proposal",
        "Modi launches brutal crackdown on corrupt officials in dramatic raid",
        "India wins cricket match against Australia in thrilling finish",
        "The government announced a routine policy change on agriculture",
        "Tragic and horrifying accident leaves dozens injured in severe highway collision"
    ]
    print("Testing emotion scorer...")
    results = score_emotion(test_headlines)
    for text, score in zip(test_headlines, results):
        print(f"Score: {score:.4f} | Text: {text}")
