import sys
import os

print("Verifying Feature Imports...")

modules = [
    "session_range",
    "mtf_confluence",
    "rolling_beta",
    "earnings_volatility",
    "short_interest",
    "fvg_scanner",
    "market_structure",
    "dcf_engine",
    "fundamental_screener",
    "portfolio_risk",
    "regime_backtest",
    "garch_forecaster",
    "insider_tracker",
    "liquidity_heatmap",
    "vol_surface",
    "factor_model",
    "components.earnings_data"
]

failed = []

for m in modules:
    try:
        __import__(m)
        print(f"[OK] Imported {m}")
    except ImportError as e:
        print(f"[FAIL] Failed to import {m}: {e}")
        failed.append(m)
    except Exception as e:
        print(f"[FAIL] Error in {m}: {e}")
        failed.append(m)

print("-" * 30)
if failed:
    print(f"Failed modules: {failed}")
    sys.exit(1)
else:
    print("All feature modules imported successfully!")
    sys.exit(0)
