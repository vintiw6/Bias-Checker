import os
import sys
import json
import spacy
from transformers import pipeline

_sentiment_pipeline = None
_spacy_nlp = None
_target_entities = None

def load_target_entities():
    """Loads target entities from data/indian_entities.json."""
    global _target_entities
    if _target_entities is None:
        path = os.path.join("data", "indian_entities.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                _target_entities = json.load(f)
        else:
            # Fallback default entities if file is not found
            _target_entities = [
                "Modi", "BJP", "Congress", "Rahul Gandhi", "Amit Shah", 
                "AAP", "Kejriwal", "Yogi", "RSS", "TMC", "Mamata", "Opposition"
            ]
    return _target_entities

def get_spacy_nlp():
    """Lazy loader for spaCy model."""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            _spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model en_core_web_sm...")
            os.system(f'"{sys.executable}" -m spacy download en_core_web_sm')
            _spacy_nlp = spacy.load("en_core_web_sm")
    return _spacy_nlp


def get_sentiment_pipeline():
    """Lazy loader for HuggingFace sentiment pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        print("Loading sentiment analysis model...")
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1 # CPU for compatibility
        )
    return _sentiment_pipeline

def extract_entities(text: str) -> dict:
    """Finds target entities in the text and scores sentiment of their surrounding sentences.
    
    Returns a dict of {entity_name: sentiment_score} where score is between -1.0 and +1.0.
    """
    if not text or not isinstance(text, str):
        return {}
        
    nlp = get_spacy_nlp()
    sentiment_analyzer = get_sentiment_pipeline()
    targets = load_target_entities()
    
    doc = nlp(text)
    
    # Track sentences containing target entities
    entity_sentences = {}
    
    for sent in doc.sents:
        sent_text = sent.text
        # Look for target entities in the sentence text
        # We perform simple substring matching for robustness, or check spaCy ents
        for entity in targets:
            # Case insensitive match with word boundaries or space to avoid partial word matching
            # e.g., "Modi" matches, but we don't want "modify" to match "Modi".
            # Simple check: is entity in sentence?
            if entity.lower() in sent_text.lower():
                if entity not in entity_sentences:
                    entity_sentences[entity] = []
                entity_sentences[entity].append(sent_text)
                
    # Score sentiment for the sentences of each entity
    entity_sentiments = {}
    for entity, sentences in entity_sentences.items():
        # Avoid duplicate sentences to prevent skew
        unique_sents = list(set(sentences))
        scores = []
        try:
            results = sentiment_analyzer(unique_sents)
            for res in results:
                label = res["label"]
                score = res["score"]
                # Map POSITIVE to score, NEGATIVE to -score
                val = score if label == "POSITIVE" else -score
                scores.append(val)
            # Average the scores
            if scores:
                entity_sentiments[entity] = sum(scores) / len(scores)
        except Exception as e:
            print(f"Error analyzing sentiment for {entity}: {e}")
            
    return entity_sentiments

def top_entities(articles: list[dict]) -> dict:
    """Aggregates entity sentiment across a list of articles.
    
    Returns a dict containing entity mentions and their average sentiment.
    """
    entity_data = {}
    for article in articles:
        ents_json = article.get("entity_json")
        if not ents_json:
            continue
        try:
            ents = json.loads(ents_json) if isinstance(ents_json, str) else ents_json
            for entity, score in ents.items():
                if entity not in entity_data:
                    entity_data[entity] = []
                entity_data[entity].append(score)
        except Exception:
            continue
            
    aggregated = {}
    for entity, scores in entity_data.items():
        aggregated[entity] = {
            "mentions": len(scores),
            "avg_sentiment": sum(scores) / len(scores)
        }
    return aggregated

if __name__ == "__main__":
    test_text = (
        "The recent announcements by PM Modi were praised by the business community, "
        "who felt that the BJP is steering the economy in the right direction. However, the "
        "Opposition led by Congress strongly criticized the policy, calling it disastrous for common citizens."
    )
    print("Testing entity sentiment extractor...")
    results = extract_entities(test_text)
    print("Results:", results)
