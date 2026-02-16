"""
News Feed & Sentiment Analyzer
Fetches news from yfinance and scores sentiment using keyword analysis.
100% FREE - no API keys needed.
"""

import yfinance as yf
from typing import List, Dict
from datetime import datetime
import re


# Sentiment word lists
POSITIVE_WORDS = {
    'surge', 'surges', 'rally', 'rallies', 'gain', 'gains', 'rise', 'rises',
    'jump', 'jumps', 'soar', 'soars', 'bullish', 'upgrade', 'upgrades',
    'beat', 'beats', 'strong', 'growth', 'profit', 'profits', 'record',
    'high', 'boost', 'boosts', 'positive', 'optimism', 'outperform',
    'buy', 'breakout', 'momentum', 'recovery', 'upward', 'advance',
}

NEGATIVE_WORDS = {
    'crash', 'crashes', 'fall', 'falls', 'drop', 'drops', 'plunge', 'plunges',
    'decline', 'declines', 'loss', 'losses', 'bearish', 'downgrade', 'downgrades',
    'miss', 'misses', 'weak', 'recession', 'risk', 'risks', 'fear', 'fears',
    'sell', 'selloff', 'warning', 'concern', 'concerns', 'slump', 'tumble',
    'negative', 'cut', 'cuts', 'layoff', 'layoffs', 'bankruptcy', 'default',
}


class NewsFeedAnalyzer:
    """Fetch and analyze news sentiment for a ticker."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    def get_news(self, max_items: int = 20) -> List[Dict]:
        """Fetch news from yfinance."""
        try:
            stock = yf.Ticker(self.ticker)
            raw_news = stock.news or []
        except Exception:
            return []

        articles = []
        for item in raw_news[:max_items]:
            title = item.get('title', '')
            publisher = item.get('publisher', 'Unknown')
            link = item.get('link', '')
            pub_time = item.get('providerPublishTime', 0)

            # Format timestamp
            try:
                dt = datetime.fromtimestamp(pub_time)
                time_str = dt.strftime('%Y-%m-%d %H:%M')
                age = self._time_ago(dt)
            except Exception:
                time_str = 'Unknown'
                age = ''

            # Score sentiment
            sentiment, score = self._score_sentiment(title)

            articles.append({
                'title': title,
                'publisher': publisher,
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
        diff = datetime.now() - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)}m ago"
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
    for a in result['articles'][:5]:
        print(f"  [{a['sentiment']}] {a['title']}")
