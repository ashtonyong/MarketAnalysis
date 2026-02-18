from valuation_history import ValuationHistory
import pandas as pd

def test_valuation():
    print("Testing Valuation History...")
    ticker = "MSFT"
    
    vh = ValuationHistory(ticker)
    print(f"Fetching valuation history for {ticker}...")
    
    df = vh.fetch_data()
    
    if not df.empty:
        print("\nValuation Results (Last 5 days):")
        print(df[['Close', 'EPS_TTM', 'PE_Ratio']].tail())
        
        print("\nSummary Stats:")
        print(f"Current P/E: {df['PE_Ratio'].iloc[-1]:.2f}")
        print(f"Min P/E (5Y): {df['PE_Ratio'].min():.2f}")
        print(f"Max P/E (5Y): {df['PE_Ratio'].max():.2f}")
        print(f"Avg P/E (5Y): {df['PE_Ratio'].mean():.2f}")
    else:
        print("No valuation data found.")

if __name__ == "__main__":
    test_valuation()
