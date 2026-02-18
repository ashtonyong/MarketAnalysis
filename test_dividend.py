from dividend_tracker import fetch_dividend_data, calc_safety_score
import pandas as pd

def test_aapl():
    print("Testing AAPL...")
    data = fetch_dividend_data("AAPL")
    if "error" in data:
        print(f"Error: {data['error']}")
    else:
        # data['yield'] is now the processed one.
        # We can't see raw from here unless we modify fetch_dividend_data to return it or print it.
        # Let's just trust the processed one for now, or use yf directly here to check.
        import yfinance as yf
        t = yf.Ticker("AAPL")
        print(f"RAW YIELD FROM YF: {t.info.get('dividendYield')}")
        print(f"Processed Yield: {data.get('yield')}")
        print(f"Payout: {data.get('annual_dividend')}")
        print(f"Safety Score Inputs: Payout={data.get('payout_ratio')}, Debt={data.get('debt_to_equity')}, FCF={data.get('fcf')}, Growth={data.get('revenue_growth')}")
        score = calc_safety_score(data.get('payout_ratio'), data.get('debt_to_equity'), data.get('fcf'), data.get('revenue_growth'))
        print(f"Calculated Safety Score: {score}")
        print(f"Dividend History Length: {len(data.get('history')) if data.get('history') is not None else 0}")

def test_brk_b():
    print("\nTesting BRK-B (No Div)...")
    data = fetch_dividend_data("BRK-B")
    print(f"Yield: {data.get('yield')}")
    print(f"History Empty? {data.get('history').empty if data.get('history') is not None else 'None'}")

if __name__ == "__main__":
    test_aapl()
    test_brk_b()
