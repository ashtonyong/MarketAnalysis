"""
Volume Profile Visual Dashboard
Interactive charts and professional visualization
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter
import numpy as np
from volume_profile_engine import VolumeProfileEngine


class VolumeProfileVisualizer:
    """
    Visual dashboard for Volume Profile analysis
    Creates professional charts and visualizations
    """
    
    def __init__(self, engine: VolumeProfileEngine):
        """
        Initialize visualizer with a Volume Profile Engine
        
        Args:
            engine: VolumeProfileEngine instance with calculated data
        """
        self.engine = engine
        self.fig = None
        self.axes = None
        
    def create_full_dashboard(self, save_path: str = None):
        """
        Create complete dashboard with multiple views
        
        Args:
            save_path: Optional path to save the figure
        """
        # Ensure data is loaded
        if self.engine.data is None or self.engine.data.empty:
            self.engine.fetch_data()
        if self.engine.volume_profile is None or self.engine.volume_profile.empty:
            self.engine.calculate_volume_profile()
        
        # Get metrics
        metrics = self.engine.get_all_metrics()
        
        # Create figure with subplots
        self.fig = plt.figure(figsize=(16, 10))
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main chart: Price action with volume profile overlay
        ax_main = self.fig.add_subplot(gs[0:2, 0:2])
        self._plot_price_with_profile(ax_main, metrics)
        
        # Volume Profile histogram (rotated)
        ax_profile = self.fig.add_subplot(gs[0:2, 2])
        self._plot_volume_histogram(ax_profile, metrics)
        
        # Volume bars
        ax_volume = self.fig.add_subplot(gs[2, 0:2])
        self._plot_volume_bars(ax_volume)
        
        # Metrics panel
        ax_metrics = self.fig.add_subplot(gs[2, 2])
        self._plot_metrics_panel(ax_metrics, metrics)
        
        # Overall title
        position_emoji = "🟢" if "ABOVE" in metrics['position'] else "🔴" if "BELOW" in metrics['position'] else "🟡"
        self.fig.suptitle(
            f"{position_emoji} {metrics['ticker']} - Volume Profile Analysis",
            fontsize=16, fontweight='bold'
        )
        
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[SAVED] Saved dashboard to {save_path}")
        
        return self.fig
    
    def _plot_price_with_profile(self, ax, metrics):
        """Plot price candlesticks with volume profile overlay"""
        data = self.engine.data
        
        # Plot price as line (simpler than candlesticks for now)
        ax.plot(data.index, data['Close'], color='#2962FF', linewidth=1.5, label='Close Price')
        
        # Add high/low envelope
        ax.fill_between(data.index, data['Low'], data['High'], 
                        alpha=0.1, color='#2962FF', label='High-Low Range')
        
        # Plot key levels
        ax.axhline(metrics['poc'], color='#FF6D00', linewidth=2, 
                  linestyle='--', label=f"POC: ${metrics['poc']:.2f}")
        ax.axhline(metrics['vah'], color='#00C853', linewidth=1.5, 
                  linestyle='--', label=f"VAH: ${metrics['vah']:.2f}")
        ax.axhline(metrics['val'], color='#D50000', linewidth=1.5, 
                  linestyle='--', label=f"VAL: ${metrics['val']:.2f}")
        
        # Shade value area
        ax.axhspan(metrics['val'], metrics['vah'], alpha=0.1, color='gray', 
                  label='Value Area (70%)')
        
        # Current price marker
        current_price = metrics['current_price']
        ax.plot(data.index[-1], current_price, 'o', 
               markersize=10, color='white', markeredgecolor='black', 
               markeredgewidth=2, label=f"Current: ${current_price:.2f}")
        
        ax.set_title('Price Action with Volume Profile Levels', fontweight='bold')
        ax.set_ylabel('Price ($)', fontweight='bold')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_volume_histogram(self, ax, metrics):
        """Plot volume distribution histogram"""
        vp = self.engine.volume_profile
        
        # Create horizontal bar chart
        # NOTE: Using 'Price' and 'Volume' based on engine implementation
        colors = []
        for price in vp['Price']:
            if price >= metrics['val'] and price <= metrics['vah']:
                colors.append('#4CAF50')  # Green for value area
            elif abs(price - metrics['poc']) < 0.1: # Approximate equality
                colors.append('#FF6D00')  # Orange for POC
            else:
                colors.append('#757575')  # Gray for outside value area
        
        ax.barh(vp['Price'], vp['Volume'], height=(vp['Price'].max() - vp['Price'].min()) / len(vp),
               color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Add key level lines
        ax.axhline(metrics['poc'], color='#FF6D00', linewidth=2, linestyle='--')
        ax.axhline(metrics['vah'], color='#00C853', linewidth=1.5, linestyle='--')
        ax.axhline(metrics['val'], color='#D50000', linewidth=1.5, linestyle='--')
        
        # Current price line
        ax.axhline(metrics['current_price'], color='black', linewidth=2)
        
        ax.set_title('Volume Distribution', fontweight='bold')
        ax.set_xlabel('Volume', fontweight='bold')
        ax.set_ylabel('Price ($)', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add legend
        value_area_patch = mpatches.Patch(color='#4CAF50', label='Value Area')
        poc_patch = mpatches.Patch(color='#FF6D00', label='POC')
        other_patch = mpatches.Patch(color='#757575', label='Outside VA')
        ax.legend(handles=[value_area_patch, poc_patch, other_patch], 
                 loc='upper right', fontsize=8)
    
    def _plot_volume_bars(self, ax):
        """Plot volume bars over time"""
        data = self.engine.data
        
        # Color bars based on price movement
        colors = ['#00C853' if close > open_price else '#D50000' 
                 for close, open_price in zip(data['Close'], data['Open'])]
        
        ax.bar(data.index, data['Volume'], color=colors, alpha=0.7, width=0.8)
        
        ax.set_title('Volume Over Time', fontweight='bold')
        ax.set_ylabel('Volume', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(DateFormatter('%m/%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_metrics_panel(self, ax, metrics):
        """Display key metrics as text panel"""
        ax.axis('off')
        
        # Create metrics text
        # Using .get for robustness if keys are missing
        pos_str = metrics.get('position', 'N/A')
        if isinstance(pos_str, str):
            pos_str = pos_str.split('(')[0].strip()

        text = f"KEY METRICS\n\n"
        text += f"Current: ${metrics['current_price']:.2f}\n\n"
        text += f"POC: ${metrics['poc']:.2f}\n"
        text += f"VAH: ${metrics['vah']:.2f}\n"
        text += f"VAL: ${metrics['val']:.2f}\n\n"
        text += f"Distance from POC:\n{metrics.get('distance_from_poc_pct', 0):+.2f}%\n\n"
        text += f"Position:\n{pos_str}\n\n"
        text += f"Period:\n{str(metrics.get('data_start', ''))[:10]} to\n{str(metrics.get('data_end', ''))[:10]}\n\n"
        text += f"Total Volume:\n{metrics.get('total_volume', 0):,.0f}"

        # Color based on position
        if "ABOVE" in metrics.get('position', ''):
            bg_color = '#E8F5E9'  # Light green
            title_color = '#00C853'
        elif "BELOW" in metrics.get('position', ''):
            bg_color = '#FFEBEE'  # Light red
            title_color = '#D50000'
        else:
            bg_color = '#FFF9C4'  # Light yellow
            title_color = '#F57F17'
        
        # Add background
        ax.add_patch(mpatches.Rectangle((0, 0), 1, 1, 
                                       transform=ax.transAxes,
                                       facecolor=bg_color, 
                                       edgecolor=title_color, 
                                       linewidth=3))
        
        # Add text
        ax.text(0.5, 0.5, text.strip(), 
               transform=ax.transAxes,
               fontsize=9,
               verticalalignment='center',
               horizontalalignment='center',
               fontfamily='monospace')
    
    def show(self):
        """Display the dashboard"""
        plt.show()


def visualize_ticker(ticker: str, period: str = "1mo", interval: str = "15m", 
                    save_path: str = None, show: bool = True):
    """
    Quick function to visualize a ticker
    
    Args:
        ticker: Stock symbol
        period: Time period
        interval: Data interval
        save_path: Optional path to save figure
        show: Whether to display the plot
    
    Returns:
        matplotlib Figure object
    """
    # Create engine and calculate
    engine = VolumeProfileEngine(ticker, period, interval)
    engine.fetch_data()
    engine.calculate_volume_profile()
    engine.get_all_metrics()
    
    # Create visualizer
    viz = VolumeProfileVisualizer(engine)
    fig = viz.create_full_dashboard(save_path=save_path)
    
    if show:
        viz.show()
    
    return fig


if __name__ == "__main__":
    # Test visualization
    import sys
    
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    print(f"Creating dashboard for {ticker}...")
    
    visualize_ticker(ticker, period="5d", interval="15m", save_path=f"{ticker}_dashboard.png", show=False)
