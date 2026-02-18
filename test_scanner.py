from setup_scanner import SetupScanner
import pandas as pd

def test_scanner():
    print("Testing Setup Scanner...")
    tickers = ["SPY", "NVDA", "AAPL"]
    
    scanner = SetupScanner(tickers)
    print(f"Scanning: {tickers}")
    
    # scan() usually expects a Streamlit progress bar, but handles None
    results = scanner.scan(progress_bar=None)
    
    if not results.empty:
        print("\nScan Results:")
        print(results[["Ticker", "Score", "Grade", "Action", "Price", "Regime", "Position", "Z-Score"]])
    else:
        print("No results returned.")

if __name__ == "__main__":
    test_scanner()
