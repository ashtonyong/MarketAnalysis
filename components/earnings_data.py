import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Curated list of ~100 liquid/popular stocks to simulate "Market" coverage
MARKET_TICKERS = [
    # Mag 7 / Big Tech
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX',
    # Semis
    'AMD', 'INTC', 'QCOM', 'MU', 'AVGO', 'TSM', 'ARM', 'SMCI',
    # Major Financials
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'V', 'MA', 'AXP',
    # Retail / Consumer
    'WMT', 'TGT', 'COST', 'HD', 'LOW', 'MCD', 'SBUX', 'NKE', 'DIS', 'KO', 'PEP',
    # Auto
    'F', 'GM', 'RIVN', 'LCID',
    # Tech / Growth / SaaS
    'CRM', 'ADBE', 'ORCL', 'IBM', 'CSCO', 'PLTR', 'SNOW', 'DDOG', 'SHOP', 'SQ', 'PYPL', 'UBER', 'ABNB',
    # Industrial / Energy
    'CAT', 'DE', 'BA', 'GE', 'XOM', 'CVX', 'COP', 'OXY',
    # Pharma
    'LLY', 'JNJ', 'PFE', 'MRK', 'ABBV', 'BIIB',
    # Meme / Retail Favorites
    'GME', 'AMC', 'COIN', 'HOOD', 'ROKU', 'DKNG', 'SOFI', 'MARA', 'RIOT', 'CLSK',
    # ETFs (sometimes have distributions marked as earnings, good to exclude usually, but kept for main ones)
    # Actually mainly stocks have earnings calls.
]

class EarningsData:
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_upcoming_earnings(days_ahead=30):
        """
        Fetches upcoming earnings for a broad market list.
        Returns a DataFrame sorted by date.
        """
        data = []
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        
        # Add user watchlist if available
        watchlist = st.session_state.get('watchlist', [])
        # Combine unique
        all_tickers = list(set(MARKET_TICKERS + watchlist))
        
        for ticker in all_tickers:
            try:
                t = yf.Ticker(ticker)
                cal = t.calendar
                
                if cal is not None and not cal.empty:
                    # 1. Normalize Earnings Date
                    ern_dates = cal.get('Earnings Date')
                    if ern_dates is None:
                        ern_dates = cal.iloc[0] if not cal.empty else None
                    
                    next_date = None
                    if isinstance(ern_dates, list): next_date = ern_dates[0]
                    elif hasattr(ern_dates, 'values'): next_date = ern_dates.values[0]
                    else: next_date = ern_dates
                    
                    if next_date:
                        nd = pd.to_datetime(next_date)
                        
                        # Filter: Upcoming only (or today)
                        if today.date() <= nd.date() <= end_date.date():
                            
                            # 2. Get Estimates
                            est = cal.get('Earnings Average')
                            if est is None: 
                                est = cal.get('EPS Estimate', [None])[0] if 'EPS Estimate' in cal else None
                            
                            # 3. Get Company Name (fast_info or info)
                            # info is slow, let's try to map or skip for speed. 
                            # We can try t.fast_info for some data but names aren't in fast_info usually.
                            # We'll stick to Ticker for now or implement a lazy name fetcher if really needed.
                            # For now, Ticker is sufficient for "Symbol", we can try to get short name if cached.
                            
                            data.append({
                                'Symbol': ticker,
                                'Date': nd,
                                'DateStr': nd.strftime('%b %d'), # "Feb 18"
                                'Day': nd.strftime('%d'), # "18"
                                'Month': nd.strftime('%b').upper(), # "FEB"
                                'EPS Est': f"{est:.2f}" if isinstance(est, (int, float)) else "N/A",
                                'Time': "N/A" # yfinance doesn't consistently give BMO/AMC in basic calendar
                            })
            except Exception:
                continue
                
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df = df.sort_values('Date')
        return df

    @staticmethod
    def get_company_name(ticker):
        """Helper to try getting a name - simplified."""
        # This could be expanded with a static mapping for speed
        return ticker # Placeholder for speed, or we can add a mapping dict later
