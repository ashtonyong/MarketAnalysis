"""
Volume Node Detector
Identifies HVN (Support/Resistance) and LVN (Breakout Zones).
"""
import pandas as pd
import numpy as np
from typing import Dict, List

class VolumeNodeDetector:
    """
    Analyzes profile shape to find structure.
    """
    
    def __init__(self, profile_df: pd.DataFrame):
        self.profile = profile_df
        
    def find_all_nodes(self, hvn_threshold: float = 1.3, lvn_threshold: float = 0.7) -> Dict:
        """
        Finds all volume nodes and groups them.
        """
        if self.profile.empty: 
            return {'hvn': [], 'lvn': [], 'average_volume': 0}
            
        # Normalize volume column name
        if 'Volume' in self.profile.columns:
            self.profile = self.profile.rename(columns={'Volume': 'volume', 'Price': 'price'})
            
        avg_vol = self.profile['volume'].mean()
        
        # Identify Nodes
        hvns = self.profile[self.profile['volume'] >= avg_vol * hvn_threshold].copy()
        lvns = self.profile[self.profile['volume'] <= avg_vol * lvn_threshold].copy()
        
        # Cluster Nodes
        hvn_clusters = self._group_into_clusters(hvns)
        lvn_clusters = self._group_into_clusters(lvns)
        
        return {
            'hvn': self._format_nodes(hvns, 'HVN'),
            'lvn': self._format_nodes(lvns, 'LVN'),
            'hvn_clusters': hvn_clusters,
            'lvn_clusters': lvn_clusters,
            'average_volume': avg_vol
        }
        
    def identify_breakout_zones(self) -> List[Dict]:
        """
        Identify breakout zones: LVN clusters sandwiched between HVN clusters.
        """
        nodes = self.find_all_nodes()
        if not nodes['hvn_clusters'] or not nodes['lvn_clusters']:
            return []
            
        breakout_zones = []
        hvns = sorted(nodes['hvn_clusters'], key=lambda x: x['price_center'])
        lvns = sorted(nodes['lvn_clusters'], key=lambda x: x['price_center'])
        
        for lvn in lvns:
            p = lvn['price_center']
            
            # Find nearest HVN below and above
            below = [h for h in hvns if h['price_high'] < p]
            above = [h for h in hvns if h['price_low'] > p]
            
            if below and above:
                supp = below[-1] # Closest below
                res = above[0]   # Closest above
                
                breakout_zones.append({
                    'price': p,
                    'support': supp['price_high'],
                    'resistance': res['price_low'],
                    'width': res['price_low'] - supp['price_high'],
                    'strength': 100 - lvn['strength'], # Lower volume = Higher breakout potential
                    'interpretation': "Breakout Zone (Gap between HVNs)"
                })
                
        return breakout_zones

    def _group_into_clusters(self, nodes_df: pd.DataFrame, gap_threshold: float = 0.05) -> List[Dict]:
        """Group nearby nodes."""
        if nodes_df.empty: return []
        
        nodes = nodes_df.sort_values('price').to_dict('records')
        clusters = []
        current = [nodes[0]]
        
        for i in range(1, len(nodes)):
            prev = current[-1]
            curr = nodes[i]
            
            # Check price gap (absolute or relative)
            # Using relative check might catch huge gaps in high price stocks
            # But simple absolute difference logic usually works for contiguous profile rows
            # If nodes are from contiguous profile bins, gap is just bin size.
            # We assume if they are close, they are one cluster.
            
            if (curr['price'] - prev['price']) / prev['price'] < 0.01: # 1% gap allowed? usually much tighter for profile bins
                current.append(curr)
            else:
                clusters.append(self._summarize_cluster(current))
                current = [curr]
                
        clusters.append(self._summarize_cluster(current))
        return clusters
        
    def _summarize_cluster(self, cluster: List) -> Dict:
        prices = [n['price'] for n in cluster]
        vols = [n['volume'] for n in cluster]
        return {
            'price_low': min(prices),
            'price_high': max(prices),
            'price_center': np.mean(prices),
            'total_volume': sum(vols),
            'strength': min(100, len(cluster) * 5) # Heuristic
        }

    def _format_nodes(self, df: pd.DataFrame, type_str: str) -> List[Dict]:
        res = []
        for _, row in df.iterrows():
            res.append({
                'price': row['price'],
                'volume': row['volume'],
                'type': type_str
            })
        return res
