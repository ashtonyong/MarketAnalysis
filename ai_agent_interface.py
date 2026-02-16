"""
AI Agent Integration Interface
Designed for seamless interaction with AI agents like Antigravity

This module provides simple, structured APIs that AI agents can call
to get Volume Profile analysis and trading insights.
"""

from typing import Dict, List, Optional
import json
from scanner import VolumeProfileScanner
from session_analysis import SessionAnalyzer
from risk_manager import RiskManager
from volume_profile_engine import VolumeProfileEngine, analyze_ticker, get_key_levels, ProfileComparator, ValueAreaMigrationTracker, POCZoneCalculator
from volume_profile_visualizer import visualize_ticker
from time_and_sales import TimeAndSalesAnalyzer
from market_profile import MarketProfileEngine
from composite_profile import CompositeProfileBuilder
from volume_nodes import VolumeNodeDetector
from pattern_detector import ProfilePatternDetector
from profile_stats import ProfileStatistics


class VolumeProfileAgent:
    """
    AI Agent-friendly wrapper for Volume Profile analysis
    Provides structured responses perfect for AI agents
    """
    
    def __init__(self):
        self.engine = VolumeProfileEngine() # Keep engine instance if needed for export_csv reusing logic

    @staticmethod
    def analyze(ticker: str, period: str = "1mo", interval: str = "15m") -> Dict:
        """
        Main analysis function for AI agents
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'SPY')
            period: Time period ('1d', '5d', '1mo', '3mo', '1y')
            interval: Data interval ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            Structured dictionary with complete analysis
        """
        try:
            engine = VolumeProfileEngine(ticker, period, interval)
            metrics = engine.get_all_metrics()
            
            if "error" in metrics:
                 return {'status': 'error', 'error': metrics['error']}

            # Add AI-friendly trading signals
            signals = VolumeProfileAgent._generate_signals(metrics)
            metrics['trading_signals'] = signals
            
            return {
                'status': 'success',
                'data': metrics
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def get_trading_plan(ticker: str, period: str = "1mo") -> Dict:
        """
        Generate actionable trading plan based on Volume Profile
        
        Args:
            ticker: Stock symbol
            period: Time period
        
        Returns:
            Dictionary with entry, stop loss, and target levels
        """
        try:
            engine = VolumeProfileEngine(ticker, period)
            metrics = engine.get_all_metrics()
            
            if "error" in metrics:
                return {'status': 'error', 'error': metrics['error']}

            current = metrics['current_price']
            poc = metrics['poc']
            vah = metrics['vah']
            val = metrics['val']
            
            plan = {}
            
            # Determine bias based on position
            if "ABOVE" in metrics['position']:
                plan['bias'] = 'BULLISH'
                plan['entry_zone'] = {'min': poc, 'max': vah}
                plan['stop_loss'] = val
                plan['target_1'] = vah + (vah - val)
                plan['target_2'] = vah + 2 * (vah - val)
                plan['strategy'] = 'Look for pullback to POC/VAH for long entry'
                
            elif "BELOW" in metrics['position']:
                plan['bias'] = 'BEARISH'
                plan['entry_zone'] = {'min': val, 'max': poc}
                plan['stop_loss'] = vah
                plan['target_1'] = val - (vah - val)
                plan['target_2'] = val - 2 * (vah - val)
                plan['strategy'] = 'Look for bounce to POC/VAL for short entry'
                
            else:
                plan['bias'] = 'NEUTRAL'
                plan['entry_zone'] = {'min': val, 'max': vah}
                plan['stop_loss'] = None
                plan['target_1'] = vah  # Breakout target
                plan['target_2'] = val  # Breakdown target
                plan['strategy'] = 'Wait for breakout above VAH (long) or below VAL (short)'
            
            plan['current_price'] = current
            plan['poc'] = poc
            plan['vah'] = vah
            plan['val'] = val
            
            return {
                'status': 'success',
                'ticker': ticker,
                'plan': plan
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def compare_tickers(tickers: List[str], period: str = "1mo") -> Dict:
        """
        Compare multiple tickers and rank by trading opportunity
        
        Args:
            tickers: List of stock symbols
            period: Time period
        
        Returns:
            Ranked comparison of tickers
        """
        results = []
        
        for ticker in tickers:
            try:
                engine = VolumeProfileEngine(ticker, period)
                metrics = engine.get_all_metrics()
                
                if "error" in metrics:
                    continue

                # Calculate opportunity score
                score = VolumeProfileAgent._calculate_opportunity_score(metrics)
                
                results.append({
                    'ticker': ticker,
                    'current_price': metrics['current_price'],
                    'position': metrics['position'].split('(')[0].strip(),
                    'distance_from_poc': abs(metrics['distance_from_poc_pct']),
                    'opportunity_score': score,
                    'poc': metrics['poc'],
                    'vah': metrics['vah'],
                    'val': metrics['val']
                })
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
        
        # Sort by opportunity score
        results.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return {
            'status': 'success',
            'comparison': results,
            'best_opportunity': results[0] if results else None
        }
    
    @staticmethod
    def get_alerts(ticker: str, period: str = "1mo") -> Dict:
        """
        Generate price alerts for key levels
        
        Args:
            ticker: Stock symbol
            period: Time period
        
        Returns:
            Dictionary with suggested price alerts
        """
        try:
            levels = get_key_levels(ticker, period)
            if not levels:
                 return {'status': 'error', 'error': 'Could not calculate levels'}

            alerts = {
                'ticker': ticker,
                'current_price': levels['current_price'],
                'alerts': [
                    {
                        'level': levels['vah'],
                        'type': 'resistance',
                        'message': f"Price approaching VAH resistance at ${levels['vah']:.2f}"
                    },
                    {
                        'level': levels['poc'],
                        'type': 'pivot',
                        'message': f"Price at POC pivot level ${levels['poc']:.2f}"
                    },
                    {
                        'level': levels['val'],
                        'type': 'support',
                        'message': f"Price approaching VAL support at ${levels['val']:.2f}"
                    }
                ]
            }
            
            return {
                'status': 'success',
                'data': alerts
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def create_chart(ticker: str, period: str = "1mo", interval: str = "15m", 
                    output_path: str = None) -> Dict:
        """
        Generate visual chart
        
        Args:
            ticker: Stock symbol
            period: Time period
            interval: Data interval
            output_path: Path to save chart (optional)
        
        Returns:
            Status and file path if saved
        """
        try:
            if output_path is None:
                output_path = f"{ticker}_volume_profile.png"
            
            visualize_ticker(ticker, period, interval, 
                           save_path=output_path, show=False)
            
            return {
                'status': 'success',
                'chart_path': output_path,
                'message': f'Chart saved to {output_path}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    def get_profile_comparison(ticker: str, days: int = 5) -> Dict:
        """Compare current profile vs previous day"""
        try:
            # New instance-based robust method
            comp = ProfileComparator(ticker).compare_yesterday_today()
            if not comp: return {'status': 'error', 'error': 'Not enough data'}
            return {'status': 'success', 'data': comp}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_migration_report(ticker: str, days: int = 10) -> Dict:
        """Track Value Area migration"""
        try:
            # New regression-based tracking
            tracker = ValueAreaMigrationTracker(ticker, days).track_migration()
            return {'status': 'success', 'data': tracker}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_poc_zones(ticker: str, days: int = 10) -> Dict:
        """Identify confluent POC zones"""
        try:
            # Multi-timeframe confluence
            zones = POCZoneCalculator(ticker).multi_timeframe_poc()
            return {'status': 'success', 'data': zones}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_order_flow_analysis(ticker: str) -> Dict:
        """Analyze Time & Sales (Volume Proxy)"""
        try:
            # 1. Get Levels
            engine = VolumeProfileEngine(ticker, period="1d", interval="5m")
            engine.fetch_data()
            profile = engine.calculate_volume_profile()
            poc = engine.find_poc()
            val, vah = engine.find_value_area()
            
            # 2. Analyze T&S
            ts_engine = VolumeProfileEngine(ticker, period="1d", interval="1m")
            ts_engine.fetch_data()
            analyzer = TimeAndSalesAnalyzer(ts_engine.data)
            
            large_prints = analyzer.analyze_large_prints()
            
            # Analyze all 3 key levels
            levels = {
                'poc': analyzer.analyze_activity_at_level(poc),
                'vah': analyzer.analyze_activity_at_level(vah),
                'val': analyzer.analyze_activity_at_level(val)
            }
            
            return {
                'status': 'success',
                'large_prints': large_prints,
                'levels': levels
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def _generate_signals(metrics: Dict) -> Dict:
        """Generate trading signals from metrics"""
        signals = []
        return {'signals': signals}
    # --- Phase 9: New Feature Methods ---

    @staticmethod
    def scan_watchlist(tickers: List[str], period: str = "1mo") -> Dict:
        """Scan multiple tickers and return ranked opportunities."""
        try:
            scanner = VolumeProfileScanner(tickers, period=period)
            results = scanner.scan_all()
            return {
                'status': 'success',
                'results': results,
                'report': scanner.generate_report(),
                'top': scanner.get_top(5),
                'errors': scanner.errors
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_session_analysis(ticker: str, period: str = "5d") -> Dict:
        """Analyze trading sessions (Asia/London/NY)."""
        try:
            analyzer = SessionAnalyzer(ticker, period=period)
            sessions = analyzer.analyze_sessions()
            comparison = analyzer.get_session_comparison()
            return {
                'status': 'success',
                'sessions': sessions,
                'comparison': comparison
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def calculate_risk(account_size: float, risk_pct: float,
                       entry: float, stop_loss: float,
                       targets: List[float] = None) -> Dict:
        """Calculate position sizing and risk metrics."""
        try:
            rm = RiskManager(account_size, risk_pct)
            pos = rm.calculate_position_size(entry, stop_loss)
            if 'error' in pos:
                return {'status': 'error', 'error': pos['error']}

            result = {'status': 'success', 'position': pos}

            if targets:
                plan = rm.multi_target_plan(entry, stop_loss, targets)
                result['targets'] = plan.get('targets', [])

            return result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    # --- Phase 7: Priority Features Methods ---

    @staticmethod
    def get_profile_comparison(ticker: str, period: str = "1mo") -> Dict:
        """Get yesterday vs today comparison"""
        try:
            comparator = ProfileComparator(ticker)
            return {'status': 'success', 'data': comparator.compare_yesterday_today()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_migration_tracker(ticker: str, lookback_days: int = 10) -> Dict:
        """Get value area migration tracking"""
        try:
            tracker = ValueAreaMigrationTracker(ticker, lookback_days)
            return {'status': 'success', 'data': tracker.track_migration()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_poc_zones(ticker: str) -> Dict:
        """Get POC zones with multi-timeframe confluence"""
        try:
            calculator = POCZoneCalculator(ticker)
            return {'status': 'success', 'data': calculator.multi_timeframe_poc()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_time_and_sales(ticker: str, poc: float, vah: float, val: float) -> Dict:
        """Get Time & Sales analysis"""
        try:
            analyzer = TimeAndSalesAnalyzer(ticker)
            large_prints = analyzer.find_large_prints()
            key_levels = analyzer.scan_key_levels(poc, vah, val)
            
            return {
                'status': 'success',
                'data': {
                    'large_prints': large_prints,
                    'key_levels': key_levels
                }
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    # --- Phase 8: Advanced Analytics Methods ---

    @staticmethod
    def get_market_profile_tpo(ticker: str) -> Dict:
        """Get Market Profile (TPO) analysis"""
        try:
            mp_engine = MarketProfileEngine(ticker)
            result = mp_engine.calculate_tpo_profile()
            return {'status': 'success', 'data': result}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_composite_profile(ticker: str, num_days: int = 5, weighting: str = 'equal') -> Dict:
        """Get composite profile"""
        try:
            builder = CompositeProfileBuilder(ticker)
            composite = builder.build_composite(num_days, weighting)
            return {'status': 'success', 'data': composite}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_volume_nodes(ticker: str, period: str = "1mo") -> Dict:
        """Get volume nodes and clusters"""
        try:
            engine = VolumeProfileEngine(ticker, period)
            engine.calculate_volume_profile()
            
            detector = VolumeNodeDetector(engine.volume_profile)
            nodes = detector.find_all_nodes()
            breakouts = detector.identify_breakout_zones()
            
            nodes['breakout_zones'] = breakouts
            return {'status': 'success', 'data': nodes}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_pattern_detection(ticker: str, period: str = "1mo") -> Dict:
        """Get pattern detection analysis"""
        try:
            engine = VolumeProfileEngine(ticker, period)
            engine.calculate_volume_profile() # Ensure profile exists
            
            detector = ProfilePatternDetector(
                engine.volume_profile,
                engine.data
            )
            patterns = detector.detect_all_patterns()
            return {'status': 'success', 'data': patterns}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @staticmethod
    def get_profile_statistics(ticker: str, period: str = "1mo") -> Dict:
        """Get comprehensive profile statistics"""
        try:
            engine = VolumeProfileEngine(ticker, period)
            metrics = engine.get_all_metrics()
            
            stats_calculator = ProfileStatistics(
                engine.volume_profile,
                engine.data,
                metrics['poc'],
                metrics['vah'],
                metrics['val']
            )
            stats = stats_calculator.calculate_all_statistics()
            return {'status': 'success', 'data': stats}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
        signals = {
            'primary_signal': '',
            'strength': '',
            'action': '',
            'risk_level': ''
        }
        
        position = metrics['position']
        distance = abs(metrics['distance_from_poc_pct'])
        
        if "ABOVE" in position:
            if distance > 5:
                signals['primary_signal'] = 'Strong bullish - far above POC'
                signals['strength'] = 'STRONG'
                signals['action'] = 'HOLD or wait for pullback'
                signals['risk_level'] = 'HIGH (overextended)'
            else:
                signals['primary_signal'] = 'Bullish near POC'
                signals['strength'] = 'MODERATE'
                signals['action'] = 'LOOK FOR LONG ENTRY'
                signals['risk_level'] = 'MEDIUM'
                
        elif "BELOW" in position:
            if distance > 5:
                signals['primary_signal'] = 'Strong bearish - far below POC'
                signals['strength'] = 'STRONG'
                signals['action'] = 'HOLD SHORT or wait for bounce'
                signals['risk_level'] = 'HIGH (overextended)'
            else:
                signals['primary_signal'] = 'Bearish near POC'
                signals['strength'] = 'MODERATE'
                signals['action'] = 'LOOK FOR SHORT ENTRY'
                signals['risk_level'] = 'MEDIUM'
        else:
            signals['primary_signal'] = 'Balanced in value area'
            signals['strength'] = 'WEAK'
            signals['action'] = 'WAIT FOR BREAKOUT'
            signals['risk_level'] = 'LOW (choppy)'
        
        return signals
    
    @staticmethod
    def _calculate_opportunity_score(metrics: Dict) -> float:
        """Calculate trading opportunity score (0-100)"""
        score = 50  # Base score
        
        distance = abs(metrics['distance_from_poc_pct'])
        
        # Closer to POC = higher opportunity
        if distance < 2:
            score += 30
        elif distance < 5:
            score += 15
        else:
            score -= 10
        
        # Inside value area = medium opportunity
        if "INSIDE" in metrics['position']:
            score += 10
        
        # Far from POC = lower opportunity (overextended)
        if distance > 10:
            score -= 20
        
        return max(0, min(100, score))

    def export_csv(self, ticker: str, period: str = "1mo", output_path: str = None) -> dict:
        """
        Export volume profile to CSV.
        """
        try:
            if output_path is None:
                output_path = f"{ticker}_profile.csv"
            
            engine = VolumeProfileEngine(ticker, period=period)
            df = engine.fetch_data(ticker, period=period)
            
            if df.empty:
                 return {"status": "error", "message": f"No data found for {ticker}"}
                 
            profile = engine.calculate_volume_profile(df)
            
            success = engine.export_to_csv(profile, output_path)
            
            return {
                'status': 'success' if success else 'error',
                'file_path': output_path if success else None,
                'message': f'Exported to {output_path}' if success else 'Export failed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    
    def analyze_composite(self, ticker: str, days: int = 5) -> dict:
        """
        Analyzes a composite profile over a specified number of days.
        """
        # ... logic ...
        # For brevity, implementing a wrapper around engine's composite logic if needed, 
        # or just relying on engine's new capabilities.
        # Re-implementing simplified version:
        
        engine = VolumeProfileEngine()
        period_map = {5: "5d", 10: "1mo", 20: "1mo", 60: "3mo"}
        period = period_map.get(days, "1mo")
        
        df = engine.fetch_data(ticker, period=period, interval="1h")
        if df.empty: return {"error": "No data"}
        
        profile = engine.calculate_composite_profile(df)
        if profile.empty: return {"error": "No profile"}
        
        metrics = engine.get_all_metrics() # Note: this gets metrics for the WHOLE period in engine, which matches basic composite
        # To be precise we should recalculate metrics on the composite profile
        
        poc = engine.find_poc(profile)
        total_volume = profile['Volume'].sum()
        vah, val = engine.find_value_area(profile, total_volume)
        shape = engine.detect_profile_shape(profile)
        
        return {
            "ticker": ticker.upper(),
            "type": "Composite",
            "period_days": days,
            "poc": round(poc, 2),
            "vah": round(vah, 2),
            "val": round(val, 2),
            "shape": shape
        }

    def check_confluence(self, ticker: str) -> dict:
        """
        Checks for confluence between Weekly (Long-term) and Daily (Short-term) profiles.
        """
        try:
            # 1. Weekly Profile (Long-term context)
            lt_engine = VolumeProfileEngine(ticker, period="1y", interval="1wk")
            lt_metrics = lt_engine.get_all_metrics()
            if "error" in lt_metrics: return {"error": "Could not fetch Long-term data"}

            # 2. Daily Profile (Short-term execution)
            st_engine = VolumeProfileEngine(ticker, period="1mo", interval="1d")
            st_metrics = st_engine.get_all_metrics()
            if "error" in st_metrics: return {"error": "Could not fetch Short-term data"}
            
            # 3. Find Confluence (Overlapping levels within threshold)
            confluences = []
            
            # Key levels to compare
            lt_levels = {'LT_POC': lt_metrics['poc'], 'LT_VAH': lt_metrics['vah'], 'LT_VAL': lt_metrics['val']}
            st_levels = {'ST_POC': st_metrics['poc'], 'ST_VAH': st_metrics['vah'], 'ST_VAL': st_metrics['val']}
            
            # Threshold for "Confluence" (e.g. 0.5% price difference)
            threshold = st_metrics['current_price'] * 0.005 
            
            for lt_name, lt_price in lt_levels.items():
                for st_name, st_price in st_levels.items():
                    if abs(lt_price - st_price) <= threshold:
                        confluences.append({
                            "level": round((lt_price + st_price) / 2, 2),
                            "sources": [lt_name, st_name],
                            "type": "Strong Support/Resistance"
                        })
                        
            return {
                "ticker": ticker,
                "confluences": confluences,
                "long_term": {"bias": lt_metrics['position'], "poc": lt_metrics['poc']},
                "short_term": {"bias": st_metrics['position'], "poc": st_metrics['poc']},
                "message": f"Found {len(confluences)} confluence levels."
            }
            
        except Exception as e:
            return {"error": str(e)}


# Convenience functions for quick AI agent calls
def ai_analyze(ticker: str, period: str = "1mo", interval: str = "15m") -> str:
    """Return JSON string for easy AI parsing"""
    result = VolumeProfileAgent.analyze(ticker, period, interval)
    return json.dumps(result, indent=2)


def ai_get_plan(ticker: str, period: str = "1mo") -> str:
    """Return trading plan as JSON string"""
    result = VolumeProfileAgent.get_trading_plan(ticker, period)
    return json.dumps(result, indent=2)


def ai_compare(tickers: List[str], period: str = "1mo") -> str:
    """Return comparison as JSON string"""
    result = VolumeProfileAgent.compare_tickers(tickers, period)
    return json.dumps(result, indent=2)


# Command examples for AI agents
AGENT_COMMANDS = {
    'analyze': 'VolumeProfileAgent.analyze("AAPL")',
    'get_plan': 'VolumeProfileAgent.get_trading_plan("SPY")',
    'compare': 'VolumeProfileAgent.compare_tickers(["AAPL", "MSFT", "GOOGL"])',
    'alerts': 'VolumeProfileAgent.get_alerts("TSLA")',
    'chart': 'VolumeProfileAgent.create_chart("NVDA", output_path="chart.png")'
}


if __name__ == "__main__":
    # Test AI agent interface
    print("=== AI AGENT INTEGRATION TEST ===\n")
    
    # Test 1: Analyze
    print("1. Analyzing SPY...")
    result = VolumeProfileAgent.analyze("SPY", period="5d")
    print(json.dumps(result, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Trading Plan
    print("2. Getting trading plan for AAPL...")
    plan = VolumeProfileAgent.get_trading_plan("AAPL")
    print(json.dumps(plan, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Compare
    print("3. Comparing multiple tickers...")
    comparison = VolumeProfileAgent.compare_tickers(["SPY", "QQQ", "DIA"])
    print(json.dumps(comparison, indent=2))
