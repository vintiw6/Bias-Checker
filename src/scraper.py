import os
import sys
import json
import hashlib
from datetime import datetime

# Prevent Windows console encoding errors for Unicode symbols (e.g. Rupee symbol)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import feedparser
import trafilatura
import httpx
from bs4 import BeautifulSoup
import db

def clean_target_url(url: str) -> str:
    """Standardizes target URLs and replaces domain overrides (e.g. The Wire to m.thewire.in)."""
    if "thewire.in" in url:
        url = url.replace("https://thewire.in/", "https://m.thewire.in/").replace("http://thewire.in/", "http://m.thewire.in/")
    return url

def resolve_url(url: str) -> str:
    """Decodes Google News redirect URLs and handles domain overrides."""
    if "news.google.com/rss/articles" in url:
        try:
            from googlenewsdecoder import gnewsdecoder
            res = gnewsdecoder(url)
            if res.get("status") and res.get("decoded_url"):
                url = res["decoded_url"]
        except Exception as e:
            print(f"Error decoding Google News URL: {e}")
            
    return clean_target_url(url)

def generate_id(url: str) -> str:
    """Generates a unique MD5 hash for the given URL."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def clean_html_fallback(html_content: str) -> str:
    """Fallback text extractor using BeautifulSoup if trafilatura fails."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        # Get text
        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text
    except Exception:
        return ""

def fetch_article_body(url: str) -> str:
    """Fetches the full article body text using trafilatura, falling back to BeautifulSoup."""
    url = clean_target_url(url)
    try:
        # Download HTML using httpx with a timeout
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        if response.status_code != 200:
            return ""
        
        # Try trafilatura extraction first
        body = trafilatura.extract(response.text)
        if body:
            return body
        
        # Fall back to BeautifulSoup if trafilatura returns None
        return clean_html_fallback(response.text)
    except Exception as e:
        print(f"Error fetching/extracting {url}: {e}")
        return ""

