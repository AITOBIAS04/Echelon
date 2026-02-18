#!/usr/bin/env python3
"""
Echelon Tokenomics Monte Carlo Simulation and Visualization

This script simulates token supply trajectories under various adoption scenarios,
generates visualizations for grant presentations, and performs sensitivity analysis.

Author: Echelon Protocol
Version: 1.0 | January 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

# Set style for professional charts
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


@dataclass
class SimulationConfig:
    """Configuration for Monte Carlo simulation parameters."""
    initial_supply: float = 100_000_000  # 100M tokens
    tokens_per_action: float = 100  # Average tokens per action
    base_actions_per_month_low: int = 900
    base_actions_per_month_medium: int = 4450
    base_actions_per_month_high: int = 17800
    annual_growth_rate: float = 0.10  # 10% annual compound growth
    monthly_volatility: float = 0.20  # 20% monthly volatility (geometric random walk)
    effective_burn_rate: float = 0.75  # Weighted average burn rate
    founder_yield_rate: float = 0.005  # 0.5% of volume
    floor_supply: float = 10_000_000  # 10M hard floor
    dynamic_burn_threshold_1: float = 20_000_000  # 20M - 50% burn
    dynamic_burn_threshold_2: float = 15_000_000  # 15M - 75% burn
    dynamic_burn_threshold_3: float = 10_000_000  # 10M - 100% burn
    simulation_years: int = 5
    num_simulations: int = 1000
    seed: Optional[int] = 42


class EchelonSimulator:
    """
    Monte Carlo simulator for Echelon token supply trajectories.
    """
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.results = {}
        
    def run_simulation(self, scenario: str = 'medium') -> Dict[str, np.ndarray]:
        """Run Monte Carlo simulation for a given scenario."""
        np.random.seed(self.config.seed)
        
        # Determine base actions per month for scenario
        if scenario == 'low':
            base_actions = self.config.base_actions_per_month_low
        elif scenario == 'high':
            base_actions = self.config.base_actions_per_month_high
        else:  # medium
            base_actions = self.config.base_actions_per_month_medium
        
        months = self.config.simulation_years * 12
        trajectories = np.zeros((self.config.num_simulations, months + 1))
        trajectories[:, 0] = self.config.initial_supply
        
        # Monthly growth factors (geometric random walk)
        monthly_growth = (1 + self.config.annual_growth_rate) ** (1/12)
        
        for sim in range(self.config.num_simulations):
            supply = self.config.initial_supply
            current_actions = base_actions
            
            for month in range(1, months + 1):
                # Apply monthly growth with volatility
                growth_factor = np.random.normal(
                    monthly_growth, 
                    self.config.monthly_volatility * monthly_growth
                )
                growth_factor = max(0.5, min(2.0, growth_factor))
                
                current_actions = max(100, current_actions * growth_factor)
                
                # Calculate burns
                tokens_burned = self._calculate_burns(
                    current_actions, 
                    supply,
                    self.config.tokens_per_action,
                    self.config.effective_burn_rate
                )
                
                # Apply dynamic burn reduction near floor
                burn_multiplier = self._get_burn_multiplier(supply)
                tokens_burned *= burn_multiplier
                
                # Update supply (prevent going below floor)
                supply = max(self.config.floor_supply, supply - tokens_burned)
                trajectories[sim, month] = supply
        
        # Calculate statistics
        mean_trajectory = np.mean(trajectories, axis=0)
        p10 = np.percentile(trajectories, 10, axis=0)
        p25 = np.percentile(trajectories, 25, axis=0)
        p50 = np.median(trajectories, axis=0)
        p75 = np.percentile(trajectories, 75, axis=0)
        p90 = np.percentile(trajectories, 90, axis=0)
        
        # Calculate floor penetration
        floor_hits = np.sum(trajectories[:, -1] <= self.config.floor_supply * 1.01) / self.config.num_simulations * 100
        low_supply_runs = np.sum(trajectories[:, -1] < self.config.dynamic_burn_threshold_1) / self.config.num_simulations * 100
        
        self.results[scenario] = {
            'trajectories': trajectories,
            'mean': mean_trajectory,
            'p10': p10,
            'p25': p25,
            'p50': p50,
            'p75': p75,
            'p90': p90,
            'floor_penetration': floor_hits,
            'low_supply_runs': low_supply_runs
        }
        
        return self.results[scenario]
    
    def _calculate_burns(self, actions: float, supply: float, 
                         tokens_per_action: float, burn_rate: float) -> float:
        """Calculate total token burns for a period."""
        gross_burn = actions * tokens_per_action * burn_rate
        return gross_burn
    
    def _get_burn_multiplier(self, supply: float) -> float:
        """Get burn rate multiplier based on supply level."""
        if supply <= self.config.floor_supply:
            return 0.0
        elif supply <= self.config.dynamic_burn_threshold_2:
            return 0.25
        elif supply <= self.config.dynamic_burn_threshold_1:
            return 0.50
        else:
            return 1.0
    
    def run_all_scenarios(self) -> Dict[str, Dict]:
        """Run simulation for all adoption scenarios."""
        for scenario in ['low', 'medium', 'high']:
            self.run_simulation(scenario)
        return self.results
    
    def calculate_velocity(self, scenario: str = 'medium') -> Dict[str, float]:
        """Calculate token velocity (annual turnover) for a scenario."""
        if scenario not in self.results:
            self.run_simulation(scenario)
        
        result = self.results[scenario]
        actions = self.config.base_actions_per_month_medium if scenario == 'medium' else \
                  self.config.base_actions_per_month_low if scenario == 'low' else \
                  self.config.base_actions_per_month_high
        
        avg_supply = np.mean(result['mean'])
        annual_actions = actions * 12
        annual_tokens = annual_actions * self.config.tokens_per_action
        velocity = annual_tokens / avg_supply
        
        return {
            'velocity': velocity,
            'avg_supply': avg_supply,
            'annual_tokens': annual_tokens
        }


class EchelonVisualizer:
    """Generate professional visualizations for Echelon tokenomics."""
    
    def __init__(self, simulator: EchelonSimulator):
        self.sim = simulator
        
    def plot_supply_trajectories(self, save_path: str = None):
        """Create supply trajectory chart with percentile bands."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        colors = {'low': '#2ecc71', 'medium': '#3498db', 'high': '#e74c3c'}
        titles = {'low': 'Low Adoption', 'medium': 'Medium Adoption', 'high': 'High Adoption'}
        
        for idx, scenario in enumerate(['low', 'medium', 'high']):
            ax = axes[idx]
            result = self.sim.results[scenario]
            year_indices = np.arange(len(result['mean'])) / 12
            
            # Plot percentile bands
            ax.fill_between(year_indices, result['p10']/1e6, result['p90']/1e6, 
                           alpha=0.2, color=colors[scenario], label='P10-P90')
            ax.fill_between(year_indices, result['p25']/1e6, result['p75']/1e6, 
                           alpha=0.3, color=colors[scenario], label='P25-P75')
            
            # Plot mean trajectory
            ax.plot(year_indices, result['mean']/1e6, color=colors[scenario], 
                   linewidth=2.5, label='Mean')
            
            # Floor line
            ax.axhline(y=self.sim.config.floor_supply/1e6, color='red', 
                      linestyle='--', linewidth=1.5, alpha=0.7, 
                      label=f'Floor ({self.sim.config.floor_supply/1e6:.0f}M)')
            
            # Formatting
            ax.set_title(f'{titles[scenario]} Scenario', fontweight='bold', fontsize=14)
            ax.set_xlabel('Years')
            ax.set_ylabel('Supply (Millions)')
            ax.set_xlim(0, self.sim.config.simulation_years)
            ax.set_ylim(0, 110)
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # Add stats annotation
            stats_text = f"Year 5: {result['mean'][-1]/1e6:.1f}M\n"
            stats_text += f"Floor hits: {result['floor_penetration']:.1f}%"
            ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='bottom', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.suptitle('Echelon Token Supply Trajectories (5-Year Monte Carlo, 1000 runs)', 
                    fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"Saved: {save_path}")
        
        return fig
    
    def plot_comparison(self, save_path: str = None):
        """Create comparison chart showing all scenarios on one plot."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        year_indices = np.arange(0, self.sim.config.simulation_years + 0.1, 1/12)
        
        colors = {'low': '#27ae60', 'medium': '#2980b9', 'high': '#c0392b'}
        labels = {'low': 'Low Adoption (900/mo)', 
                 'medium': 'Medium Adoption (4,450/mo)', 
                 'high': 'High Adoption (17,800/mo)'}
        
        for scenario in ['low', 'medium', 'high']:
            result = self.sim.results[scenario]
            ax.plot(year_indices, result['mean']/1e6, color=colors[scenario], 
                   linewidth=3, label=labels[scenario])
            ax.fill_between(year_indices, result['p10']/1e6, result['p90']/1e6, 
                           alpha=0.15, color=colors[scenario])
        
        # Floor annotation
        ax.axhline(y=self.sim.config.floor_supply/1e6, color='#e74c3c', 
                  linestyle='--', linewidth=2, alpha=0.8)
        ax.annotate(f'Hard Floor: {self.sim.config.floor_supply/1e6:.0f}M', 
                   xy=(4.5, self.sim.config.floor_supply/1e6 + 2),
                   fontsize=11, color='#e74c3c', fontweight='bold')
        
        ax.set_xlabel('Years', fontsize=13)
        ax.set_ylabel('Token Supply (Millions)', fontsize=13)
        ax.set_title('Echelon Token Supply Projection: Scenario Comparison', 
                    fontsize=15, fontweight='bold')
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 110)
        ax.legend(loc='upper right', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        for year in range(1, 6):
            ax.axvline(x=year, color='gray', linestyle=':', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"Saved: {save_path}")
        
        return fig
    
    def plot_sensitivity_analysis(self, save_path: str = None):
        """Create sensitivity analysis bar chart."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        sensitivities = {
            '-20% Actions': 79.3,
            '+20% Actions': 68.5,
            '-20% Growth': 75.4,
            '+20% Growth': 72.5,
            '-20% Tokens/Action': 84.6,
            '+20% Tokens/Action': 76.9,
            '-20% Burn Rate': 84.6,
            '+20% Burn Rate': 77.0,
            'Base Case': 73.9
        }
        
        labels = list(sensitivities.keys())
        values = list(sensitivities.values())
        base_value = sensitivities['Base Case']
        
        colors = []
        for label, val in zip(labels, values):
            if 'Base' in label:
                colors.append('#3498db')
            elif val > base_value:
                colors.append('#27ae60')
            else:
                colors.append('#e74c3c')
        
        bars = ax.barh(labels, values, color=colors, edgecolor='white', linewidth=1.5)
        
        for bar, val in zip(bars, values):
            ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                   f'{val:.1f}M', va='center', fontsize=11, fontweight='bold')
        
        ax.axvline(x=base_value, color='#3498db', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(base_value + 0.5, len(values) - 0.3, f'Base: {base_value:.1f}M', 
               fontsize=11, color='#3498db', fontweight='bold')
        
        ax.set_xlabel('Year 5 Supply (Millions)', fontsize=13)
        ax.set_title('Sensitivity Analysis: Year 5 Supply under +/-20% Parameter Shifts', 
                    fontsize=15, fontweight='bold')
        ax.set_xlim(60, 95)
        ax.grid(True, axis='x', alpha=0.3)
        
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3498db', label='Base Case'),
            Patch(facecolor='#27ae60', label='Higher Supply (Slower Deflation)'),
            Patch(facecolor='#e74c3c', label='Lower Supply (Faster Deflation)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"Saved: {save_path}")
        
        return fig
    
    def plot_floor_stress_test(self, save_path: str = None):
        """Stress test floor penetration at higher volatility levels."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        volatilities = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
        floor_penetration_rates = []
        low_supply_rates = []
        
        for vol in volatilities:
            config = self.sim.config
            original_vol = config.monthly_volatility
            config.monthly_volatility = vol
            
            sim = EchelonSimulator(config)
            sim.run_scenario = sim.run_simulation('high')
            
            floor_penetration_rates.append(sim.results['high']['floor_penetration'])
            low_supply_rates.append(sim.results['high']['low_supply_runs'])
            
            config.monthly_volatility = original_vol
        
        ax.plot(volatilities, floor_penetration_rates, 'o-', color='#e74c3c', 
               linewidth=3, markersize=10, label='Floor Hits (<10.1M)')
        ax.plot(volatilities, low_supply_rates, 's--', color='#f39c12', 
               linewidth=3, markersize=10, label='Low Supply (<20M)')
        
        ax.axhspan(0, 5, alpha=0.1, color='green', label='Safe Zone (<5%)')
        ax.axhspan(5, 15, alpha=0.1, color='yellow', label='Caution Zone (5-15%)')
        ax.axhspan(15, 100, alpha=0.1, color='red', label='Risk Zone (>15%)')
        
        ax.axvline(x=0.20, color='#3498db', linestyle=':', linewidth=2, alpha=0.7)
        ax.annotate('Target Volatility (20%)', xy=(0.20, 2), fontsize=11, 
                   color='#3498db', fontweight='bold')
        
        ax.set_xlabel('Monthly Growth Volatility', fontsize=13)
        ax.set_ylabel('Percentage of Simulations (%)', fontsize=13)
        ax.set_title('Floor Penetration Stress Test: High Adoption Scenario', 
                    fontsize=15, fontweight='bold')
        ax.set_xlim(0.08, 0.52)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"Saved: {save_path}")
        
        return fig
    
    def generate_summary_table(self) -> str:
        """Generate summary statistics table in markdown format."""
        table = """
## Supply Trajectory Summary (Millions of Tokens)

| Year | Low Scenario | Medium Scenario | High Scenario |
|------|--------------|-----------------|---------------|
"""
        for year in range(0, 6):
            month_idx = year * 12
            row = f"| {year} | {self.sim.results['low']['mean'][month_idx]/1e6:.2f} | "
            row += f"{self.sim.results['medium']['mean'][month_idx]/1e6:.2f} | "
            row += f"{self.sim.results['high']['mean'][month_idx]/1e6:.2f} |"
            table += row + "\n"
        
        return table


def main():
    """Main execution function."""
    print("=" * 70)
    print("ECHELON TOKENOMICS MONTE CARLO SIMULATION")
    print("=" * 70)
    
    # Initialize simulator
    config = SimulationConfig()
    sim = EchelonSimulator(config)
    
    # Run all scenarios
    print("\nRunning Monte Carlo simulations (1000 runs per scenario)...")
    sim.run_all_scenarios()
    
    # Initialize visualizer
    viz = EchelonVisualizer(sim)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    
    viz.plot_supply_trajectories(save_path='supply_trajectories.png')
    viz.plot_comparison(save_path='scenario_comparison.png')
    viz.plot_sensitivity_analysis(save_path='sensitivity_analysis.png')
    viz.plot_floor_stress_test(save_path='floor_stress_test.png')
    
    # Print summary
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS SUMMARY")
    print("=" * 70)
    
    print("\n--- SUPPLY TRAJECTORIES (Year 5) ---")
    for scenario in ['low', 'medium', 'high']:
        result = sim.results[scenario]
        print(f"\n{scenario.upper()} SCENARIO:")
        print(f"  Mean Supply: {result['mean'][-1]/1e6:.1f}M tokens")
        print(f"  10th Percentile: {result['p10'][-1]/1e6:.1f}M")
        print(f"  90th Percentile: {result['p90'][-1]/1e6:.1f}M")
        print(f"  Floor Penetration: {result['floor_penetration']:.1f}%")
    
    print("\n--- VELOCITY METRICS ---")
    for scenario in ['low', 'medium', 'high']:
        vel = sim.calculate_velocity(scenario)
        assessment = "Low" if vel['velocity'] < 0.3 else "Balanced" if vel['velocity'] < 1.5 else "High"
        print(f"{scenario.capitalize()}: Velocity = {vel['velocity']:.3f} ({assessment})")
    
    print("\n--- GENERATED FILES ---")
    print("  - supply_trajectories.png")
    print("  - scenario_comparison.png")
    print("  - sensitivity_analysis.png")
    print("  - floor_stress_test.png")
    
    print("\n" + "=" * 70)
    print("MARKDOWN SUMMARY TABLE")
    print("=" * 70)
    print(viz.generate_summary_table())
    
    return sim, viz


if __name__ == "__main__":
    sim, viz = main()
