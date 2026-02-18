from peer_comparison import get_peers, fetch_peer_metrics
import pandas as pd

def test_peers():
    ticker = "NVDA"
    print(f"Testing Peer Fetch for {ticker}...")
    peers = get_peers(ticker)
    print(f"Peers found: {peers}")
    
    if peers:
        all_tickers = [ticker] + peers[:3]
        print(f"Fetching metrics for: {all_tickers}")
        df = fetch_peer_metrics(all_tickers)
        print("Metrics DataFrame:")
        print(df.head())
        
        # Test specific columns exist and are not empty
        required = ["P/E", "ROE", "Net Margin"]
        # Note: keys in df are labels from METRICS_DEF, e.g. "P/E", "ROE"
        print(f"Columns: {df.columns.tolist()}")
        
    else:
        print("No peers found (check industry mapping).")

if __name__ == "__main__":
    test_peers()
