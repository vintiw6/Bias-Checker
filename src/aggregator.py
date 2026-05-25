import os
import json
import pandas as pd
import numpy as np
import db
from sentence_transformers import SentenceTransformer, util

_embedding_model = None

def get_embedding_model():
    """Lazy loader for sentence-transformers model."""
    global _embedding_model
    if _embedding_model is None:
        print("Loading sentence-transformers model...")
        _embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _embedding_model

def compute_outlet_profiles() -> pd.DataFrame:
    """Computes aggregate profiles for all outlets based on scored articles."""
    df = db.get_all_scored()
    if df.empty:
        print("No scored articles found in the database. Cannot compute profiles.")
        return pd.DataFrame()
        
    profiles = []
    
    # Load outlet config for ground truth lean
    outlets_file = os.path.join("data", "outlets.json")
    with open(outlets_file, "r") as f:
        outlets_config = json.load(f)
        
    grouped = df.groupby("outlet")
    
    for outlet, group in grouped:
        avg_emotion = float(group["emotion"].mean())
        avg_clickbait = float(group["clickbait"].mean())
        article_count = int(group.shape[0])
        
        # Get perceived lean
        lean = outlets_config.get(outlet, {}).get("lean", "center")
        
        # Compute lean offset for continuous bias score
        # left = -0.3, center-left = -0.15, center = 0.0, right = 0.3
        lean_offsets = {
            "left": -0.3,
            "center-left": -0.15,
            "center": 0.0,
            "right": 0.3
        }
        offset = lean_offsets.get(lean, 0.0)
        
        # Continuous bias score heuristic: (avg_emotion * 0.4) + (avg_clickbait * 0.002) + offset
        # Clickbait is 0-100, emotion is 0-1. Let's scale clickbait down to 0-1 range.
        # bias_score should ideally fall in -1.0 to +1.0
        norm_clickbait = avg_clickbait / 100.0
        bias_score = (avg_emotion * 0.3) + (norm_clickbait * 0.2) + offset
        # Clip to [-1.0, 1.0] just in case
        bias_score = max(-1.0, min(1.0, bias_score))
        
        # Aggregate top entities for this outlet
        all_entities = {}
        for _, row in group.iterrows():
            ent_str = row["entity_json"]
            if ent_str:
                try:
                    ents = json.loads(ent_str)
                    for ent, sent in ents.items():
                        if ent not in all_entities:
                            all_entities[ent] = []
                        all_entities[ent].append(sent)
                except Exception:
                    continue
                    
        # Find the most mentioned entity and its average sentiment
        top_entity = "N/A"
        top_entity_sentiment = 0.0
        top_entity_mentions = 0
        
        if all_entities:
            # Sort by number of mentions
            sorted_ents = sorted(all_entities.items(), key=lambda x: len(x[1]), reverse=True)
            top_ent_name, sentiments = sorted_ents[0]
            top_entity = top_ent_name
            top_entity_sentiment = float(sum(sentiments) / len(sentiments))
            top_entity_mentions = len(sentiments)
            
        profiles.append({
            "outlet": outlet,
            "lean": lean,
            "avg_emotion": avg_emotion,
            "avg_clickbait": avg_clickbait,
            "article_count": article_count,
            "bias_score": bias_score,
            "top_entity": top_entity,
            "top_entity_sentiment": top_entity_sentiment,
            "top_entity_mentions": top_entity_mentions
        })
        
    return pd.DataFrame(profiles)

def get_story_pairs(articles_df: pd.DataFrame = None) -> pd.DataFrame:
    """Finds cross-outlet article pairs covering the same story and calculates framing divergence."""
    if articles_df is None:
        articles_df = db.get_all_scored()
        
    if articles_df.empty or articles_df.shape[0] < 2:
        print("Not enough scored articles to pair stories.")
        return pd.DataFrame()
        
    # Get embedding model
    model = get_embedding_model()
    
    # Reset index to ensure alignments match
    articles_df = articles_df.reset_index(drop=True)
    headlines = articles_df["headline"].tolist()
    
    # Compute embeddings
    print("Computing semantic embeddings for headlines...")
    embeddings = model.encode(headlines, convert_to_tensor=True)
    
    # Compute cosine similarities
    cosine_scores = util.cos_sim(embeddings, embeddings).cpu().numpy()
    
    pairs = []
    num_articles = len(headlines)
    
    # Avoid duplicate pairs and self-pairing
    for i in range(num_articles):
        for j in range(i + 1, num_articles):
            score = cosine_scores[i][j]
            # Match if similarity is high and outlets are different (0.52 is optimized for prototype overlays)
            if score > 0.52 and articles_df.loc[i, "outlet"] != articles_df.loc[j, "outlet"]:
                art_a = articles_df.loc[i]
                art_b = articles_df.loc[j]
                
                # Framing divergence: absolute difference in emotional intensity
                div = abs(art_a["emotion"] - art_b["emotion"])
                
                pairs.append({
                    "headline_a": art_a["headline"],
                    "outlet_a": art_a["outlet"],
                    "emotion_a": art_a["emotion"],
                    "clickbait_a": art_a["clickbait"],
                    "url_a": art_a["url"],
                    "headline_b": art_b["headline"],
                    "outlet_b": art_b["outlet"],
                    "emotion_b": art_b["emotion"],
                    "clickbait_b": art_b["clickbait"],
                    "url_b": art_b["url"],
                    "similarity": float(score),
                    "divergence": float(div)
                })
                
    if not pairs:
        return pd.DataFrame()
        
    pairs_df = pd.DataFrame(pairs)
    # Deduplicate matching stories (e.g. if the exact same headline comparison is repeated)
    pairs_df = pairs_df.sort_values(by="divergence", ascending=False)
    
    # Simple deduplication: don't include the same headline twice in the top list
    seen_headlines = set()
    unique_pairs = []
    for _, row in pairs_df.iterrows():
        h_a = row["headline_a"]
        h_b = row["headline_b"]
        if h_a not in seen_headlines and h_b not in seen_headlines:
            unique_pairs.append(row)
            seen_headlines.add(h_a)
            seen_headlines.add(h_b)
            
    # Return top 10 pairs with highest divergence
    return pd.DataFrame(unique_pairs).head(10)

if __name__ == "__main__":
    print("Testing aggregator calculation...")
    profiles = compute_outlet_profiles()
    if not profiles.empty:
        print("\n=== Outlet Profiles ===")
        print(profiles.to_string(index=False))
        
        print("\n=== Story Pairs ===")
        pairs = get_story_pairs()
        if not pairs.empty:
            print(pairs[["outlet_a", "headline_a", "outlet_b", "headline_b", "divergence"]].head(5).to_string(index=False))
        else:
            print("No matching story pairs found.")
    else:
        print("No scored articles found to test aggregator.")
