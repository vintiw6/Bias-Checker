import plotly.express as px
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import json
from datetime import datetime

# Add the project root and src folders to python path to import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import src.db as db
import src.aggregator as aggregator
import src.scraper as scraper
import src.emotion as emotion
import src.clickbait as clickbait
import src.entity as entity

# -----------------------------------------------------------------------------
# Premium Minimalist Aesthetics & Page Config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Indian News Bias Auditor",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern, premium custom CSS
st.markdown("""
<style>
    /* Premium Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Vercel-inspired Obsidian Dark Theme background */
    .stApp {
        background: #0B1120;
        color: #F9FAFB;
    }
    
    /* Clean Minimalist Sidebar */
    [data-testid="stSidebar"] {
        background: #090D1A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    
    /* Remove default divider line in sidebar */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.04);
    }
    
    /* Minimalist Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #F9FAFB !important;
        letter-spacing: -0.02em;
    }
    
    /* Vercel/Linear Card Panels */
    .premium-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .premium-card:hover {
        border-color: rgba(59, 130, 246, 0.25);
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    /* Sleek Low-Opacity Outline Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        border-radius: 4px;
        text-transform: uppercase;
        margin-right: 8px;
        letter-spacing: 0.05em;
    }
    
    .badge-left { 
        background-color: rgba(59, 130, 246, 0.06); 
        color: #60A5FA; 
        border: 1px solid rgba(59, 130, 246, 0.15); 
    }
    .badge-center-left { 
        background-color: rgba(16, 185, 129, 0.06); 
        color: #34D399; 
        border: 1px solid rgba(16, 185, 129, 0.15); 
    }
    .badge-center { 
        background-color: rgba(107, 114, 128, 0.06); 
        color: #D1D5DB; 
        border: 1px solid rgba(107, 114, 128, 0.15); 
    }
    .badge-right { 
        background-color: rgba(225, 29, 72, 0.06); 
        color: #FB7185; 
        border: 1px solid rgba(225, 29, 72, 0.15); 
    }
    
    /* Form inputs and buttons styling */
    .stTextInput>div>div>input {
        background-color: #0E131F !important;
        color: #F9FAFB !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 6px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }
    
    /* Radio elements in sidebar styling */
    div[data-testid="stRadio"] label {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
    }
    div[data-testid="stRadio"] label[data-selected="true"] {
        color: #F9FAFB !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loader
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_dashboard_data():
    """Fetches articles, outlet profiles, and story pairs."""
    os.makedirs("data", exist_ok=True)
    scored_csv_path = os.path.join("data", "scored_articles.csv")
    
    raw_articles = pd.DataFrame()
    if os.path.exists(scored_csv_path):
        try:
            raw_articles = pd.read_csv(scored_csv_path)
            if not raw_articles.empty:
                # Ensure all required columns exist
                required_cols = ["id", "outlet", "headline", "url", "body", "published_at", "scraped_at", "lean", "emotion", "clickbait", "entity_json"]
                for col in required_cols:
                    if col not in raw_articles.columns:
                        raw_articles[col] = None
                raw_articles["entity_json"] = raw_articles["entity_json"].fillna("{}")
        except Exception as e:
            print(f"Error loading scored_articles.csv: {e}")
            
    if raw_articles.empty:
        db.init_db()
        raw_articles = db.get_all_scored()
        
    profiles_df = aggregator.compute_outlet_profiles(raw_articles)
    
    if not raw_articles.empty:
        pairs_df = aggregator.get_story_pairs(raw_articles)
    else:
        pairs_df = pd.DataFrame()
        
    return raw_articles, profiles_df, pairs_df

# Load data
articles_df, profiles_df, pairs_df = load_dashboard_data()

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div style='padding: 10px 0px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.1em; color: #F9FAFB;'>BIAS AUDITOR</span><br><span style='font-size: 0.72rem; color: #94A3B8; letter-spacing: 0.05em;'>AI MEDIA INTELLIGENCE</span></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.8rem; line-height: 1.5; margin-top: 8px;'>Real-time AI-powered linguistics auditing of Indian news outlets.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation Radio
    page = st.radio(
        "Navigation",
        ["Bias Meter", "Live Auditor", "Leaderboard", "Story Compare", "About"],
        index=0
    )
    
    st.markdown("---")
    
    # System info in sidebar
    if not articles_df.empty:
        latest_scrape = articles_df["scraped_at"].max()
        try:
            dt = datetime.fromisoformat(latest_scrape)
            formatted_date = dt.strftime("%d %b %Y, %I:%M %p UTC")
        except Exception:
            formatted_date = latest_scrape
        st.markdown(f"<p style='color: #94A3B8; font-size:0.8rem; margin-bottom: 4px;'>Last Update:</p><code style='color:#F9FAFB; font-size:0.75rem;'>{formatted_date}</code>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94A3B8; font-size:0.8rem; margin-top: 8px; margin-bottom: 4px;'>Articles Scored:</p><code style='color:#F9FAFB; font-size:0.75rem;'>{len(articles_df)}</code>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #94A3B8; font-size:0.8rem;'>System status: Pending Ingestion</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main Dashboard Pages
# -----------------------------------------------------------------------------
if articles_df.empty or profiles_df.empty:
    st.markdown("<h1 style='font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; color: #F9FAFB;'>Bias Auditor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1rem; margin-bottom: 32px;'>A quantitative media intelligence platform analyzing language patterns, clickbait velocity, and framing index across Indian news media.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        <div class="premium-card">
            <h3 style="font-size: 1.1rem; font-weight: 600; color: #F9FAFB; margin-top: 0; margin-bottom: 12px;">Onboarding Setup Required</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6; margin-bottom: 20px;">
                No scored articles were detected in the data directory. To initialize the dashboard, you can choose to immediately generate high-fidelity pre-scored demo data, or run the NLP pipeline on active news feeds locally.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='font-size: 0.95rem; font-weight: 500; color: #F9FAFB; margin-bottom: 12px;'>Initialize Demo Dataset</p>", unsafe_allow_html=True)
        if st.button("Generate Demo Data", type="primary", use_container_width=True):
            with st.spinner("Ingesting pre-calculated NLP profiles..."):
                try:
                    try:
                        import demo_data
                    except ImportError:
                        import src.demo_data as demo_data
                    demo_data.generate_demo_scored()
                    demo_data.generate_demo_scraped()
                    st.success("Demo data successfully generated. Ingestion finished.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
                    
    with col2:
        st.markdown("""
        <div class="premium-card">
            <h3 style="font-size: 1.1rem; font-weight: 600; color: #F9FAFB; margin-top: 0; margin-bottom: 12px;">Local Pipeline Instructions</h3>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 8px;"><b>1. Set Up Environment</b></p>
            <pre style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.75rem; color: #E2E8F0; margin-bottom: 16px; white-space: pre-wrap; word-wrap: break-word;">python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt</pre>
            
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 8px;"><b>2. Run RSS Scraper</b></p>
            <pre style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.75rem; color: #E2E8F0; margin-bottom: 16px; white-space: pre-wrap; word-wrap: break-word;">python src/scraper.py</pre>
            
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 8px;"><b>3. Execute NLP Analyzer</b></p>
            <pre style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.75rem; color: #E2E8F0; margin-bottom: 0px; white-space: pre-wrap; word-wrap: break-word;">python src/runner.py</pre>
        </div>
        """, unsafe_allow_html=True)
else:
    # Page 1: Bias Meter
    if page == "Bias Meter":
        st.markdown("<h1 style='font-size: 2rem; font-weight: 700; color: #F9FAFB; margin-bottom: 8px;'>Bias Meter</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 24px;'>Aggregated continuous bias index based on emotional intensity, clickbait indicators, and perceived alignment offset.</p>", unsafe_allow_html=True)
        
        # Sort profiles to make chart look clean
        df_chart = profiles_df.sort_values(by="bias_score")
        
        # Map perceived leans to clean, high-end professional colors
        color_map = {
            "left": "#3B82F6",         # Sleek Accent Blue
            "center-left": "#0D9488",  # Premium Teal
            "center": "#4B5563",       # Professional Slate Gray
            "right": "#E11D48"         # Vibrant Rose Red
        }
        
        df_chart["color"] = df_chart["lean"].map(color_map)
        
        fig = go.Figure()
        
        for idx, row in df_chart.iterrows():
            fig.add_trace(go.Bar(
                name=row["outlet"],
                y=[row["outlet"]],
                x=[row["bias_score"]],
                orientation='h',
                marker=dict(color=row["color"], line=dict(color='rgba(255,255,255,0.04)', width=1)),
                hovertemplate=(
                    f"<b>{row['outlet']}</b><br>"
                    f"Lean: {row['lean'].upper()}<br>"
                    f"Bias Index: {row['bias_score']:.2f}<br>"
                    f"Clickbait: {row['avg_clickbait']:.1f}%<br>"
                    f"Emotion Score: {row['avg_emotion']:.2f}<br>"
                    f"Articles Scored: {row['article_count']}<extra></extra>"
                )
            ))
            
        fig.update_layout(
            barmode='stack',
            xaxis=dict(
                title="Continuous Bias Index (-1.0 = Left, 0 = Balanced Center, +1.0 = Right)",
                tickmode='array',
                tickvals=[-1.0, -0.5, 0, 0.5, 1.0],
                ticktext=['Left Align', 'Center-Left', 'Balanced Center', 'Center-Right', 'Right Align'],
                range=[-1.0, 1.0],
                gridcolor='rgba(255,255,255,0.03)',
                zerolinecolor='rgba(255,255,255,0.1)',
                color='#94a3b8',
                title_font=dict(size=11, color='#94A3B8')
            ),
            yaxis=dict(
                color='#94a3b8',
                showgrid=False
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            height=350,
            margin=dict(l=0, r=0, t=10, b=40)
        )
        
        # Render horizontal bar chart inside a card
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Highlighted outlets
        col1, col2, col3 = st.columns(3)
        
        with col1:
            most_emotive = profiles_df.sort_values(by="avg_emotion", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='premium-card'>
                <span style='font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #F472B6;'>Highest Emotional Charge</span>
                <h2 style='font-size: 1.5rem; font-weight: 700; margin: 12px 0px; color: #F9FAFB;'>{most_emotive['outlet']}</h2>
                <p style='color:#94A3B8; font-size: 0.85rem; margin: 0;'>Average emotion score: <b style='color:#F9FAFB;'>{most_emotive['avg_emotion']:.2f}</b> (0 to 1 scale)</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            most_clickbait = profiles_df.sort_values(by="avg_clickbait", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='premium-card'>
                <span style='font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #F59E0B;'>Highest Clickbait Velocity</span>
                <h2 style='font-size: 1.5rem; font-weight: 700; margin: 12px 0px; color: #F9FAFB;'>{most_clickbait['outlet']}</h2>
                <p style='color:#94A3B8; font-size: 0.85rem; margin: 0;'>Average clickbait: <b style='color:#F9FAFB;'>{most_clickbait['avg_clickbait']:.1f}%</b> sensationalist probability</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            most_articles = profiles_df.sort_values(by="article_count", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='premium-card'>
                <span style='font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #3B82F6;'>Volume Leader</span>
                <h2 style='font-size: 1.5rem; font-weight: 700; margin: 12px 0px; color: #F9FAFB;'>{most_articles['outlet']}</h2>
                <p style='color:#94A3B8; font-size: 0.85rem; margin: 0;'>Total articles scored: <b style='color:#F9FAFB;'>{most_articles['article_count']}</b> stories parsed</p>
            </div>
            """, unsafe_allow_html=True)

    # Page 2: Live Auditor
    elif page == "Live Auditor":
        st.markdown("<h1 style='font-size: 2rem; font-weight: 700; color: #F9FAFB; margin-bottom: 8px;'>Live Article Auditor</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 24px;'>Paste the URL of any Indian news article to scrape and analyze its linguistic metrics in real time.</p>", unsafe_allow_html=True)
        
        # User input field
        url_input = st.text_input("Enter Article URL:", placeholder="https://www.ndtv.com/india-news/...")
        
        if st.button("Run Live Audit", type="primary"):
            if not url_input.strip():
                st.warning("Please enter a valid URL.")
            else:
                with st.spinner("Scraping article contents and metadata..."):
                    article = scraper.scrape_single_article(url_input)
                    
                if "error" in article:
                    st.error(f"Failed: {article['error']}")
                else:
                    st.success("Article successfully scraped. Executing linguistic analysis...")
                    
                    headline = article["headline"]
                    body = article["body"]
                    
                    # 1. Headline Emotion Scorer
                    with st.spinner("Analyzing emotional intensity..."):
                        emotion_scores = emotion.score_emotion([headline])
                        emo_score = emotion_scores[0] if emotion_scores else 0.0
                        
                    # 2. Headline Clickbait Sensationalism Scorer
                    with st.spinner("Analyzing headline sensationalism..."):
                        clickbait_scores = clickbait.score_clickbait([headline])
                        cb_score = clickbait_scores[0] if clickbait_scores else 0.0
                        
                    # 3. Body Entity Extraction + Context Sentiment Scorer
                    with st.spinner("Performing named entity sentiment mapping..."):
                        text_to_analyze = body if len(body.strip()) > 50 else headline
                        entity_sentiments = entity.extract_entities(text_to_analyze)
                        
                    # 4. Map Perceived Lean Offset
                    lean_offsets = {
                        "left": -0.3,
                        "center-left": -0.15,
                        "center": 0.0,
                        "right": 0.3
                    }
                    
                    perceived_lean = "unknown (assumed center)"
                    lean_offset = 0.0
                    
                    outlets_file = os.path.join("data", "outlets.json")
                    with open(outlets_file, "r") as f:
                        outlets_config = json.load(f)
                        
                    matched_outlet = None
                    for name, config in outlets_config.items():
                        domain = config["rss"].split("//")[-1].split("/")[0].replace("www.", "")
                        url_clean = url_input.split("//")[-1].split("/")[0].replace("www.", "")
                        if domain in url_clean or url_clean in domain:
                            matched_outlet = name
                            perceived_lean = config["lean"]
                            lean_offset = lean_offsets.get(perceived_lean, 0.0)
                            break
                            
                    norm_clickbait = cb_score / 100.0
                    bias_score = (emo_score * 0.3) + (norm_clickbait * 0.2) + lean_offset
                    bias_score = max(-1.0, min(1.0, bias_score))
                    
                    st.markdown("---")
                    st.markdown("<h2 style='text-align: center; margin-bottom: 24px;'>Audit Results</h2>", unsafe_allow_html=True)
                    
                    # Meta Card
                    st.markdown(f"""
                    <div class="premium-card">
                        <span class="badge badge-center-left" style="font-size:0.75rem;">Live Audited Source</span>
                        <h3 style="margin-top: 12px; font-size: 1.4rem; font-weight: 700; color:#F9FAFB; background:none; -webkit-text-fill-color:initial; margin-bottom: 8px;">{headline}</h3>
                        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 4px;"><b>Source URL:</b> <a href="{url_input}" target="_blank" style="color: #3B82F6; text-decoration: none;">{url_input}</a></p>
                        <p style="color: #94a3b8; font-size: 0.85rem; margin: 0;"><b>Mapped Perceived Editorial Lean:</b> <span style="text-transform:uppercase; font-weight:700; color: #F9FAFB;">{perceived_lean}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metrics Columns
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        emo_label = "Neutral" if emo_score < 0.3 else "Moderately Charged" if emo_score < 0.6 else "Highly Charged"
                        st.markdown(f"""
                        <div class="premium-card" style="text-align: center;">
                            <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #F472B6; letter-spacing: 0.05em;">Emotion Intensity</span>
                            <h2 style="font-size: 2.2rem; font-weight: 700; margin: 12px 0px; color: #F9FAFB;">{emo_score:.2f}</h2>
                            <span class="badge" style="background-color:rgba(244, 114, 182, 0.06); color:#F472B6; border: 1px solid rgba(244, 114, 182, 0.15);">{emo_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        cb_label = "Factual" if cb_score < 30 else "Sensationalist" if cb_score < 70 else "Clickbait"
                        st.markdown(f"""
                        <div class="premium-card" style="text-align: center;">
                            <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #F59E0B; letter-spacing: 0.05em;">Sensationalism Index</span>
                            <h2 style="font-size: 2.2rem; font-weight: 700; margin: 12px 0px; color: #F9FAFB;">{cb_score:.1f}%</h2>
                            <span class="badge" style="background-color:rgba(245, 158, 11, 0.06); color:#F59E0B; border: 1px solid rgba(245, 158, 11, 0.15);">{cb_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col3:
                        bias_label = "Left Lean" if bias_score < -0.15 else "Balanced Center" if bias_score < 0.15 else "Right Lean"
                        bias_color = "#3B82F6" if bias_score < -0.15 else "#6B7280" if bias_score < 0.15 else "#E11D48"
                        st.markdown(f"""
                        <div class="premium-card" style="text-align: center;">
                            <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: {bias_color}; letter-spacing: 0.05em;">Continuous Bias Index</span>
                            <h2 style="font-size: 2.2rem; font-weight: 700; margin: 12px 0px; color: {bias_color};">{bias_score:.3f}</h2>
                            <span class="badge" style="background-color:rgba(255, 255, 255, 0.03); color:#F9FAFB; border: 1px solid {bias_color};">{bias_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # Entity Sentiment Table
                    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size: 1.1rem; font-weight: 600; margin-top:0px; margin-bottom: 16px; color:#F9FAFB;'>Political Entity Sentiment Mapping</h3>", unsafe_allow_html=True)
                    if not entity_sentiments:
                        st.info("No tracked Indian political entities identified in this article body.")
                    else:
                        ent_df = pd.DataFrame([
                            {"Entity Name": k, "Context Sentiment": round(v, 3), "Context Sentiment Label": "Positive" if v > 0.1 else "Negative" if v < -0.1 else "Neutral"}
                            for k, v in entity_sentiments.items()
                        ])
                        st.dataframe(ent_df, use_container_width=True, hide_index=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Full body text view
                    with st.expander("View Extracted Text"):
                        st.write(body)

    # Page 3: Leaderboard
    elif page == "Leaderboard":
        st.markdown("<h1 style='font-size: 2rem; font-weight: 700; color: #F9FAFB; margin-bottom: 8px;'>Media Outlet Leaderboard</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 24px;'>Compare grammatical and sentiment indexes side-by-side. Click headers to sort outlets.</p>", unsafe_allow_html=True)
        
        lead_df = profiles_df.copy()
        lead_df = lead_df.rename(columns={
            "outlet": "Outlet",
            "lean": "Lean",
            "avg_emotion": "Emotion Index",
            "avg_clickbait": "Sensationalism (%)",
            "article_count": "Articles Audited",
            "bias_score": "Continuous Bias Score",
            "top_entity": "Top Entity Mentions",
            "top_entity_sentiment": "Top Entity Sentiment"
        })
        
        # Round digits for clean visual format
        lead_df["Emotion Index"] = lead_df["Emotion Index"].round(3)
        lead_df["Sensationalism (%)"] = lead_df["Sensationalism (%)"].round(1)
        lead_df["Continuous Bias Score"] = lead_df["Continuous Bias Score"].round(3)
        lead_df["Top Entity Sentiment"] = lead_df["Top Entity Sentiment"].round(3)
        
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.dataframe(
            lead_df.sort_values(by="Continuous Bias Score"), 
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download Button
        csv_data = lead_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Leaderboard as CSV",
            data=csv_data,
            file_name="indian_news_bias_leaderboard.csv",
            mime="text/csv",
        )

    # Page 4: Story Compare
    elif page == "Story Compare":
        st.markdown("<h1 style='font-size: 2rem; font-weight: 700; color: #F9FAFB; margin-bottom: 8px;'>Cross-Outlet Story Comparison</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 24px;'>Discover the contrast in language framing. Using semantic search, we pair stories covering the same real-world event across different outlets and calculate framing divergence.</p>", unsafe_allow_html=True)
        
        if pairs_df.empty:
            st.info("Additional articles from differing outlets must be indexed to surface overlapping story pairings.")
        else:
            # Select boxes for matched stories
            options = []
            for idx, row in pairs_df.iterrows():
                title = f"Divergence: {row['divergence']:.2f} | Story: {row['headline_a'][:50]}..."
                options.append((idx, title))
                
            selected_idx = st.selectbox(
                "Choose a paired story to compare:",
                options=range(len(options)),
                format_func=lambda x: options[x][1]
            )
            
            story = pairs_df.iloc[selected_idx]
            div_val = story['divergence']
            
            # Premium story divergence header
            st.markdown(f"""
            <div class="premium-card" style="margin-bottom: 24px; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-right: 12px;">Framing Divergence</span>
                        <span style="font-size: 1.1rem; font-weight: 700; color: #EC4899;">{div_val:.2f}</span>
                    </div>
                    <div>
                        <span style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-right: 12px;">Headline Semantic Similarity</span>
                        <span style="font-size: 1.1rem; font-weight: 700; color: #10B981;">{story['similarity']*100:.1f}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            
            # Outlet A
            with col_a:
                st.markdown(f"""
                <div class="premium-card">
                    <span class="badge badge-neutral" style="background-color: rgba(255, 255, 255, 0.04); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.7rem; font-weight:700;">{story['outlet_a'].upper()}</span>
                    <h3 style="margin-top: 16px; font-size: 1.25rem; font-weight: 600; line-height: 1.4; color: #F9FAFB; background: none; -webkit-text-fill-color: initial;">{story['headline_a']}</h3>
                    <div style="margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">Emotional Intensity</span>
                            <span style="color: #F9FAFB; font-size: 0.85rem; font-weight: 600;">{story['emotion_a']:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">Clickbait Probability</span>
                            <span style="color: #F9FAFB; font-size: 0.85rem; font-weight: 600;">{story['clickbait_a']:.1f}%</span>
                        </div>
                        <a href="{story['url_a']}" target="_blank" style="display: inline-block; font-size: 0.8rem; color: #3B82F6; text-decoration: none; font-weight: 600;">Read Source Article &rarr;</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Outlet B
            with col_b:
                st.markdown(f"""
                <div class="premium-card">
                    <span class="badge badge-neutral" style="background-color: rgba(255, 255, 255, 0.04); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.7rem; font-weight:700;">{story['outlet_b'].upper()}</span>
                    <h3 style="margin-top: 16px; font-size: 1.25rem; font-weight: 600; line-height: 1.4; color: #F9FAFB; background: none; -webkit-text-fill-color: initial;">{story['headline_b']}</h3>
                    <div style="margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">Emotional Intensity</span>
                            <span style="color: #F9FAFB; font-size: 0.85rem; font-weight: 600;">{story['emotion_b']:.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">Clickbait Probability</span>
                            <span style="color: #F9FAFB; font-size: 0.85rem; font-weight: 600;">{story['clickbait_b']:.1f}%</span>
                        </div>
                        <a href="{story['url_b']}" target="_blank" style="display: inline-block; font-size: 0.8rem; color: #3B82F6; text-decoration: none; font-weight: 600;">Read Source Article &rarr;</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Page 5: About
    elif page == "About":
        st.markdown("<h1 style='font-size: 2rem; font-weight: 700; color: #F9FAFB; margin-bottom: 8px;'>Methodology and Architecture</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 24px;'>Overview of NLP models and algorithms applied to analyze linguistics metrics across news outlets.</p>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="premium-card">
            <h3 style="font-size: 1.2rem; font-weight: 600; color: #F9FAFB; margin-top: 0; margin-bottom: 16px;">System Goal</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.7; margin-bottom: 0;">
                The Indian News Bias Auditor parses headlines and body text from RSS news feeds to execute programmatic text linguistics evaluations. It addresses the lack of quantitative research data in Indian journalism by introducing automated multi-lens NLP scoring layers.
            </p>
        </div>
        
        <div class="premium-card">
            <h3 style="font-size: 1.2rem; font-weight: 600; color: #F9FAFB; margin-top: 0; margin-bottom: 20px;">NLP Pipeline Stages</h3>
            
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 1rem; font-weight: 600; color: #F9FAFB; margin-bottom: 6px;">1. Emotion Intensity (RoBERTa)</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                    We leverage the <code>j-hartmann/emotion-english-distilroberta-base</code> transformer model to predict the probabilities of specific emotions. The overall Emotion Intensity represents the total probability of non-neutral language expression (calculated as <code>1.0 - neutral_probability</code>).
                </p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 1rem; font-weight: 600; color: #F9FAFB; margin-bottom: 6px;">2. Clickbait Sensationalism Index (BERT)</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                    We use the <code>valurank/distilroberta-clickbait</code> classification pipeline to compute the probability (from 0% to 100%) that a headline uses clickbait hooks, exaggerations, or extreme superlatives.
                </p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 1rem; font-weight: 600; color: #F9FAFB; margin-bottom: 6px;">3. Named Entity Sentiment Context (spaCy + DistilBERT)</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                    Using named entity recognition via <code>en_core_web_sm</code>, we extract major political entities. We isolate the surrounding sentence mentioning each entity and run it through <code>distilbert-base-uncased-finetuned-sst-2-english</code> to score the context sentiment between -1.0 (highly negative) and +1.0 (highly positive).
                </p>
            </div>
            
            <div style="margin-bottom: 0px;">
                <h4 style="font-size: 1rem; font-weight: 600; color: #F9FAFB; margin-bottom: 6px;">4. Headline Framing Divergence (Sentence-Transformers)</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                    To isolate differences in coverage framing, we generate semantic embeddings of headlines using the <code>paraphrase-multilingual-MiniLM-L12-v2</code> model. We pair articles showing a high cosine similarity score across differing outlets and calculate framing divergence as the absolute difference in headline emotional intensity.
                </p>
            </div>
        </div>
        
        <div class="premium-card">
            <h3 style="font-size: 1.2rem; font-weight: 600; color: #F9FAFB; margin-top: 0; margin-bottom: 12px;">Disclaimer</h3>
            <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                The scores rendered on this dashboard are mathematical metrics derived using pretrained machine learning models analyzing specific linguistic choices. They represent descriptive resources for media literacy and linguistic research, and do not constitute human moral judgments, qualitative verdicts of factual credibility, or proof of intent.
            </p>
        </div>
        """, unsafe_allow_html=True)
