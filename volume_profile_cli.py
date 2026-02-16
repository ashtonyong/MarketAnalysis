"""
Volume Profile CLI - Command Line Interface
Quick testing and analysis from terminal
"""

import argparse
import sys
from volume_profile_engine import VolumeProfileEngine, analyze_ticker, get_key_levels, check_position
from ai_agent_interface import VolumeProfileAgent # Added for confluence/export capabilities
from volume_profile_backtester import VolumeProfileBacktester, STRATEGIES

def cli_analyze(args):
    """Analyze a ticker and show full report"""
    print(f"\n[ANALYSIS] Analyzing {args.ticker}...\n")
    
    engine = VolumeProfileEngine(
        ticker=args.ticker,
        period=args.period,
        interval=args.interval
    )
    
    # Show summary
    print(engine.get_summary())
    
    # Show detailed metrics if verbose
    if args.verbose:
        print("\n[METRICS] DETAILED METRICS:")
        metrics = engine.get_all_metrics() # Ensure we call the method to get dict
        for key, value in metrics.items():
            print(f"   {key}: {value}")


def cli_quick(args):
    """Quick check of key levels"""
    print(f"\n[QUICK] Quick Check - {args.ticker}\n")
    
    levels = get_key_levels(args.ticker, args.period)
    if not levels:
        print("Error fetching data.")
        return

    position = check_position(args.ticker, args.period)
    
    print(f"Current Price: ${levels['current_price']:.2f}")
    print(f"POC:          ${levels['poc']:.2f}")
    print(f"VAH:          ${levels['vah']:.2f}")
    print(f"VAL:          ${levels['val']:.2f}")
    print(f"\nPosition: {position} Value Area")
    print()


def cli_compare(args):
    """Compare multiple tickers"""
    print(f"\n[COMPARE] Comparing {', '.join(args.tickers)}...\n")
    
    results = []
    for ticker in args.tickers:
        try:
            levels = get_key_levels(ticker, args.period)
            position = check_position(ticker, args.period)
            if levels:
                results.append({
                    'ticker': ticker,
                    'price': levels['current_price'],
                    'poc': levels['poc'],
                    'position': position
                })
        except Exception as e:
            print(f"[ERROR] Error analyzing {ticker}: {e}")
    
    # Print comparison table
    print(f"{'TICKER':<8} {'PRICE':<10} {'POC':<10} {'POSITION':<10}")
    print("=" * 50)
    for r in results:
        pos_str = r['position'] if r['position'] else "N/A"
        print(f"{r['ticker']:<8} ${r['price']:<9.2f} ${r['poc']:<9.2f} {pos_str:<10}")
    print()


def cli_levels(args):
    """Export key levels for trading platform"""
    print(f"\n[LEVELS] Exporting levels for {args.ticker}...\n")
    
    levels = get_key_levels(args.ticker, args.period)
    if not levels:
        print("Error fetching levels.")
        return

    # Format for TradingView or similar
    print("# Copy these levels to your trading platform:")
    print(f"VAH: {levels['vah']:.2f}")
    print(f"POC: {levels['poc']:.2f}")
    print(f"VAL: {levels['val']:.2f}")
    
    # Also show as alerts
    print("\n# Suggested Alerts:")
    print(f"Alert if price crosses above VAH: {levels['vah']:.2f}")
    print(f"Alert if price crosses below VAL: {levels['val']:.2f}")
    print(f"Alert if price touches POC: {levels['poc']:.2f}")
    print()

def cli_export(args):
    """Export profile to CSV"""
    print(f"\n[EXPORT] Exporting CSV for {args.ticker}...\n")
    agent = VolumeProfileAgent()
    outfile = args.output if args.output else f"{args.ticker}_profile.csv"
    res = agent.export_csv(args.ticker, period=args.period, output_path=outfile)
    print(res['message'])

def cli_confluence(args):
    """Check multi-timeframe confluence"""
    print(f"\n[CONFLUENCE] Checking Confluence for {args.ticker}...\n")
    agent = VolumeProfileAgent()
    result = agent.check_confluence(args.ticker)
    
    if "error" in result:
         print(f"Error: {result['error']}")
         return

    print("=" * 50)
    print(f"MULTI-TIMEFRAME ANALYSIS: {result['ticker']}")
    print("=" * 50)
    
    lt = result['long_term']
    st = result['short_term']
    
    print(f"Long-Term (Weekly): {lt['bias']}")
    print(f"Short-Term (Daily): {st['bias']}")
    print("-" * 50)
    
    confluences = result['confluences']
    if not confluences:
        print("[NONE] No strong confluence levels found.")
    else:
        print(f"[FOUND] Found {len(confluences)} Confluence Levels:\n")
        print("{:<10} {:<30} {:<10}".format("Level", "Sources", "Type"))
        print("-" * 50)
        for c in confluences:
            sources = "+".join(c['sources'])
            print("{:<10} {:<30} {:<10}".format(
                f"${c['level']}", 
                sources,
                "Strong"
            ))
    print("=" * 50)


