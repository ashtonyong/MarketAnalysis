# 📊 Volume Profile Trading Tool
**Professional-grade Volume Profile analysis with AI Agent integration**

Built for traders who want powerful orderflow analysis for FREE, with the ability to upgrade to real-time data later.

---

## 🎯 What This Tool Does

- **Volume Profile Analysis**: Calculate POC, VAH, VAL from price data
- **Advanced Analytics**: **NEW!** Profile Comparison, Migration Tracking, and POC Zones
- **Order Flow**: **NEW!** Time & Sales with Large Print Detection
- **Visual Dashboard**: Professional charts and visualizations
- **CLI Interface**: Quick command-line analysis
- **AI Agent Ready**: Designed to work with Antigravity and other AI agents

[📘 **Read the User Guide for New Features**](USER_GUIDE.md)

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Run Your First Analysis

**CLI Mode:**
```bash
# Full analysis
python volume_profile_cli.py analyze SPY

# Quick check
python volume_profile_cli.py quick AAPL

# Compare stocks
python volume_profile_cli.py compare AAPL MSFT GOOGL TSLA

# Export key levels
python volume_profile_cli.py levels NVDA

# Export to CSV
python volume_profile_cli.py export AAPL
```

**Visual Mode:**
```bash
# Create visual dashboard
python volume_profile_visualizer.py SPY
```

**Python Code:**
```python
from volume_profile_engine import VolumeProfileEngine

# Analyze a ticker
engine = VolumeProfileEngine("AAPL", period="1mo", interval="15m")
# Note: get_summary() is a placeholder for engine summary logic if implemented
# print(engine.get_summary()) 
```

---

## 🤖 AI Agent Integration (Antigravity)

This tool is designed to work seamlessly with AI agents like **Antigravity**. Here's how:

### Method 1: Direct Python Integration

```python
from ai_agent_interface import VolumeProfileAgent

# Have Antigravity call these functions:

# 1. Full analysis
result = VolumeProfileAgent.analyze("AAPL", period="1mo")
print(result)

# 2. Get trading plan
plan = VolumeProfileAgent.get_trading_plan("SPY")
print(plan)

# 3. Compare multiple stocks
comparison = VolumeProfileAgent.compare_tickers(["AAPL", "MSFT", "GOOGL"])
print(comparison)

# 4. Generate alerts
alerts = VolumeProfileAgent.get_alerts("TSLA")
print(alerts)

# 5. Create chart
chart = VolumeProfileAgent.create_chart("NVDA", output_path="nvda_chart.png")
print(chart)

# 6. Export Data
csv_result = VolumeProfileAgent.export_csv("SPY")
print(csv_result)
```

### Method 2: JSON API Style

```python
from ai_agent_interface import ai_analyze, ai_get_plan, ai_compare

# Returns JSON strings for easy parsing
# Note: Ensure these wrapper functions exist in ai_agent_interface.py
# analysis_json = ai_analyze("AAPL")
```

### Method 3: CLI Integration

Antigravity can call the CLI directly:

```bash
# Antigravity executes:
python volume_profile_cli.py analyze AAPL --period 1mo --interval 15m
python volume_profile_cli.py quick SPY
python volume_profile_cli.py compare AAPL MSFT GOOGL
```

---

## 📖 How Antigravity Can Use This Tool

### Scenario 1: User asks "Analyze AAPL for me"

**Antigravity workflow:**
```python
from ai_agent_interface import VolumeProfileAgent

# Step 1: Get analysis
result = VolumeProfileAgent.analyze("AAPL", period="1mo")

# Step 2: Get trading plan
plan = VolumeProfileAgent.get_trading_plan(result)

# Step 3: Create visual chart
# chart = VolumeProfileAgent.create_chart("AAPL", output_path="/home/claude/aapl_chart.png")

# Step 4: Return results to user
print(f"Analysis complete! Current price: ${result['current_price']}")
print(f"Trading Signal: {plan['bias']}")
print(f"Action: {plan['strategy']}")
```

### Scenario 2: User asks "Which stocks have the best setup today?"

**Antigravity workflow:**
```python
# Compare multiple stocks
watchlist = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMD"]
comparison = VolumeProfileAgent.compare_tickers(watchlist, period="5d")

# Get the best opportunity
# best = comparison['best_opportunity'] # Logic to filter best
# print(f"Best setup: {best['ticker']}")
```

---

## 📚 Available Functions

### Core Engine Functions

```python
from volume_profile_engine import VolumeProfileEngine

engine = VolumeProfileEngine()

# Fetch market data
df = engine.fetch_data("SPY", period="1mo", interval="15m")

# Calculate volume profile
profile = engine.calculate_volume_profile(df)

# Get key levels
poc = engine.find_poc(profile)  # Point of Control
val, vah = engine.find_value_area(profile, profile['Volume'].sum())  # Value Area

# Detect Shape
shape = engine.detect_profile_shape(profile)

# Export
engine.export_to_csv(profile, "spy_profile.csv")
```