def scrape_single_article(url: str) -> dict:
    """Downloads the HTML of a single URL and extracts both the headline and body text."""
    url = resolve_url(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        if response.status_code != 200:
            return {"error": f"Failed to fetch page. HTTP Status Code: {response.status_code}"}
            
        # Parse HTML to find title / headline
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Search for headline in open graph title, twitter title, h1, or title tag
        og_title = soup.find("meta", property="og:title")
        tw_title = soup.find("meta", attrs={"name": "twitter:title"})
        title_tag = soup.find("title")
        h1_tag = soup.find("h1")
        
        headline = ""
        if og_title and og_title.get("content"):
            headline = og_title.get("content").strip()
        elif tw_title and tw_title.get("content"):
            headline = tw_title.get("content").strip()
        elif h1_tag:
            headline = h1_tag.get_text().strip()
        elif title_tag:
            headline = title_tag.get_text().strip()
            
        # Clean headline (often sites append site names like "Headline - The Hindu")
        if headline:
            for separator in [" - ", " | ", " : "]:
                if separator in headline:
                    # Pick the longest part or first part
                    parts = headline.split(separator)
                    headline = parts[0].strip()
                    break
                    
        # Extract body text using trafilatura
        body = trafilatura.extract(response.text)
        if not body:
            body = clean_html_fallback(response.text)
            
        if not headline:
            headline = "Untitled Article"
            
        return {
            "headline": headline,
            "body": body if body else "No content extracted.",
            "url": url
        }
    except Exception as e:
        return {"error": f"Failed to extract article contents: {e}"}

def scrape_feeds():
    """Scrapes all feeds specified in data/outlets.json, stores new articles in the DB & scraped_articles.csv."""
    # Ensure database/directory is initialized
    os.makedirs("data", exist_ok=True)
    db.init_db()
    
    # Load outlet configuration
    outlets_file = os.path.join("data", "outlets.json")
    if not os.path.exists(outlets_file):
        print(f"Error: {outlets_file} not found.")
        return
        
    with open(outlets_file, "r") as f:
        outlets = json.load(f)
        
    print("Starting scraping process...")
    all_scraped_articles = []
    total_scraped_new = 0
    
    for outlet_name, info in outlets.items():
        rss_url = info["rss"]
        lean = info["lean"]
        print(f"Scraping feed for {outlet_name}: {rss_url}")
        
        try:
            # Fetch RSS feed using httpx with User-Agent to bypass Cloudflare block
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            try:
                response = httpx.get(rss_url, headers=headers, timeout=10.0, follow_redirects=True)
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                else:
                    feed = feedparser.parse(rss_url)
            except Exception:
                feed = feedparser.parse(rss_url)

            if not feed.entries:
                print(f"Warning: No entries found for {outlet_name} (feed might be down or invalid).")
                continue
                
            scraped_count = 0

            # Limit to first 50 entries to increase audit coverage per outlet
            for entry in feed.entries[:50]:
                url = entry.get("link")
                if not url:
                    continue
                
                # Resolve Google News redirect URLs and overrides
                url = resolve_url(url)
                
                # Check for duplicate in database before downloading full article body
                if db.article_exists(url):
                    continue
                
                headline = entry.get("title", "")
                if not headline:
                    continue
                
                # Parse published time
                published_at = entry.get("published") or entry.get("updated")
                if not published_at:
                    published_at = datetime.utcnow().isoformat()
                
                # Fetch full article body
                print(f"Fetching body for: {headline[:50]}...")
                body = fetch_article_body(url)
                
                article_data = {
                    "id": generate_id(url),
                    "outlet": outlet_name,
                    "headline": headline,
                    "url": url,
                    "body": body if body else "No content extracted.",
                    "published_at": published_at,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "lean": lean
                }
                
                db.insert_article(article_data)
                all_scraped_articles.append(article_data)
                scraped_count += 1
                total_scraped_new += 1
                
            print(f"Successfully scraped {scraped_count} new articles from {outlet_name}")
            
        except Exception as e:
            print(f"Error processing outlet {outlet_name}: {e}")
            continue

    # Write newly scraped articles to data/scraped_articles.csv
    scraped_csv = os.path.join("data", "scraped_articles.csv")
    
    # Read existing URLs to prevent duplicates in CSV
    existing_urls = set()
    if os.path.exists(scraped_csv):
        try:
            import csv
            with open(scraped_csv, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("url"):
                        existing_urls.add(row["url"])
        except Exception as e:
            print(f"Warning: Could not read existing scraped_articles.csv: {e}")

    new_articles_for_csv = [art for art in all_scraped_articles if art["url"] not in existing_urls]
    
    if new_articles_for_csv:
        file_exists = os.path.exists(scraped_csv)
        try:
            import csv
            with open(scraped_csv, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "outlet", "headline", "url", "body", "published_at", "scraped_at", "lean"])
                if not file_exists:
                    writer.writeheader()
                for art in new_articles_for_csv:
                    writer.writerow(art)
            print(f"Successfully saved {len(new_articles_for_csv)} new articles to {scraped_csv}")
        except Exception as e:
            print(f"Error writing to scraped_articles.csv: {e}")

    # Fallback Mechanism: If no new articles are scraped and the file is missing/empty, generate fallback data
    csv_missing_or_empty = not os.path.exists(scraped_csv) or os.path.getsize(scraped_csv) < 50
    if total_scraped_new == 0 and csv_missing_or_empty:
        print("No new articles scraped and scraped_articles.csv is missing or empty.")
        print("Live scraping failed or offline. Generating high-quality fallback scraped articles...")
        try:
            try:
                import demo_data
            except ImportError:
                import src.demo_data as demo_data
            demo_data.generate_demo_scraped()
        except Exception as e:
            print(f"Error generating fallback scraped data: {e}")

if __name__ == "__main__":
    scrape_feeds()
