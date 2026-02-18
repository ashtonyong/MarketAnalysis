from pairs_trading import PairsTrader
import pandas as pd

def test_pairs():
    print("Testing Pairs Trader...")
    t1 = "SPY"
    t2 = "QQQ"
    
    pt = PairsTrader(t1, t2)
    print(f"Analyzing {t1} vs {t2}...")
    
    data = pt.fetch_data()
    
    if not data.empty:
        res = pt.calculate_metrics(data)
        
        if res:
            print("\nAnalysis Results:")
            print(f"Correlation: {res['correlation']:.2f}")
            print(f"Hedge Ratio: {res['hedge_ratio']:.3f}")
            print(f"R-Squared: {res['r_squared']:.3f}")
            print(f"Current Spread Z-Score: {res['z_score'].iloc[-1]:.2f}")
            
            print("\nSpread Data (Last 5):")
            print(res['spread'].tail())
    else:
        print("No data fetched.")

if __name__ == "__main__":
    test_pairs()