def cli_backtest(args):
    """Run backtest simulation"""
    print(f"\n[BACKTEST] Running {args.strategy} on {args.ticker}...\n")
    
    try:
        bt = VolumeProfileBacktester(args.ticker, initial_capital=args.capital)
        strategy = STRATEGIES.get(args.strategy)
        
        if not strategy:
            print(f"Strategy {args.strategy} not found.")
            return

        results = bt.run_strategy(strategy)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return
            
        print("-" * 40)
        print(f"PERFORMANCE REPORT ({args.ticker})")
        print("-" * 40)
        print(f"Total Trades:    {results['total_trades']}")
        print(f"Win Rate:        {results['win_rate']}%")
        print(f"Total Return:    {results['total_return']}%")
        print(f"Final Capital:   ${results['final_capital']:.2f}")
        print(f"Avg Win:         {results['avg_win']:.2f}%")
        print(f"Avg Loss:        {results['avg_loss']:.2f}%")
        print("-" * 40)
        
    except Exception as e:
        print(f"Backtest failed: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Volume Profile Analysis Tool - Professional Grade',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full analysis of SPY
  python volume_profile_cli.py analyze SPY
  
  # Quick check with custom period
  python volume_profile_cli.py quick AAPL --period 3mo
  
  # Compare multiple stocks
  python volume_profile_cli.py compare AAPL MSFT GOOGL
  
  # Export levels for trading
  python volume_profile_cli.py levels TSLA

  # Export to CSV
  python volume_profile_cli.py export SPY

  # Check confluence
  python volume_profile_cli.py confluence SPY
  
  # Detailed analysis with 5-minute bars
  python volume_profile_cli.py analyze SPY --interval 5m --verbose
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Full volume profile analysis')
    analyze_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    analyze_parser.add_argument('--period', type=str, default='1mo', 
                               help='Time period (1d, 5d, 1mo, 3mo, 1y, etc.)')
    analyze_parser.add_argument('--interval', type=str, default='15m',
                               help='Data interval (1m, 5m, 15m, 1h, 1d)')
    analyze_parser.add_argument('--verbose', '-v', action='store_true',
                               help='Show detailed metrics')
    analyze_parser.set_defaults(func=cli_analyze)
    
    # Quick command
    quick_parser = subparsers.add_parser('quick', help='Quick key levels check')
    quick_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    quick_parser.add_argument('--period', type=str, default='1mo',
                             help='Time period')
    quick_parser.set_defaults(func=cli_quick)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple tickers')
    compare_parser.add_argument('tickers', type=str, nargs='+',
                               help='Stock ticker symbols to compare')
    compare_parser.add_argument('--period', type=str, default='1mo',
                               help='Time period')
    compare_parser.set_defaults(func=cli_compare)

    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Backtest a strategy')
    backtest_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    backtest_parser.add_argument('--strategy', type=str, choices=list(STRATEGIES.keys()), default='mean_reversion', help='Strategy to run')
    backtest_parser.add_argument('--capital', type=float, default=10000, help='Initial capital')
    backtest_parser.set_defaults(func=cli_backtest)
    
    # Levels command
    levels_parser = subparsers.add_parser('levels', help='Export key levels')
    levels_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    levels_parser.add_argument('--period', type=str, default='1mo',
                              help='Time period')
    levels_parser.set_defaults(func=cli_levels)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    export_parser.add_argument('--period', type=str, default='1mo', help='Time period')
    export_parser.add_argument('--output', type=str, default=None, help='Output filename')
    export_parser.set_defaults(func=cli_export)

    # Confluence command
    confluence_parser = subparsers.add_parser('confluence', help='Check multi-timeframe confluence')
    confluence_parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    confluence_parser.set_defaults(func=cli_confluence)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}\n")
        # import traceback; traceback.print_exc() # debug
        sys.exit(1)


if __name__ == "__main__":
    main()