### AI Agent Functions

```python
from ai_agent_interface import VolumeProfileAgent

agent = VolumeProfileAgent()

# Full analysis with trading signals
agent.analyze(ticker, period, interval)

# Get actionable trading plan
agent.get_trading_plan(analysis_result)

# Compare multiple tickers
agent.compare_tickers([ticker1, ticker2, ...], period)

# Detect Composite Profile
agent.analyze_composite(ticker, days=5)

# Export CSV
agent.export_csv(ticker)
```

---

## 📊 Data Sources

### Current (FREE):
- **Yahoo Finance** via yfinance library
- Historical data for stocks and ETFs
- 15-minute delayed data

### Future Upgrades (PAID):
- Real-time data feeds
- Forex and futures (XAU/USD, GC)
- Level 2 order book data
- Options flow

---

## 💰 Monetization Path

**Phase 1 (Current - FREE):**
- Build with free historical data
- Perfect the algorithms
- Build user base

**Phase 2 (Add Real-time Data):**
- Integrate paid data feeds ($50-100/month)
- Real-time alerts
- Live scanning

**Phase 3 (SaaS Platform):**
- Subscription service ($30-50/month)
- Web dashboard
- Mobile alerts
- Multi-asset support

---

## 🛠️ Technical Details

### File Structure
```
volume-profile-tool/
├── volume_profile_engine.py      # Core calculations
├── volume_profile_cli.py         # Command-line interface
├── volume_profile_visualizer.py  # Visual dashboard (Todo)
├── ai_agent_interface.py         # AI agent integration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Key Parameters

**period:** Time range for analysis
- `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

**interval:** Bar size
- Intraday: `1m`, `2m`, `5m`, `15m`, `30m`, `1h`
- Daily: `1d`, `5d`, `1wk`, `1mo`, `3mo`

**num_bins:** Number of price levels (default: 50)
- More bins = higher resolution
- Fewer bins = smoother profile

---

## 🎓 Volume Profile Concepts

**POC (Point of Control):**
- Price level with highest volume
- Acts as strong support/resistance
- Traders often return to POC

**VAH (Value Area High):**
- Upper boundary of 70% volume
- Resistance level
- Breakout above VAH = bullish

**VAL (Value Area Low):**
- Lower boundary of 70% volume
- Support level
- Breakdown below VAL = bearish

**Trading Strategies:**
1. **Mean Reversion**: Trade back to POC from extremes
2. **Breakout**: Trade breaks above VAH or below VAL
3. **Value Area Rejection**: Fade moves outside value area

---

## 🚀 Next Features to Build

### Phase 1 (Free):
- ✅ Volume Profile calculation
- ✅ POC, VAH, VAL identification
- ✅ Visual dashboard (Coming soon)
- ✅ CLI interface
- ✅ AI agent integration
- [ ] Multi-timeframe analysis
- [ ] Historical backtesting
- [ ] Pattern recognition

### Phase 2 (Paid):
- [ ] Real-time data integration
- [ ] Live alerts and notifications
- [ ] Options flow integration
- [ ] Smart Money Concepts overlay
- [ ] Order book visualization
- [ ] Composite volume profiles (Implemented basic version)

---

## 🤝 Integration with Other Tools

This tool is designed to work with:
- **Antigravity**: AI agent for automated analysis
- **TradingView**: Export levels for charting
- **Discord/Telegram**: Automated alerts
- **Trading platforms**: Export signals
- **Spreadsheets**: Data export

---

## 💡 Tips for Best Results

1. **Use appropriate timeframes**:
   - Day trading: 1d period, 5m-15m interval
   - Swing trading: 1mo-3mo period, 1h-1d interval
   - Position trading: 1y period, 1d interval

2. **Combine with other indicators**:
   - Volume Profile + RSI
   - Volume Profile + Moving Averages
   - Volume Profile + Support/Resistance

3. **Multiple timeframes**:
   - Check daily, weekly, and monthly profiles
   - Look for confluence of key levels

4. **Real-time monitoring**:
   - Watch how price interacts with levels
   - POC acts as magnet for price
   - VAH/VAL often see reversals

---

## 🎯 Quick Reference

```python
# Most common use cases:

# 1. Quick analysis
from ai_agent_interface import VolumeProfileAgent
agent = VolumeProfileAgent()
result = agent.analyze("AAPL")

# 2. Get trading plan
plan = agent.get_trading_plan(result)

# 3. Compare stocks
comparison = agent.compare_tickers(["AAPL", "MSFT", "GOOGL"])

# 4. Export CSV
agent.export_csv("TSLA")

# 5. CLI usage
# python volume_profile_cli.py analyze AAPL
# python volume_profile_cli.py quick SPY
# python volume_profile_cli.py compare AAPL MSFT GOOGL
# python volume_profile_cli.py export AAPL
```

---

**Built with ❤️ for the trading community**

Happy Trading! 📈
