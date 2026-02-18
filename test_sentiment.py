from sentiment_timeline import NewsSentiment
import pandas as pd

def test_sentiment():
    print("Testing Sentiment Analyzer...")
    ticker = "AAPL"
    
    analyzer = NewsSentiment(ticker)
    print(f"Fetching news for {ticker}...")
    
    df = analyzer.get_timeline()
    
    if not df.empty:
        print("\nSentiment Results:")
        print(df[["Date", "Title", "Sentiment", "Source"]].head())
        print(f"\nTotal Articles: {len(df)}")
        print(f"Average Sentiment: {df['Sentiment'].mean():.2f}")
    else:
        print("No news found.")

if __name__ == "__main__":
    test_sentiment()
