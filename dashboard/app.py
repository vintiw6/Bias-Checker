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
# Premium Aesthetics & Page Config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Indian News Bias Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern, premium custom CSS
st.markdown("""
<style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Sleek Obsidian Dark Theme background */
    .stApp {
        background: #070a13;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.05) 0, transparent 50%), 
            radial-gradient(at 100% 0%, rgba(14, 165, 233, 0.04) 0, transparent 40%),
            radial-gradient(at 50% 100%, rgba(15, 23, 42, 0.8) 0, transparent 60%);
        color: #e2e8f0;
    }
    
    /* Clean Minimalist Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.02);
    }
    
    /* High-End Platinum & Silver Header Styling */
    h1, h2, h3 {
        font-weight: 700 !important;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        letter-spacing: -0.03em;
    }
    
    /* Obsidian Card panels */
    .metric-card {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(14, 165, 233, 0.25);
        box-shadow: 0 6px 25px rgba(14, 165, 233, 0.08);
    }
    
    /* Sleek Low-Opacity Outline Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        border-radius: 6px;
        text-transform: uppercase;
        margin-right: 8px;
        letter-spacing: 0.02em;
    }
    .badge-left { 
        background-color: rgba(14, 165, 233, 0.08); 
        color: #38bdf8; 
        border: 1px solid rgba(14, 165, 233, 0.2); 
    }
    .badge-center-left { 
        background-color: rgba(20, 184, 166, 0.08); 
        color: #2dd4bf; 
        border: 1px solid rgba(20, 184, 166, 0.2); 
    }
    .badge-center { 
        background-color: rgba(100, 116, 139, 0.08); 
        color: #cbd5e1; 
        border: 1px solid rgba(100, 116, 139, 0.2); 
    }
    .badge-right { 
        background-color: rgba(249, 115, 22, 0.08); 
        color: #fb923c; 
        border: 1px solid rgba(249, 115, 22, 0.2); 
    }
    
    .badge-divergence { 
        background-color: rgba(239, 68, 68, 0.08); 
        color: #fca5a5; 
        border: 1px solid rgba(239, 68, 68, 0.2); 
    }
    
    /* Article Box Panel */
    .article-box {
        background: rgba(15, 23, 42, 0.25);
        border-left: 3px solid #0ea5e9;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.01);
        border-right: 1px solid rgba(255, 255, 255, 0.01);
        border-bottom: 1px solid rgba(255, 255, 255, 0.01);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loader
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_dashboard_data():
    """Fetches articles, outlet profiles, and story pairs."""
    db.init_db()
    raw_articles = db.get_all_scored()
    profiles_df = aggregator.compute_outlet_profiles()
    
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
    st.image("https://img.icons8.com/nolan/128/binoculars.png", width=70)
    st.markdown("<h2 style='margin-top:0px;'>Bias Auditor</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.85rem;'>Real-time AI-powered linguistics auditing of Indian news media.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation Radio
    page = st.radio(
        "Navigate",
        ["🔍 Bias Meter", "⚡ Live Auditor", "📊 Leaderboard", "⚖️ Story Compare", "💡 About"],
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
        st.markdown(f"**Last Scrape Update:**\n`{formatted_date}`")
        st.markdown(f"**Articles Scored:** `{len(articles_df)}`")
    else:
        st.info("No articles scored yet. Run the scraper and pipeline runner to populate data.")

# -----------------------------------------------------------------------------
# Main Dashboard Pages
# -----------------------------------------------------------------------------
if articles_df.empty or profiles_df.empty:
    st.markdown("# 🔍 Indian News Bias Auditor")
    st.warning("⚠️ No scored articles found in the database. Please run `python src/scraper.py` and then `python src/runner.py` to collect and analyze news data.")
    st.markdown("""
    ### Quick Start Local Dev Instructions:
    1. Activate your virtual environment:
       ```bash
       .venv\\Scripts\\activate
       ```
    2. Run the RSS scraper to pull active stories:
       ```bash
       python src/scraper.py
       ```
    3. Run the scoring pipeline to analyze them using RoBERTa, DistilBERT, spaCy, and Sentence-Transformers:
       ```bash
       python src/runner.py
       ```
    4. Refresh this dashboard!
    """)
else:
    # Page 1: Bias Meter
    if "Bias Meter" in page:
        st.markdown("# 🔍 Indian News Bias Meter")
        st.markdown("Aggregated continuous bias index based on emotional intensity, clickbait indicators, and perceived alignment offset.")
        
        # Plotly horizontal bar chart for continuous bias scores
        # Sort profiles to make chart look clean
        df_chart = profiles_df.sort_values(by="bias_score")
        
        # Map perceived leans to clean, high-end professional colors
        color_map = {
            "left": "#0ea5e9",         # Sleek Ice Blue
            "center-left": "#0d9488",  # Premium Teal
            "center": "#475569",       # Professional Slate
            "right": "#ea580c"         # Cohesive Saffron Orange
        }
        
        df_chart["color"] = df_chart["lean"].map(color_map)
        
        fig = go.Figure()
        
        for idx, row in df_chart.iterrows():
            fig.add_trace(go.Bar(
                name=row["outlet"],
                y=[row["outlet"]],
                x=[row["bias_score"]],
                orientation='h',
                marker=dict(color=row["color"], line=dict(color='rgba(255,255,255,0.1)', width=1)),
                hovertemplate=(
                    f"<b>{row['outlet']}</b><br>"
                    f"Perceived Lean: {row['lean'].upper()}<br>"
                    f"Continuous Bias Index: {row['bias_score']:.2f}<br>"
                    f"Avg Clickbait Score: {row['avg_clickbait']:.1f}%<br>"
                    f"Avg Emotion Score: {row['avg_emotion']:.2f}<br>"
                    f"Articles Analyzed: {row['article_count']}<extra></extra>"
                )
            ))
            
        fig.update_layout(
            barmode='stack',
            xaxis=dict(
                title="Continuous Bias Index (-1.0 = Left, 0 = Balanced Center, +1.0 = Right)",
                tickmode='array',
                tickvals=[-1.0, -0.5, 0, 0.5, 1.0],
                ticktext=['Left Align', 'Center-Left', 'Center / Balanced', 'Center-Right', 'Right Align'],
                range=[-1.0, 1.0],
                gridcolor='rgba(255,255,255,0.05)',
                zerolinecolor='rgba(255,255,255,0.2)',
                color='#94a3b8'
            ),
            yaxis=dict(
                color='#94a3b8',
                showgrid=False
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=20, b=40)
        )
        
        # Render horizontal bar chart inside a card
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Highlighted outlets
        col1, col2, col3 = st.columns(3)
        
        with col1:
            most_emotive = profiles_df.sort_values(by="avg_emotion", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='font-size: 1.1rem; color: #a855f7; margin-top:0px;'>🔥 Highest Emotional Charge</h3>
                <h2 style='font-size: 1.6rem; margin: 8px 0px;'>{most_emotive['outlet']}</h2>
                <p style='color:#94a3b8; font-size: 0.9rem;'>Average emotion score: <b>{most_emotive['avg_emotion']:.2f}</b> (0-1 scale)</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            most_clickbait = profiles_df.sort_values(by="avg_clickbait", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='font-size: 1.1rem; color: #ec4899; margin-top:0px;'>🎣 Highest Clickbait Index</h3>
                <h2 style='font-size: 1.6rem; margin: 8px 0px;'>{most_clickbait['outlet']}</h2>
                <p style='color:#94a3b8; font-size: 0.9rem;'>Average clickbait: <b>{most_clickbait['avg_clickbait']:.1f}%</b> sensationalist probability</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            most_articles = profiles_df.sort_values(by="article_count", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='metric-card'>
                <h3 style='font-size: 1.1rem; color: #6366f1; margin-top:0px;'>📚 Most Active Coverage</h3>
                <h2 style='font-size: 1.6rem; margin: 8px 0px;'>{most_articles['outlet']}</h2>
                <p style='color:#94a3b8; font-size: 0.9rem;'>Total articles scored: <b>{most_articles['article_count']}</b> stories parsed</p>
            </div>
            """, unsafe_allow_html=True)

    # Page 1.5: Live Auditor
    elif "Live Auditor" in page:
        st.markdown("# ⚡ Live Article Auditor")
        st.markdown("Paste the URL of any Indian news article to scrape and analyze its linguistic metrics in real time.")
        
        # User input field
        url_input = st.text_input("Enter article URL:", placeholder="https://www.ndtv.com/india-news/...")
        
        if st.button("🔍 Run Live Audit", type="primary"):
            if not url_input.strip():
                st.warning("Please enter a valid URL.")
            else:
                with st.spinner("Scraping article contents and metadata..."):
                    article = scraper.scrape_single_article(url_input)
                    
                if "error" in article:
                    st.error(f"❌ {article['error']}")
                else:
                    st.success("✅ Article successfully scraped! Running linguistic analyzers...")
                    
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
                        # Simple substring match on URL domain
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
                    st.markdown("<h2 style='text-align: center;'>🔍 Audit Results</h2>", unsafe_allow_html=True)
                    
                    # Meta Card
                    st.markdown(f"""
                    <div class="metric-card">
                        <span class="badge badge-center-left" style="font-size:0.8rem;">Live Audited Source</span>
                        <h3 style="margin-top: 12px; font-size: 1.5rem; font-weight: 700; color:#ffffff; background:none; -webkit-text-fill-color:initial;">{headline}</h3>
                        <p style="color: #94a3b8; font-size: 0.95rem; margin-top:8px;"><b>Source URL:</b> <a href="{url_input}" target="_blank" style="color: #818cf8;">{url_input}</a></p>
                        <p style="color: #94a3b8; font-size: 0.95rem;"><b>Mapped Perceived Editorial Lean:</b> <span style="text-transform:uppercase; font-weight:700;">{perceived_lean}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metrics Columns
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        emo_label = "Neutral" if emo_score < 0.3 else "Moderately Charged" if emo_score < 0.6 else "Highly Charged"
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <h3 style="font-size: 1.1rem; color: #a855f7; margin-top:0px;">🔥 Emotion Intensity</h3>
                            <h2 style="font-size: 2.2rem; margin: 12px 0px;">{emo_score:.2f}</h2>
                            <span class="badge" style="background-color:rgba(168, 85, 247, 0.2); color:#c084fc; border: 1px solid #a855f7;">{emo_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        cb_label = "Factual / Objective" if cb_score < 30 else "Sensationalist Hook" if cb_score < 70 else "Clickbait / Urgency Trap"
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <h3 style="font-size: 1.1rem; color: #ec4899; margin-top:0px;">🎣 Sensationalism Index</h3>
                            <h2 style="font-size: 2.2rem; margin: 12px 0px;">{cb_score:.1f}%</h2>
                            <span class="badge" style="background-color:rgba(236, 72, 153, 0.2); color:#f472b6; border: 1px solid #ec4899;">{cb_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col3:
                        bias_label = "Left Lean" if bias_score < -0.15 else "Balanced Center" if bias_score < 0.15 else "Right Lean"
                        bias_color = "#3b82f6" if bias_score < -0.15 else "#6b7280" if bias_score < 0.15 else "#f97316"
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <h3 style="font-size: 1.1rem; color: {bias_color}; margin-top:0px;">⚖️ Continuous Bias Index</h3>
                            <h2 style="font-size: 2.2rem; margin: 12px 0px; color: {bias_color};">{bias_score:.3f}</h2>
                            <span class="badge" style="background-color:rgba(255, 255, 255, 0.05); color:#f3f4f6; border: 1px solid {bias_color};">{bias_label}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # Entity Sentiment Table
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown("### 🏷️ Identified Political Entity Sentiment Mapping")
                    if not entity_sentiments:
                        st.info("No tracked Indian political entities identified in this article body.")
                    else:
                        ent_df = pd.DataFrame([
                            {"Entity Name": k, "Context Sentiment (-1.0 to +1.0)": round(v, 3), "Context Sentiment Label": "Positive" if v > 0.1 else "Negative" if v < -0.1 else "Neutral"}
                            for k, v in entity_sentiments.items()
                        ])
                        st.dataframe(ent_df, use_container_width=True, hide_index=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Full body text view
                    with st.expander("📖 View Extracted Article Text"):
                        st.write(body)

    # Page 2: Leaderboard
    elif "Leaderboard" in page:
        st.markdown("# 📊 Media Outlet Leaderboard")
        st.markdown("Compare grammatical & sentiment indexes side-by-side. Click headers to sort outlets.")
        
        # Standardize columns for user readability
        lead_df = profiles_df.copy()
        lead_df = lead_df.rename(columns={
            "outlet": "Outlet",
            "lean": "Perceived Lean",
            "avg_emotion": "Emotion Index (0-1)",
            "avg_clickbait": "Sensationalism (%)",
            "article_count": "Articles Audited",
            "bias_score": "Continuous Bias Score",
            "top_entity": "Top Entity Mentions",
            "top_entity_sentiment": "Top Entity Sentiment"
        })
        
        # Round digits for clean visual format
        lead_df["Emotion Index (0-1)"] = lead_df["Emotion Index (0-1)"].round(3)
        lead_df["Sensationalism (%)"] = lead_df["Sensationalism (%)"].round(1)
        lead_df["Continuous Bias Score"] = lead_df["Continuous Bias Score"].round(3)
        lead_df["Top Entity Sentiment"] = lead_df["Top Entity Sentiment"].round(3)
        
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.dataframe(
            lead_df.sort_values(by="Continuous Bias Score"), 
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download Button
        csv = lead_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Leaderboard as CSV",
            data=csv,
            file_name="indian_news_bias_leaderboard.csv",
            mime="text/csv",
        )

    # Page 3: Story Compare
    elif "Story Compare" in page:
        st.markdown("# ⚖️ Cross-Outlet Story Comparison")
        st.markdown("Discover the contrast in language framing. Using semantic search, we pair stories covering the same real-world event across different outlets and calculate framing divergence.")
        
        if pairs_df.empty:
            st.info("💡 Scrape more articles from differing outlets to surface overlapping news coverage pairings!")
        else:
            # Select boxes for matched stories
            options = []
            for idx, row in pairs_df.iterrows():
                # Formulate a dropdown title
                title = f"Divergence: {row['divergence']:.2f} | Story: {row['headline_a'][:50]}..."
                options.append((idx, title))
                
            selected_idx = st.selectbox(
                "Choose a paired story to compare:",
                options=range(len(options)),
                format_func=lambda x: options[x][1]
            )
            
            story = pairs_df.iloc[selected_idx]
            
            # Colored divergence header
            div_val = story['divergence']
            div_color = "red" if div_val > 0.4 else "orange" if div_val > 0.2 else "green"
            
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 16px; margin-bottom: 24px;">
                <span class="badge badge-divergence" style="font-size: 0.9rem; padding: 6px 12px;">Framing Divergence: {div_val:.2f}</span>
                <span style="color: #94a3b8; font-size: 0.95rem;">Headline Semantic Similarity: <b>{story['similarity']*100:.1f}%</b></span>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            
            # Outlet A
            with col_a:
                st.markdown(f"""
                <div class="metric-card">
                    <span class="badge badge-{story['outlet_a'].lower().replace(' ', '-')}">{story['outlet_a']}</span>
                    <h3 style="margin-top: 12px; font-size: 1.4rem; font-weight: 700; color: #ffffff; background: none; -webkit-text-fill-color: initial;">{story['headline_a']}</h3>
                    <hr style="border-color: rgba(255,255,255,0.05); margin: 16px 0px;"/>
                    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 8px;">🔥 Emotion Intensity Score: <b>{story['emotion_a']:.2f}</b></p>
                    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 8px;">🎣 Clickbait Sensationalism: <b>{story['clickbait_a']:.1f}%</b></p>
                    <a href="{story['url_a']}" target="_blank" style="display:inline-block; margin-top: 12px; color: #818cf8; text-decoration: none; font-weight: 600;">🔗 Read Source Article</a>
                </div>
                """, unsafe_allow_html=True)
                
            # Outlet B
            with col_b:
                st.markdown(f"""
                <div class="metric-card">
                    <span class="badge badge-{story['outlet_b'].lower().replace(' ', '-')}">{story['outlet_b']}</span>
                    <h3 style="margin-top: 12px; font-size: 1.4rem; font-weight: 700; color: #ffffff; background: none; -webkit-text-fill-color: initial;">{story['headline_b']}</h3>
                    <hr style="border-color: rgba(255,255,255,0.05); margin: 16px 0px;"/>
                    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 8px;">🔥 Emotion Intensity Score: <b>{story['emotion_b']:.2f}</b></p>
                    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 8px;">🎣 Clickbait Sensationalism: <b>{story['clickbait_b']:.1f}%</b></p>
                    <a href="{story['url_b']}" target="_blank" style="display:inline-block; margin-top: 12px; color: #818cf8; text-decoration: none; font-weight: 600;">🔗 Read Source Article</a>
                </div>
                """, unsafe_allow_html=True)

    # Page 4: About
    elif "About" in page:
        st.markdown("# 💡 Project Methodology & About")
        
        st.markdown("""
        ### Objective
        The Indian News Bias Auditor parses headlines and bodies from RSS news feeds to run programmatic text linguistics evaluations. Unlike Western media, which is extensively graded on bias indices (such as AllSides), Indian journalism has a significant lack of quantitative research data. This project solves that gap with automated NLP layers.
        
        ---
        
        ### NLP Pipelines Applied
        
        1. **Emotion Intensity (RoBERTa)**:
           We leverage the `j-hartmann/emotion-english-distilroberta-base` transformer model to predict the probabilities of emotions (Anger, Disgust, Fear, Joy, Sadness, Surprise, Neutral). The overall **Emotion Intensity** score represents the total probability of non-neutral language expression (`1.0 - neutral_probability`).
           
        2. **Sensationalism / Clickbait Index (BERT)**:
           We use the `mrm8488/bert-mini-finetuned-clickbait` classification pipeline to compute the probability (from 0% to 100%) that a headline uses clickbait tricks (exaggerations, emotional traps, vague references, or extreme superlatives).
           
        3. **Entity Context Sentiment Analysis (spaCy + DistilBERT)**:
           Using named entity recognition via `en_core_web_sm`, we extract major political entities (e.g., *Modi, BJP, Congress, Opposition, Rahul Gandhi*). We locate the exact sentence mentioning each entity and run it through `distilbert-base-uncased-finetuned-sst-2-english` to score the context sentiment between **-1.0 (highly negative)** and **+1.0 (highly positive)**.
           
        4. **Headline Framing Divergence (Sentence-Transformers)**:
           To isolate the "spin" or editorial framing applied to identical news, we use semantic headline embeddings generated via the `paraphrase-multilingual-MiniLM-L12-v2` transformer model. We pair articles that show over **72% similarity** across different outlets, and compute **Framing Divergence** as the absolute difference in emotional intensity between their respective headlines.
           
        ---
        
        ### Disclaimers & Ethics
        
        > [!WARNING]
        > **Descriptive Metrics, Not Verdicts:**
        > The scores rendered on this dashboard are mathematical metrics derived using pretrained machine learning models analyzing linguistic choices. They do not constitute human moral judgments, qualitative verdicts of factual credibility, or proof of intent. These are descriptive resources for media literacy and research.
        """, unsafe_allow_html=True)
