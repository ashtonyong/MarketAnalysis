from garch_forecaster import GarchForecaster
import pandas as pd

def test_garch():
    print("Testing GARCH Forecaster...")
    ticker = "SPY"
    
    gf = GarchForecaster(ticker)
    print(f"Forecasting volatility for {ticker}...")
    
    res = gf.forecast_vol()
    
    if res:
        print("\nForecast Results:")
        print(f"Method: {res['method']}")
        print(f"Current Vol (Ann): {res['current_vol']:.2f}%")
        
        print("\nConditional Vol (Last 5 days):")
        print(res['conditional_vol'].tail())
    else:
        print("Forecast failed.")

if __name__ == "__main__":
    test_garch()
