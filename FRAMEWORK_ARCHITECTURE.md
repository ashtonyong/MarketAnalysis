# VOLUME PROFILE / MARKET PROFILE FRAMEWORK
## Architecture Document for Antigravity Coding Agent

---

## 🏗️ CORE FRAMEWORK ARCHITECTURE

### 1. DATA LAYER
**Purpose:** Fetch and normalize market data

```
DataFetcher
├── fetch_historical_data(ticker, period, interval)
├── fetch_realtime_data(ticker)  [Future: paid feeds]
├── normalize_data() 
└── validate_data()
```

### 2. CALCULATION ENGINE
**Purpose:** Core Volume Profile calculations

```
VolumeProfileCalculator
├── calculate_volume_distribution(data, num_bins)
│   └── Distribute volume across price levels
├── find_poc(volume_profile)
│   └── Price level with highest volume
├── find_value_area(volume_profile, percentage=0.70)
│   └── Expand from POC until 70% volume captured
├── calculate_composite_profile(multiple_sessions)
│   └── Combine multiple days/sessions
└── calculate_tpo_profile(time_price_opportunities)
    └── Market Profile TPO calculation
```

### 3. ANALYSIS LAYER
**Purpose:** Interpret the data and generate signals

```
ProfileAnalyzer
├── detect_position(current_price, vah, val, poc)
├── generate_signals(position, metrics)
│   ├── mean_reversion_signal()
│   ├── breakout_signal()
│   └── rejection_signal()
├── calculate_opportunity_score(metrics)
├── identify_patterns()
│   ├── poor_high/low
│   ├── single_prints
│   ├── excess
│   └── balance_area
└── compare_profiles(current_profile, historical_profiles)
```

### 4. VISUALIZATION LAYER
**Purpose:** Create charts and visual representations

```
ProfileVisualizer
├── plot_volume_profile(data, profile)
├── plot_market_profile_tpo(tpo_data)
├── plot_composite_profile(multiple_days)
├── create_dashboard(all_metrics)
└── export_chart(format='png|pdf|html')
```

### 5. TRADING LOGIC LAYER
**Purpose:** Generate actionable trading plans

```
TradingPlanner
├── generate_entry_zones(bias, vah, val, poc)
├── calculate_stop_loss(position, volatility)
├── calculate_targets(entry, profile_range)
├── size_position(risk_amount, stop_distance)
└── generate_trading_plan(analysis_results)
```

### 6. ALERT SYSTEM
**Purpose:** Monitor and notify on key events

```
AlertManager
├── set_price_alert(ticker, level, condition)
├── monitor_profile_changes()
├── detect_profile_breaks()
├── send_notification(method='email|sms|discord|telegram')
└── manage_alert_queue()
```

---

## 🎯 KEY CONCEPTS

### Volume Profile Concepts

**1. Volume Distribution**
- Distribute volume across price levels touched by each OHLC bar.

**2. Point of Control (POC)**
- Price level with highest volume. Strong support/resistance.

**3. Value Area (VA)**
- Range containing 70% of volume (VAH/VAL).

**4. Profile Types**
- **Single Day Profile**: One trading session.
- **Composite Profile**: Multiple days combined.
- **tpo Profile**: Time-based (Market Profile).

### Market Profile Concepts

**1. TPO (Time Price Opportunity)**
- 30-minute periods assigned letters (A, B, C...).
- Shows where *time* was spent.

**2. Profile Shapes**
- **P-Shape**: Trending up (Short covering).
- **b-Shape**: Trending down (Long liquidation).
- **D-Shape**: Double distribution (Trend + Balance).
- **Normal**: Bell curve (Balance).

**3. Key Patterns**
- **Poor High/Low**: Thin tails, likely to revisit.
- **Excess**: Rejection, strong S/R.
- **Single Prints**: Gaps, fast movement.

---

## 📐 MATHEMATICAL FOUNDATIONS

### Value Area Calculation
```
1. Find POC (max volume price)
2. Start with POC volume
3. Look at adjacent levels (above and below POC)
4. Add the level with more volume
5. Repeat until cumulative volume >= 70% of total
```

### Profile Shape Classification
- **Normal**: Symmetric, tapering extremes.
- **P-Shape**: Volume heavy at top, thin tail bottom.
- **b-Shape**: Volume heavy at bottom, thin tail top.

---

## 🤖 AI AGENT INTERFACE DESIGN

### Request/Response Format
```json
{
    "status": "success",
    "ticker": "AAPL",
    "current_price": 175.23,
    "profile": {
        "poc": 174.50,
        "vah": 176.80,
        "val": 172.20,
        "value_area_volume_pct": 70.5
    },
    "signals": {
        "bias": "BULLISH",
        "entry_zone": [174.50, 176.80]
    },
    "pattern": "P_SHAPE_TRENDING"
}
```
