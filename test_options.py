from options_analytics import OptionsAnalytics
import pandas as pd

def test_options():
    print("Testing Options Analytics...")
    ticker = "SPY"
    
    oa = OptionsAnalytics(ticker)
    print(f"Fetching expirations for {ticker}...")
    
    exps = oa.get_expirations()
    
    if exps:
        print(f"Expirations found: {len(exps)}")
        first_exp = exps[0]
        print(f"Fetching chain for {first_exp}...")
        
        calls, puts = oa.get_chain(first_exp)
        
        if not calls.empty and not puts.empty:
            print(f"Calls: {len(calls)}, Puts: {len(puts)}")
            
            max_pain = oa.calculate_max_pain(calls, puts)
            print(f"Max Pain Strike: {max_pain}")
            
            print("\nSample Calls:")
            print(calls[['strike', 'lastPrice', 'openInterest', 'volume']].head())
        else:
            print("Failed to fetch chain data.")
    else:
        print("No expirations found.")

if __name__ == "__main__":
    test_options()
