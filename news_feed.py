"""
News Feed & Sentiment Analyzer
Fetches news from Google News RSS feed (100% FREE, no API key).
Scores sentiment using keyword analysis.
"""

import requests
import xml.etree.ElementTree as ET
import re
from typing import List, Dict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


# Sentiment word lists
POSITIVE_WORDS = {
    'surge', 'surges', 'rally', 'rallies', 'gain', 'gains', 'rise', 'rises',
    'jump', 'jumps', 'soar', 'soars', 'bullish', 'upgrade', 'upgrades',
    'beat', 'beats', 'strong', 'growth', 'profit', 'profits', 'record',
    'high', 'boost', 'boosts', 'positive', 'optimism', 'outperform',
    'buy', 'breakout', 'momentum', 'recovery', 'upward', 'advance',
    'higher', 'top', 'best', 'up', 'climbs', 'above', 'exceeded',
}

NEGATIVE_WORDS = {
    'crash', 'crashes', 'fall', 'falls', 'drop', 'drops', 'plunge', 'plunges',
    'decline', 'declines', 'loss', 'losses', 'bearish', 'downgrade', 'downgrades',
    'miss', 'misses', 'weak', 'recession', 'risk', 'risks', 'fear', 'fears',
    'sell', 'selloff', 'warning', 'concern', 'concerns', 'slump', 'tumble',
    'negative', 'cut', 'cuts', 'layoff', 'layoffs', 'bankruptcy', 'default',
    'lower', 'worst', 'down', 'below', 'plummets', 'sinks', 'collapses',
}

# Map tickers to search-friendly names for better Google News results
TICKER_NAMES = {
    'SPY': 'SPY S&P 500 ETF',
    'QQQ': 'QQQ Nasdaq ETF',
    'AAPL': 'Apple AAPL stock',
    'MSFT': 'Microsoft MSFT stock',
    'GOOGL': 'Google GOOGL stock',
    'AMZN': 'Amazon AMZN stock',
    'NVDA': 'Nvidia NVDA stock',
    'TSLA': 'Tesla TSLA stock',
    'META': 'Meta META stock',
    'GC=F': 'gold price',
    'SI=F': 'silver price',
    'CL=F': 'crude oil price',
    'BTC-USD': 'Bitcoin BTC crypto',
    'ETH-USD': 'Ethereum ETH crypto',
    'ES=F': 'S&P 500 futures',
    'NQ=F': 'Nasdaq futures',
    'EURUSD=X': 'EUR USD forex',
    'DX-Y.NYB': 'US Dollar index DXY',
    'TLT': 'Treasury bonds TLT',
}


class NewsFeedAnalyzer:
    """Fetch and analyze news sentiment using Google News RSS."""

    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.search_query = TICKER_NAMES.get(ticker, f"{ticker} stock")

    def get_news(self, max_items: int = 15) -> List[Dict]:
        """Fetch news from Google News RSS."""
        url = self.GOOGLE_NEWS_RSS.format(query=requests.utils.quote(self.search_query))

        try:
            resp = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            resp.raise_for_status()
        except Exception as e:
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            return []

        articles = []
        items = root.findall('.//item')

        for item in items[:max_items]:
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            pub_date = item.findtext('pubDate', '')
            source = item.findtext('source', '')

            # Parse date
            time_str = ''
            age = ''
            try:
                dt = parsedate_to_datetime(pub_date)
                time_str = dt.strftime('%Y-%m-%d %H:%M')
                age = self._time_ago(dt)
            except Exception:
                time_str = pub_date
                age = ''

            # Extract publisher from title (Google News format: "Title - Publisher")
            publisher = source
            if not publisher and ' - ' in title:
                parts = title.rsplit(' - ', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    publisher = parts[1].strip()

            # Score sentiment
            sentiment, score = self._score_sentiment(title)

            articles.append({
                'title': title,
                'publisher': publisher or 'Unknown',
                'link': link,
                'time': time_str,
                'age': age,
                'sentiment': sentiment,
                'score': score,
            })

        return articles

    def get_sentiment_summary(self) -> Dict:
        """Get overall sentiment summary."""
        articles = self.get_news()
        if not articles:
            return {
                'articles': [],
                'overall_sentiment': 'NO DATA',
                'avg_score': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
            }

        scores = [a['score'] for a in articles]
        avg = sum(scores) / len(scores) if scores else 0

        pos = sum(1 for s in scores if s > 0)
        neg = sum(1 for s in scores if s < 0)
        neu = sum(1 for s in scores if s == 0)

        if avg > 0.15:
            overall = 'BULLISH'
        elif avg < -0.15:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'

        return {
            'articles': articles,
            'overall_sentiment': overall,
            'avg_score': round(avg, 3),
            'positive_count': pos,
            'negative_count': neg,
            'neutral_count': neu,
        }

    def _score_sentiment(self, text: str):
        """Score text sentiment using keyword matching."""
        words = set(re.findall(r'\w+', text.lower()))
        pos_matches = words & POSITIVE_WORDS
        neg_matches = words & NEGATIVE_WORDS

        pos_count = len(pos_matches)
        neg_count = len(neg_matches)
        total = pos_count + neg_count

        if total == 0:
            return 'Neutral', 0

        score = (pos_count - neg_count) / total
        if score > 0:
            return 'Positive', round(score, 2)
        elif score < 0:
            return 'Negative', round(score, 2)
        return 'Neutral', 0

    def _time_ago(self, dt: datetime) -> str:
        """Convert datetime to 'X ago' string."""
        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        diff = now - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{max(1, int(diff.total_seconds() / 60))}m ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        else:
            return f"{int(hours / 24)}d ago"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    nf = NewsFeedAnalyzer('SPY')
    result = nf.get_sentiment_summary()
    print(f"Overall: {result['overall_sentiment']} (score: {result['avg_score']})")
    print(f"Positive: {result['positive_count']} | Negative: {result['negative_count']} | Neutral: {result['neutral_count']}")
    print()
    for a in result['articles'][:10]:
        print(f"  [{a['sentiment']:>8}] {a['title']}")
        print(f"            {a['publisher']} - {a['age']}")
        print()
