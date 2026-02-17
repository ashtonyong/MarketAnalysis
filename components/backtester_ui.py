import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from backtester import BacktestEngine
from quant_engine import (
    MonteCarloSimulator, RegimeDetector,
    KellyCriterion, ZScoreCalculator,
    SetupScorer, CorrelationAnalyzer
)
from volume_profile_engine import VolumeProfileEngine

def render_backtester_tab(ticker: str, period: str):
    """Full professional backtester UI"""

    st.header("⚡ Strategy Backtester")

    engine = BacktestEngine()

    # Strategy selector
    col1, col2, col3, col4 = st.columns(4)

    strategy = col1.selectbox("Strategy", [
        'value_area_reversion',
        'poc_bounce',
        'failed_auction',
        'zscore_mean_reversion',
        'breakout_retest'
    ], help="Select trading strategy to backtest")

    capital = col2.number_input("Capital ($)", value=10000, step=1000)
    risk = col3.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.1)
    
    # Map friendly names to actual intervals
    period_map = {'3mo': '3mo', '6mo': '6mo', '1y': '1y', '2y': '2y'}
    bt_period = col4.selectbox("Period", list(period_map.keys()), index=2)

    col1b, col2b = st.columns(2)
    run_single = col1b.button("▶ Run Strategy", type="primary",
                               use_container_width=True)
    run_all = col2b.button("⚡ Compare All 5 Strategies",
                           use_container_width=True)

    if run_single:
        with st.spinner(f"Running {strategy}..."):
            results = engine.run_backtest(ticker, strategy, bt_period,
                                         '1d', capital, risk)

        if 'error' in results:
            st.error(f"Error: {results['error']}")
        else:
            # ---- RESULTS HEADER ----
            st.success(f"✅ Backtest complete: {results['total_trades']} trades")

            # Key metrics row
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Total Return",
                      f"{results.get('total_return_pct', 0):+.1f}%")
            c2.metric("Win Rate",
                      f"{results.get('win_rate', 0):.1f}%")
            c3.metric("Profit Factor",
                      f"{results.get('profit_factor', 0):.2f}")
            c4.metric("Max Drawdown",
                      f"-{results.get('max_drawdown_pct', 0):.1f}%")
            c5.metric("Sharpe Ratio",
                      f"{results.get('sharpe_ratio', 0):.2f}")
            c6.metric("Trades",
                      results.get('total_trades', 0))

            st.divider()

            # Tabs for detailed results
            t1, t2, t3, t4, t5, t6 = st.tabs([
                "📈 Equity Curve",
                "🎲 Monte Carlo",
                "📊 Statistical Edge",
                "🎯 Kelly Sizing",
                "🌊 Market Regime",
                "📋 Trade Log"
            ])

            with t1:
                st.subheader("Equity Curve")
                if results.get('equity_curve'):
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=results['equity_curve'],
                        mode='lines',
                        name='Portfolio Value',
                        line=dict(color='#00C853', width=2)
                    ))
                    fig.add_hline(y=capital, line_dash='dash',
                                  line_color='gray',
                                  annotation_text='Starting Capital')
                    fig.update_layout(
                        title=f'{strategy} - Equity Curve',
                        yaxis_title='Portfolio Value ($)',
                        xaxis_title='Trade Number',
                        template='plotly_dark',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with t2:
                st.subheader("Monte Carlo Simulation (5,000 runs)")
                mc_data = results.get('monte_carlo', {})
                if mc_data and 'results' in mc_data:
                    r = mc_data['results']
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Median Outcome",
                              f"${r['median']:,.0f}",
                              delta=f"{r['expected_return_pct']:+.1f}%")
                    c2.metric("Best Case (95th)",
                              f"${r['best_case']:,.0f}",
                              delta=f"{r['best_return_pct']:+.1f}%")
                    c3.metric("Worst Case (5th)",
                              f"${r['worst_case']:,.0f}",
                              delta=f"{r['worst_return_pct']:+.1f}%")

                    st.metric("Probability of Profit",
                              f"{r['probability_of_profit']}%")
                    st.metric("Expected Max Drawdown",
                              f"{r['avg_max_drawdown']:.1f}%")

                    if mc_data.get('sample_equity_curves'):
                        fig = go.Figure()
                        for curve in mc_data['sample_equity_curves'][:30]:
                            fig.add_trace(go.Scatter(
                                y=curve, mode='lines', opacity=0.2,
                                line=dict(color='blue', width=1),
                                showlegend=False
                            ))
                        fig.update_layout(
                            title='Monte Carlo - 30 Sample Paths',
                            template='plotly_dark',
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)

            with t3:
                st.subheader("Statistical Edge Analysis")
                edge = results.get('statistical_edge', {})
                if edge and 'error' not in edge:
                    verdict = edge.get('verdict', '')
                    if 'EXCELLENT' in verdict or 'GOOD' in verdict:
                        st.success(f"✅ {edge.get('recommendation', '')}")
                    elif 'MARGINAL' in verdict:
                        st.warning(f"⚠️ {edge.get('recommendation', '')}")
                    else:
                        st.error(f"❌ {edge.get('recommendation', '')}")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Win Rate",
                              f"{edge.get('win_rate', 0):.1f}%")
                    c2.metric("Profit Factor",
                              f"{edge.get('profit_factor', 0):.2f}")
                    c3.metric("Expectancy",
                              f"${edge.get('expectancy_per_trade', 0):.2f}")
                    c4.metric("Max Consec. Losses",
                              edge.get('max_consecutive_losses', 0))

                    c1b, c2b = st.columns(2)
                    c1b.metric("Avg Win",
                               f"${edge.get('avg_win', 0):.2f}")
                    c2b.metric("Avg Loss",
                               f"${edge.get('avg_loss', 0):.2f}")

            with t4:
                st.subheader("Kelly Criterion Position Sizing")
                kelly = results.get('kelly_criterion', {})
                if kelly and 'error' not in kelly:
                    st.info(f"💡 {kelly.get('recommendation', '')}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Full Kelly",
                              f"{kelly.get('full_kelly_pct', 0):.1f}%")
                    c2.metric("Half Kelly (Recommended)",
                              f"{kelly.get('half_kelly_pct', 0):.1f}%")
                    c3.metric("Safe Kelly",
                              f"{kelly.get('safe_kelly_pct', 0):.1f}%")

                    st.subheader("Recommended Position Sizes")
                    for account, size in kelly.get('position_sizes', {}).items():
                        st.write(f"**{account}:** Risk {size} per trade")

            with t5:
                st.subheader("Market Regime Analysis")
                regime = results.get('regime', {})
                if regime:
                    reg = regime.get('regime', 'UNKNOWN')
                    if 'RANGING' in reg:
                        st.success(f"📊 Regime: **{reg}**")
                    elif 'TRENDING' in reg:
                        st.info(f"📈 Regime: **{reg}**")
                    else:
                        st.warning(f"⚡ Regime: **{reg}**")

                    st.write(f"**{regime.get('description', '')}**")
                    st.write(f"Best Strategy: {regime.get('best_strategy', '')}")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("ADX", f"{regime.get('adx', 0):.1f}")
                    c2.metric("ATR Ratio",
                              f"{regime.get('atr_ratio', 0):.2f}x")
                    c3.metric("Confidence",
                              regime.get('confidence', 'N/A'))

                    st.subheader("Recommendations")
                    for rec in regime.get('recommendations', []):
                        st.write(rec)

            with t6:
                st.subheader("Trade Log")
                trades = results.get('trades', [])
                if trades:
                    trade_data = [{
                        'Time': str(t.entry_time)[:16],
                        'Dir': t.direction,
                        'Entry': f"${t.entry_price:.2f}",
                        'Exit': f"${t.exit_price:.2f}",
                        'P&L': f"${t.pnl:.2f}",
                        'Result': t.result,
                        'Exit Reason': t.exit_reason
                    } for t in trades[-50:]]
                    
                    df_log = pd.DataFrame(trade_data)
                    st.dataframe(df_log, width="stretch", hide_index=True)

                    # Export
                    csv = df_log.to_csv(index=False)
                    st.download_button(
                        "📥 Download Trade Log",
                        csv,
                        f"trades_{strategy}_{ticker}.csv",
                        "text/csv"
                    )

    if run_all:
        with st.spinner("Running all 5 strategies..."):
            comparison = engine.compare_all_strategies(ticker, bt_period,
                                                       '1d', capital)

        if 'comparison' in comparison and comparison['comparison']:
            best = comparison['best_strategy']
            st.success(f"✅ Best strategy: **{best['strategy']}**")

            df_comp = pd.DataFrame(comparison['comparison'])
            df_comp.columns = ['Strategy', 'Trades', 'Win Rate %',
                         'Return %', 'Profit Factor',
                         'Max DD %', 'Sharpe', 'Expectancy $']

            # Color code by return
            st.dataframe(df_comp, width="stretch", hide_index=True)

    # ---- STANDALONE QUANT TOOLS ----
    st.divider()
    st.header("🔬 Quant Analysis Tools")

    qt1, qt2, qt3 = st.tabs([
        "🎲 Monte Carlo",
        "📐 Z-Score",
        "🔗 Correlation"
    ])

    with qt1:
        st.subheader("Monte Carlo Simulator")
        st.caption("Simulate thousands of outcomes for any strategy")

        c1, c2, c3 = st.columns(3)
        mc_wr = c1.slider("Win Rate (%)", 30, 80, 65)
        mc_win = c2.number_input("Avg Win ($)", value=150.0)
        mc_loss = c3.number_input("Avg Loss ($)", value=100.0)

        c4, c5 = st.columns(2)
        mc_trades = c4.slider("Trades to Simulate", 20, 500, 100)
        mc_cap = c5.number_input("Starting Capital ($)", value=10000)

        if st.button("🎲 Run Monte Carlo"):
            mc = MonteCarloSimulator()
            mc_results = mc.run(mc_wr/100, mc_win, mc_loss,
                               mc_trades, 5000, mc_cap)

            r = mc_results['results']
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Median", f"${r['median']:,.0f}",
                      f"{r['expected_return_pct']:+.1f}%")
            c2.metric("Best (95th)", f"${r['best_case']:,.0f}",
                      f"{r['best_return_pct']:+.1f}%")
            c3.metric("Worst (5th)", f"${r['worst_case']:,.0f}",
                      f"{r['worst_return_pct']:+.1f}%")
            c4.metric("Prob of Profit", f"{r['probability_of_profit']}%")

    with qt2:
        st.subheader("Z-Score Calculator")
        st.caption("See how statistically extreme current price is")

        if st.button("📐 Calculate Z-Score"):
            vpe = VolumeProfileEngine(ticker, period='3mo')
            metric_data = vpe.get_all_metrics()

            z_calc = ZScoreCalculator()
            z_results = z_calc.calculate(vpe.data, metric_data['poc'])

            if z_results.get('signal') in ['STRONGLY_OVERBOUGHT',
                                           'STRONGLY_OVERSOLD']:
                st.error(f"⚠️ {z_results['signal']}: {z_results['action']}")
            else:
                st.info(f"📊 {z_results['signal']}: {z_results['action']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Z-Score", f"{z_results['current_z_score']:.3f}")
            c2.metric("Mean", f"${z_results['rolling_mean']:.2f}")
            c3.metric("Reversion Prob",
                      f"{z_results['reversion_probability']}%")
            st.write(z_results['interpretation'])

    with qt3:
        st.subheader("Correlation Matrix")
        st.caption("Find correlated assets - avoid doubling up risk")

        default_tickers = "SPY, QQQ, AAPL, MSFT, GLD, TLT"
        corr_input = st.text_input("Tickers (comma-separated)",
                                   default_tickers)

        if st.button("🔗 Analyze Correlations"):
            tickers_list = [t.strip() for t in corr_input.split(',')]
            analyzer = CorrelationAnalyzer()

            with st.spinner("Calculating correlations..."):
                corr_results = analyzer.calculate(tickers_list, '3mo')

            if 'error' not in corr_results:
                st.subheader("⚠️ Highly Correlated Pairs (Avoid Both)")
                for pair in corr_results.get('high_correlation_pairs', []):
                    st.warning(
                        f"{pair['ticker1']} + {pair['ticker2']}: "
                        f"r={pair['correlation']} - {pair['warning']}"
                    )

                st.subheader("✅ Good Hedge Pairs")
                for hedge in corr_results.get('hedge_pairs', []):
                    st.success(
                        f"{hedge['ticker1']} + {hedge['ticker2']}: "
                        f"r={hedge['correlation']} - {hedge['note']}"
                    )

                corr_df = pd.DataFrame(corr_results['correlation_matrix'])
                st.subheader("Full Correlation Matrix")
                st.dataframe(corr_df.style.background_gradient(
                    cmap='RdYlGn', vmin=-1, vmax=1),
                    width="stretch")
