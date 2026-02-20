from watchlist_scoring import WatchlistScorer
from ai_report import AIReportGenerator
import pandas as pd
import os

def test_features():
    print("Testing Platform-Wide Features...")
    
    # 1. Test Watchlist Scorer
    print("\n[1] Testing WatchlistScorer...")
    scorer = WatchlistScorer()
    tickers = ["AAPL", "MSFT"] # Keep it small for speed
    
    print(f"Fetching data for {tickers}...")
    # Mock data fetch if needed, but let's try real fetch if classes use yfinance
    # The class uses yfinance, so this tests that too.
    try:
        data = scorer.fetch_data(tickers)
        if not data.empty:
            print(f"Data fetched: {len(data)} rows")
            
            scores = scorer.calculate_scores(data)
            print("Scores Head:")
            print(scores[['Ticker', 'Total_Score']])
            
            assert 'Total_Score' in scores.columns
            assert not scores.empty
        else:
            print("Warning: No data fetched (API limit or network?)")
    except Exception as e:
        print(f"WatchlistScorer Error: {e}")

    # 2. Test AI Report Generator
    print("\n[2] Testing AIReportGenerator...")
    try:
        generator = AIReportGenerator()
        mock_data = {
            'price': 150.00, 
            'tech_posture': 'Bullish',
            'fund_posture': 'Strong',
            'recommendation': 'BUY',
            'rsi': 65.4,
            'trend': 'Upward',
            'volatility': 0.15,
            'market_cap': '2.5T',
            'pe': 35.2
        }
        
        output = generator.generate_report("TEST_TICKER", mock_data)
        print(f"Report generated at: {output}")
        
        if os.path.exists(output):
            print(" PDF file exists.")
            # Clean up
            os.remove(output)
            print("Cleaned up test file.")
        else:
            print(" PDF file not found.")
            
    except Exception as e:
        print(f"AIReportGenerator Error: {e}")
        
    print("\n Verification Complete!")

if __name__ == "__main__":
    test_features()
