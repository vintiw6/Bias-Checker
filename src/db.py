import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join("data", "articles.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the articles table if it does not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            outlet TEXT NOT NULL,
            headline TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            body TEXT,
            published_at TEXT,
            scraped_at TEXT,
            lean TEXT,
            emotion REAL,
            clickbait REAL,
            entity_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_article(row: dict):
    """Inserts a new article into the articles table if the URL is unique."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articles (id, outlet, headline, url, body, published_at, scraped_at, lean)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["id"],
            row["outlet"],
            row["headline"],
            row["url"],
            row["body"],
            row["published_at"],
            row["scraped_at"],
            row["lean"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        # Ignore duplicates
        pass
    finally:
        conn.close()

def get_unscored_articles() -> list[dict]:
    """Retrieves all articles that have not yet been analyzed/scored."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, outlet, headline, url, body, published_at, scraped_at, lean
        FROM articles
        WHERE emotion IS NULL OR clickbait IS NULL OR entity_json IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_scores(article_id: str, emotion: float, clickbait: float, entity_json: str):
    """Updates the scoring fields for a specific article."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE articles
        SET emotion = ?, clickbait = ?, entity_json = ?
        WHERE id = ?
    """, (emotion, clickbait, entity_json, article_id))
    conn.commit()
    conn.close()

def get_all_scored() -> pd.DataFrame:
    """Retrieves all scored articles as a pandas DataFrame."""
    csv_path = os.path.join("data", "scored_articles.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Ensure entity_json handles NaNs and missing values gracefully
            if "entity_json" in df.columns:
                df["entity_json"] = df["entity_json"].fillna("{}")
            return df
        except Exception as e:
            print(f"Warning: Failed to read scored_articles.csv: {e}. Falling back to SQLite database.")
            
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT id, outlet, headline, url, body, published_at, scraped_at, lean, emotion, clickbait, entity_json
        FROM articles
        WHERE emotion IS NOT NULL AND clickbait IS NOT NULL AND entity_json IS NOT NULL
    """, conn)
    conn.close()
    return df

def article_exists(url: str) -> bool:
    """Checks if an article with the given URL already exists in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

