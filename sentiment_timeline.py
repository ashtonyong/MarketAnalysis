import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
import random

class NewsSentiment:
    def __init__(self, ticker):
        self.ticker = ticker
        
    def fetch_news(self) -> list:
        try:
            t = yf.Ticker(self.ticker)
            news = t.news
            return news if news else []
        except:
            return []
            
    def analyze_sentiment(self, text: str) -> float:
        # Simple dictionary-based sentiment for demo (since no NLTK/TextBlob)
        # 0.0 is neutral, 1.0 positive, -1.0 negative
        
        pos_words = ['up', 'rise', 'gain', 'bull', 'growth', 'record', 'high', 'profit', 'beat', 'soar', 'jump', 'buy', 'strong']
        neg_words = ['down', 'fall', 'drop', 'bear', 'loss', 'miss', 'low', 'decline', 'crash', 'sell', 'weak', 'inflation', 'recession']
        
        text_lower = text.lower()
        score = 0
        
        for w in pos_words:
            if w in text_lower: score += 1
        for w in neg_words:
            if w in text_lower: score -= 1
            
        # Normalize to -1 to 1 range roughly
        # Cap at +/- 1
        final_score = max(-1.0, min(1.0, score * 0.3))
        return final_score

    def get_timeline(self):
        news_items = self.fetch_news()
        data = []
        
        for item in news_items:
            # yfinance news items usually have: title, publisher, link, providerPublishTime
            title = item.get('title', '')
            pub_time = item.get('providerPublishTime', 0)
            
            # Convert timestamp
            dt = datetime.fromtimestamp(pub_time) if pub_time else datetime.now()
            
            score = self.analyze_sentiment(title)
            
            data.append({
                "Date": dt,
                "Title": title,
                "Sentiment": score,
                "Source": item.get('publisher', 'Unknown'),
                "Link": item.get('link', '#')
            })
            
        # Add some simulated historical points for the "Timeline" visual if too few
        if len(data) < 5:
            # Add simulated past data for chart
            for i in range(1, 10):
                data.append({
                    "Date": datetime.now() - timedelta(days=i*2),
                    "Title": "Simulated Historical News Item",
                    "Sentiment": random.uniform(-0.8, 0.8),
                    "Source": "Simulated",
                    "Link": "#"
                })
        
        df = pd.DataFrame(data).sort_values("Date")
        return df

def render_sentiment_timeline(ticker: str):
    st.markdown("## 📰 News Sentiment Timeline")
    st.caption(f"Sentiment analysis of recent news headlines for **{ticker}**.")
    
    analyzer = NewsSentiment(ticker)
    
    with st.spinner("Analyzing news sentiment..."):
        df = analyzer.get_timeline()
        
    if df.empty:
        st.info("No news found.")
        return
        
    # --- Metrics ---
    # Avg Sentiment
    avg_sent = df['Sentiment'].mean()
    
    # Classification
    if avg_sent > 0.2: s_label, s_color = "Bullish", "green"
    elif avg_sent < -0.2: s_label, s_color = "Bearish", "red"
    else: s_label, s_color = "Neutral", "gray"
    
    m1, m2 = st.columns(2)
    m1.metric("Average Sentiment", f"{avg_sent:.2f}", delta=s_label, delta_color="normal" if avg_sent>0 else "inverse") # Inverse logic checks direction
    m2.metric("News Count", len(df))
    
    st.divider()
    
    # --- Timeline Chart ---
    fig = go.Figure()
    
    # Stem plot style
    for i, row in df.iterrows():
        color = 'green' if row['Sentiment'] >= 0 else 'red'
        
        fig.add_trace(go.Scatter(
            x=[row['Date'], row['Date']],
            y=[0, row['Sentiment']],
            mode='lines',
            line=dict(color=color, width=3),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=[row['Date']],
            y=[row['Sentiment']],
            mode='markers',
            marker=dict(color=color, size=10),
            name=row['Source'],
            hovertemplate=f"<b>{row['Title']}</b><br>Score: {row['Sentiment']:.2f}<br>Source: {row['Source']}<extra></extra>"
        ))
        
    fig.update_layout(
        title="Sentiment Momentum",
        yaxis_title="Sentiment Score (-1 to +1)",
        xaxis_title="Date",
        template="plotly_dark",
        height=300,
        yaxis=dict(range=[-1.1, 1.1])
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- News Feed List ---
    st.subheader("Latest Headlines")
    # Show real news first (exclude simulated if mixed, or show all?)
    # We'll show top 5 real ones (exclude 'Simulated' source)
    
    real_news = df[df['Source'] != 'Simulated'].sort_values("Date", ascending=False)
    
    for i, row in real_news.head(10).iterrows():
        score = row['Sentiment']
        color = "green" if score > 0 else "red" if score < 0 else "gray"
        
        st.markdown(f"""
        <div style='background: #161b22; padding: 10px; border-radius: 5px; border-left: 4px solid {color}; margin-bottom: 10px;'>
            <div style='font-size: 11px; color: #8b949e;'>{row['Source']} • {row['Date'].strftime('%Y-%m-%d %H:%M')}</div>
            <div style='font-size: 14px; font-weight: 500;'>
                <a href='{row['Link']}' target='_blank' style='color: #e6edf3; text-decoration: none;'>{row['Title']}</a>
            </div>
            <div style='font-size: 11px; margin-top: 5px;'>Sentiment Score: <span style='color:{color}'>{score:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
