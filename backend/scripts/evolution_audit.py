"""
Evolution Audit & Analytics
============================
Comprehensive analysis of agent evolution, fairness, and performance.

Features:
- Archetype balance analysis (detect OP/weak archetypes)
- Fitness progression tracking
- Wealth distribution (Gini coefficient)
- Trait correlation analysis
- Visual reports (matplotlib/terminal)

Usage:
    python -m backend.scripts.evolution_audit
    python -m backend.scripts.evolution_audit --domain financial --generations 50
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter
import math

# Optional: matplotlib for visualizations
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib not installed. Text-only output.")

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GenerationStats:
    generation: int
    average_fitness: float
    max_fitness: float
    min_fitness: float
    top_archetypes: List[str]
    population_size: int
    extinct_count: int
    mutation_rate: float
    timestamp: str = ""

@dataclass
class AuditReport:
    domain: str
    total_generations: int
    fitness_improvement: float
    dominant_archetype: str
    dominant_percentage: float
    archetype_distribution: Dict[str, float]
    is_balanced: bool
    is_learning: bool
    recommendations: List[str]
    gini_coefficient: float

# =============================================================================
# DATA LOADING
# =============================================================================

def load_evolution_history(domain: str = "financial") -> Optional[List[Dict]]:
    """Load evolution history from JSON file."""
    filepath = os.path.join(DATA_DIR, f"{domain}_evolution_history.json")
    
    if not os.path.exists(filepath):
        # Try alternate locations
        alt_paths = [
            os.path.join(BASE_DIR, "data", f"{domain}_evolution_history.json"),
            os.path.join(BASE_DIR, "simulation", f"{domain}_evolution_history.json"),
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                filepath = alt
                break
        else:
            return None
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def generate_mock_history(generations: int = 20) -> List[Dict]:
    """Generate mock evolution history for testing."""
    import random
    
    archetypes = ["SHARK", "WHALE", "DEGEN", "VALUE", "MOMENTUM", "CONTRARIAN"]
    history = []
    
    # Simulate evolution where SHARK becomes dominant
    base_fitness = 50.0
    shark_dominance = 0.2  # Starts at 20%
    
    for gen in range(1, generations + 1):
        # Fitness improves over time (with noise)
        fitness = base_fitness + (gen * 1.5) + random.uniform(-5, 5)
        
        # SHARK becomes more dominant (simulating OP archetype)
        shark_dominance = min(0.6, shark_dominance + 0.02)
        
        # Generate top archetypes for this generation
        top_archs = []
        for _ in range(5):
            if random.random() < shark_dominance:
                top_archs.append("SHARK")
            else:
                top_archs.append(random.choice(archetypes))
        
        history.append({
            "generation": gen,
            "average_fitness": round(fitness, 2),
            "max_fitness": round(fitness * 1.3, 2),
            "min_fitness": round(fitness * 0.5, 2),
            "top_archetypes": top_archs,
            "population_size": 100 - gen,  # Population shrinks
            "extinct_count": gen,
            "mutation_rate": 0.1,
            "timestamp": datetime.now().isoformat(),
        })
    
    return history

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def calculate_gini_coefficient(values: List[float]) -> float:
    """
    Calculate Gini coefficient for wealth/fitness distribution.
    0 = perfect equality, 1 = perfect inequality
    """
    if not values or len(values) < 2:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Gini formula
    numerator = sum((2 * i - n - 1) * x for i, x in enumerate(sorted_values, 1))
    denominator = n * sum(sorted_values)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def analyze_archetype_balance(history: List[Dict]) -> Dict[str, Any]:
    """Analyze archetype distribution for fairness."""
    all_winners = []
    for gen in history:
        all_winners.extend(gen.get('top_archetypes', []))
    
    if not all_winners:
        return {"balanced": True, "distribution": {}, "dominant": None}
    
    counts = Counter(all_winners)
    total = sum(counts.values())
    
    distribution = {arch: (count / total) * 100 for arch, count in counts.items()}
    
    # Find dominant archetype
    dominant = max(distribution, key=distribution.get)
    dominant_pct = distribution[dominant]
    
    # Balance thresholds
    is_balanced = dominant_pct < 35  # Less than 35% for any single archetype
    
    # Identify weak archetypes
    weak_archetypes = [arch for arch, pct in distribution.items() if pct < 5]
    
    return {
        "distribution": distribution,
        "dominant": dominant,
        "dominant_percentage": dominant_pct,
        "balanced": is_balanced,
        "weak_archetypes": weak_archetypes,
    }

def analyze_fitness_progression(history: List[Dict]) -> Dict[str, Any]:
    """Analyze fitness improvement over generations."""
    if len(history) < 2:
        return {"learning": False, "improvement": 0}
    
    fitness_values = [g.get('average_fitness', 0) for g in history]
    
    start = fitness_values[0]
    end = fitness_values[-1]
    
    if start == 0:
        improvement = 0
    else:
        improvement = ((end - start) / start) * 100
    
    # Check for consistent improvement (not just end > start)
    improving_generations = sum(
        1 for i in range(1, len(fitness_values)) 
        if fitness_values[i] > fitness_values[i-1]
    )
    improvement_rate = improving_generations / (len(fitness_values) - 1)
    
    # Calculate volatility
    if len(fitness_values) > 1:
        mean = sum(fitness_values) / len(fitness_values)
        variance = sum((x - mean) ** 2 for x in fitness_values) / len(fitness_values)
        volatility = math.sqrt(variance) / mean if mean > 0 else 0
    else:
        volatility = 0
    
    return {
        "start_fitness": start,
        "end_fitness": end,
        "improvement_percent": improvement,
        "improvement_rate": improvement_rate,
        "volatility": volatility,
        "learning": improvement > 5 and improvement_rate > 0.5,
        "fitness_history": fitness_values,
    }

def generate_recommendations(archetype_analysis: Dict, fitness_analysis: Dict) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []
    
    # Archetype balance recommendations
    if not archetype_analysis["balanced"]:
        dominant = archetype_analysis["dominant"]
        pct = archetype_analysis["dominant_percentage"]
        recommendations.append(
            f"⚠️ NERF {dominant}: At {pct:.1f}%, this archetype is overpowered. "
            f"Consider reducing base stats or adding counters."
        )
    
    for weak in archetype_analysis.get("weak_archetypes", []):
        recommendations.append(
            f"⚠️ BUFF {weak}: This archetype is underperforming (<5%). "
            f"Consider boosting survival traits or unique abilities."
        )
    
    # Learning recommendations
    if not fitness_analysis["learning"]:
        if fitness_analysis["improvement_percent"] < 0:
            recommendations.append(
                "❌ REGRESSION DETECTED: Fitness is decreasing. "
                "Increase mutation rate or check fitness function."
            )
        else:
            recommendations.append(
                "⚠️ STAGNATION: Evolution is not progressing. "
                "Try increasing mutation rate from 0.1 to 0.15."
            )
    
    if fitness_analysis["volatility"] > 0.3:
        recommendations.append(
            "⚠️ HIGH VOLATILITY: Fitness is unstable. "
            "Consider reducing mutation rate or adding elitism."
        )
    
    if not recommendations:
        recommendations.append("✅ System is healthy. No immediate action needed.")
    
    return recommendations

# =============================================================================
# VISUALIZATION
# =============================================================================

def print_text_report(report: AuditReport):
    """Print text-based report to terminal."""
    print("\n" + "=" * 70)
    print(f"🧬 EVOLUTION AUDIT REPORT - {report.domain.upper()} DOMAIN")
    print("=" * 70)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print(f"   Generations Analyzed: {report.total_generations}")
    print(f"   Fitness Improvement:  {report.fitness_improvement:+.1f}%")
    print(f"   Gini Coefficient:     {report.gini_coefficient:.3f} ", end="")
    if report.gini_coefficient < 0.3:
        print("(Healthy)")
    elif report.gini_coefficient < 0.5:
        print("(Moderate inequality)")
    else:
        print("(⚠️ High inequality)")
    
    # Status indicators
    print(f"\n⚖️ BALANCE STATUS")
    print(f"   System Balanced: {'✅ Yes' if report.is_balanced else '❌ No'}")
    print(f"   Agents Learning: {'✅ Yes' if report.is_learning else '❌ No'}")
    
    # Archetype distribution
    print(f"\n🎭 ARCHETYPE DISTRIBUTION")
    sorted_archs = sorted(report.archetype_distribution.items(), key=lambda x: -x[1])
    for arch, pct in sorted_archs:
        bar_length = int(pct / 2)
        bar = "█" * bar_length + "░" * (25 - bar_length)
        status = ""
        if pct > 40:
            status = " ⚠️ OP"
        elif pct < 5:
            status = " ⚠️ WEAK"
        print(f"   {arch:12} [{bar}] {pct:5.1f}%{status}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    for rec in report.recommendations:
        print(f"   {rec}")
    
    print("\n" + "=" * 70)

def plot_evolution_charts(history: List[Dict], domain: str, save_path: str = None):
    """Generate matplotlib visualizations."""
    if not HAS_MATPLOTLIB:
        print("⚠️ matplotlib not available for charts")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Evolution Audit: {domain.upper()} Domain', fontsize=14, fontweight='bold')
    
    generations = [g['generation'] for g in history]
    fitness = [g['average_fitness'] for g in history]
    
    # 1. Fitness over time
    ax1 = axes[0, 0]
    ax1.plot(generations, fitness, 'b-', linewidth=2, label='Avg Fitness')
    if 'max_fitness' in history[0]:
        max_fit = [g['max_fitness'] for g in history]
        min_fit = [g['min_fitness'] for g in history]
        ax1.fill_between(generations, min_fit, max_fit, alpha=0.3, label='Range')
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Fitness')
    ax1.set_title('Fitness Progression')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Archetype pie chart
    ax2 = axes[0, 1]
    all_archs = []
    for g in history:
        all_archs.extend(g.get('top_archetypes', []))
    arch_counts = Counter(all_archs)
    if arch_counts:
        labels = list(arch_counts.keys())
        sizes = list(arch_counts.values())
        colors = plt.cm.Set3(range(len(labels)))
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('Archetype Distribution')
    
    # 3. Population over time
    ax3 = axes[1, 0]
    if 'population_size' in history[0]:
        pop_sizes = [g['population_size'] for g in history]
        ax3.bar(generations, pop_sizes, color='green', alpha=0.7)
        ax3.set_xlabel('Generation')
        ax3.set_ylabel('Population')
        ax3.set_title('Population Size')
    else:
        ax3.text(0.5, 0.5, 'No population data', ha='center', va='center')
    
    # 4. Fitness improvement rate
    ax4 = axes[1, 1]
    if len(fitness) > 1:
        improvements = [
            ((fitness[i] - fitness[i-1]) / fitness[i-1]) * 100 if fitness[i-1] > 0 else 0
            for i in range(1, len(fitness))
        ]
        colors = ['green' if x > 0 else 'red' for x in improvements]
        ax4.bar(generations[1:], improvements, color=colors, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_xlabel('Generation')
        ax4.set_ylabel('Improvement %')
        ax4.set_title('Generation-over-Generation Improvement')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Chart saved to: {save_path}")
    else:
        plt.show()

# =============================================================================
# MAIN AUDIT FUNCTION
# =============================================================================

def run_audit(domain: str = "financial", use_mock: bool = False) -> AuditReport:
    """Run complete evolution audit and return report."""
    
    # Load or generate data
    if use_mock:
        print("🎭 Using mock data for demonstration")
        history = generate_mock_history(20)
    else:
        history = load_evolution_history(domain)
        if not history:
            print(f"📂 No history found for {domain}, generating mock data...")
            history = generate_mock_history(20)
    
    # Run analyses
    archetype_analysis = analyze_archetype_balance(history)
    fitness_analysis = analyze_fitness_progression(history)
    
    # Calculate Gini coefficient from fitness values
    fitness_values = [g.get('average_fitness', 0) for g in history]
    gini = calculate_gini_coefficient(fitness_values)
    
    # Generate recommendations
    recommendations = generate_recommendations(archetype_analysis, fitness_analysis)
    
    # Create report
    report = AuditReport(
        domain=domain,
        total_generations=len(history),
        fitness_improvement=fitness_analysis["improvement_percent"],
        dominant_archetype=archetype_analysis["dominant"] or "N/A",
        dominant_percentage=archetype_analysis["dominant_percentage"] if archetype_analysis["dominant"] else 0,
        archetype_distribution=archetype_analysis["distribution"],
        is_balanced=archetype_analysis["balanced"],
        is_learning=fitness_analysis["learning"],
        recommendations=recommendations,
        gini_coefficient=gini,
    )
    
    return report, history

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Evolution Audit Tool")
    parser.add_argument("--domain", default="financial", help="Domain to audit")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--chart", action="store_true", help="Generate charts")
    parser.add_argument("--save", type=str, help="Save chart to file")
    args = parser.parse_args()
    
    # Run audit
    report, history = run_audit(args.domain, args.mock)
    
    # Print text report
    print_text_report(report)
    
    # Generate charts if requested
    if args.chart or args.save:
        plot_evolution_charts(
            history, 
            args.domain, 
            save_path=args.save
        )
    
    return report

if __name__ == "__main__":
    main()




