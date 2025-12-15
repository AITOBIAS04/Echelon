"""
Synthetic OSINT Generator
=========================

For budget/concept testing - generates realistic fake OSINT signals
to feed the Situation Room without needing real API subscriptions.

This creates believable:
- Geopolitical events
- Corporate news
- Market movements
- Military activity
- Social unrest signals

Perfect for:
- Demo environments
- Testing mission generation
- Showcasing the platform
- Development without API costs
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from backend.core.mission_generator import OSINTSignal, SignalSource, SignalCategory
except ImportError:
    from backend.core.mission_generator import OSINTSignal, SignalSource, SignalCategory


# =============================================================================
# SYNTHETIC SIGNAL TEMPLATES
# =============================================================================

# Geopolitical Events
GEOPOLITICAL_TEMPLATES = [
    # Taiwan/China
    {
        "headline": "China announces surprise military exercises near Taiwan",
        "summary": "PLA forces begin unscheduled naval drills in Taiwan Strait. Regional tensions escalate as US carrier group monitors situation.",
        "entities": ["China", "Taiwan", "PLA", "US Navy"],
        "base_urgency": 0.8,
        "base_virality": 0.7,
        "sentiment": -0.6,
    },
    {
        "headline": "Taiwan reports record airspace incursions",
        "summary": "{count} Chinese military aircraft entered Taiwan's ADIZ in 24-hour period, highest number this year.",
        "entities": ["Taiwan", "China", "ADIZ"],
        "base_urgency": 0.7,
        "base_virality": 0.6,
        "sentiment": -0.5,
    },
    # Russia/Ukraine
    {
        "headline": "Ukraine claims major gains in {region} offensive",
        "summary": "Ukrainian forces report capturing key positions. Russia denies territorial losses.",
        "entities": ["Ukraine", "Russia", "{region}"],
        "base_urgency": 0.75,
        "base_virality": 0.8,
        "sentiment": 0.3,
    },
    {
        "headline": "NATO announces additional military aid package",
        "summary": "${amount}B in new military assistance approved. Package includes advanced air defense systems.",
        "entities": ["NATO", "Ukraine", "Pentagon"],
        "base_urgency": 0.6,
        "base_virality": 0.65,
        "sentiment": 0.4,
    },
    # Middle East
    {
        "headline": "Iran enrichment levels reach new high",
        "summary": "IAEA reports uranium enrichment at {percent}%, raising concerns about weapons capability.",
        "entities": ["Iran", "IAEA", "Nuclear"],
        "base_urgency": 0.85,
        "base_virality": 0.7,
        "sentiment": -0.7,
    },
    {
        "headline": "Saudi Arabia and Iran hold secret talks",
        "summary": "Sources confirm back-channel negotiations in {location}. Potential regional détente discussed.",
        "entities": ["Saudi Arabia", "Iran", "Diplomacy"],
        "base_urgency": 0.7,
        "base_virality": 0.75,
        "sentiment": 0.5,
    },
    # North Korea
    {
        "headline": "North Korea launches {count} ballistic missiles",
        "summary": "Projectiles flew {distance}km before landing in Sea of Japan. South Korea condemns provocation.",
        "entities": ["North Korea", "South Korea", "Japan", "Missiles"],
        "base_urgency": 0.9,
        "base_virality": 0.85,
        "sentiment": -0.8,
    },
    # Generic tensions
    {
        "headline": "{country_a} recalls ambassador from {country_b}",
        "summary": "Diplomatic crisis escalates over {issue}. Trade talks suspended indefinitely.",
        "entities": ["{country_a}", "{country_b}", "Diplomacy"],
        "base_urgency": 0.65,
        "base_virality": 0.5,
        "sentiment": -0.4,
    },
]

# Corporate/Business Events
CORPORATE_TEMPLATES = [
    {
        "headline": "{company} CEO unexpectedly resigns amid investigation",
        "summary": "Board accepts immediate resignation. Internal probe reportedly uncovered financial irregularities.",
        "entities": ["{company}", "CEO", "Investigation"],
        "base_urgency": 0.8,
        "base_virality": 0.85,
        "sentiment": -0.6,
        "category": SignalCategory.CORPORATE,
    },
    {
        "headline": "Major tech company announces {count},000 layoffs",
        "summary": "{company} cutting {percent}% of workforce. Restructuring expected to save ${amount}B annually.",
        "entities": ["{company}", "Tech", "Layoffs"],
        "base_urgency": 0.7,
        "base_virality": 0.8,
        "sentiment": -0.5,
        "category": SignalCategory.CORPORATE,
    },
    {
        "headline": "Hostile takeover bid launched for {company}",
        "summary": "{acquirer} offers ${amount}B for {company}. Board recommends shareholders reject 'inadequate' offer.",
        "entities": ["{company}", "{acquirer}", "M&A"],
        "base_urgency": 0.75,
        "base_virality": 0.7,
        "sentiment": -0.2,
        "category": SignalCategory.CORPORATE,
    },
    {
        "headline": "Whistleblower alleges fraud at {company}",
        "summary": "Former executive claims systematic accounting manipulation. SEC launches investigation.",
        "entities": ["{company}", "SEC", "Fraud"],
        "base_urgency": 0.85,
        "base_virality": 0.9,
        "sentiment": -0.7,
        "category": SignalCategory.CORPORATE,
    },
    {
        "headline": "{company} announces surprise partnership with {partner}",
        "summary": "Strategic alliance valued at ${amount}B. Combined market cap exceeds ${total}T.",
        "entities": ["{company}", "{partner}", "Partnership"],
        "base_urgency": 0.6,
        "base_virality": 0.75,
        "sentiment": 0.6,
        "category": SignalCategory.CORPORATE,
    },
]

# Economic/Market Events
ECONOMIC_TEMPLATES = [
    {
        "headline": "Oil prices surge {percent}% on supply concerns",
        "summary": "Brent crude jumps to ${price}/barrel. {reason} cited as primary driver.",
        "entities": ["Oil", "OPEC", "Energy"],
        "base_urgency": 0.7,
        "base_virality": 0.65,
        "sentiment": -0.4,
        "category": SignalCategory.ECONOMIC,
    },
    {
        "headline": "Federal Reserve signals surprise rate decision",
        "summary": "Fed officials hint at {direction} policy shift. Markets react with {reaction}.",
        "entities": ["Federal Reserve", "Interest Rates", "Markets"],
        "base_urgency": 0.8,
        "base_virality": 0.75,
        "sentiment": 0.0,
        "category": SignalCategory.ECONOMIC,
    },
    {
        "headline": "{country} currency crashes {percent}% in single session",
        "summary": "Central bank intervention fails to stem decline. IMF monitoring situation closely.",
        "entities": ["{country}", "Currency", "IMF"],
        "base_urgency": 0.85,
        "base_virality": 0.8,
        "sentiment": -0.7,
        "category": SignalCategory.ECONOMIC,
    },
    {
        "headline": "Inflation data surprises: {direction} than expected",
        "summary": "CPI comes in at {percent}%, {comparison} analyst forecasts. Bond markets react sharply.",
        "entities": ["Inflation", "CPI", "Bonds"],
        "base_urgency": 0.75,
        "base_virality": 0.7,
        "sentiment": -0.3,
        "category": SignalCategory.ECONOMIC,
    },
    {
        "headline": "Major bank faces liquidity crisis",
        "summary": "{bank} stock halted after {percent}% drop. Regulators assessing systemic risk.",
        "entities": ["{bank}", "Banking", "Crisis"],
        "base_urgency": 0.9,
        "base_virality": 0.9,
        "sentiment": -0.8,
        "category": SignalCategory.ECONOMIC,
    },
]

# Technology/Cyber Events
TECHNOLOGY_TEMPLATES = [
    {
        "headline": "Major cyberattack hits {target} infrastructure",
        "summary": "Critical systems offline for {hours} hours. State-sponsored actors suspected.",
        "entities": ["{target}", "Cybersecurity", "Infrastructure"],
        "base_urgency": 0.9,
        "base_virality": 0.85,
        "sentiment": -0.7,
        "category": SignalCategory.TECHNOLOGY,
    },
    {
        "headline": "AI breakthrough: {company} announces {capability}",
        "summary": "New model demonstrates {achievement}. Industry experts call it 'paradigm shift'.",
        "entities": ["{company}", "AI", "Technology"],
        "base_urgency": 0.7,
        "base_virality": 0.9,
        "sentiment": 0.6,
        "category": SignalCategory.TECHNOLOGY,
    },
    {
        "headline": "Data breach exposes {count} million users",
        "summary": "{company} confirms unauthorized access. Personal data including {data_types} compromised.",
        "entities": ["{company}", "Data Breach", "Privacy"],
        "base_urgency": 0.8,
        "base_virality": 0.85,
        "sentiment": -0.6,
        "category": SignalCategory.TECHNOLOGY,
    },
]

# Assassination/Mystery Events (for "Who Killed X?" narratives)
MYSTERY_TEMPLATES = [
    {
        "headline": "Prominent {role} found dead in {location}",
        "summary": "{name}, known for {known_for}, discovered under suspicious circumstances. Authorities investigating.",
        "entities": ["{name}", "{location}", "Investigation"],
        "base_urgency": 0.95,
        "base_virality": 0.9,
        "sentiment": -0.9,
        "category": SignalCategory.GEOPOLITICAL,
        "is_mystery": True,
    },
    {
        "headline": "{name} missing after {event}",
        "summary": "Last seen {last_seen}. Associates report concerns about threats received prior to disappearance.",
        "entities": ["{name}", "Missing", "Investigation"],
        "base_urgency": 0.85,
        "base_virality": 0.8,
        "sentiment": -0.7,
        "category": SignalCategory.GEOPOLITICAL,
        "is_mystery": True,
    },
]


# =============================================================================
# VARIABLE POOLS FOR TEMPLATES
# =============================================================================

VARIABLE_POOLS = {
    "company": [
        "Nexus Technologies", "Quantum Dynamics", "Atlas Corp", "Meridian Holdings",
        "Titan Industries", "Apex Systems", "Vanguard Tech", "Phoenix Group",
        "Sterling Partners", "Zenith Capital", "Obsidian Labs", "Prism Innovations",
    ],
    "acquirer": [
        "BlackRock", "Berkshire", "SoftBank", "Sequoia", "Private Equity Consortium",
    ],
    "partner": [
        "Microsoft", "Google", "Amazon", "Apple", "NVIDIA", "Meta", "OpenAI",
    ],
    "country_a": [
        "United States", "China", "Russia", "India", "Turkey", "Brazil",
    ],
    "country_b": [
        "United Kingdom", "France", "Germany", "Japan", "Australia", "Canada",
    ],
    "issue": [
        "territorial disputes", "trade policy", "espionage allegations", 
        "sanctions violations", "human rights concerns",
    ],
    "region": [
        "Kherson", "Zaporizhzhia", "Donetsk", "Luhansk", "Crimea",
    ],
    "location": [
        "Geneva", "Vienna", "Singapore", "Dubai", "Istanbul",
    ],
    "name": [
        "Viktor Petrov", "Elena Vasquez", "James Chen", "Marcus Webb",
        "Alexei Volkov", "Sarah Mitchell", "Omar Hassan", "Yuki Tanaka",
        "Isabella Torres", "Dmitri Sokolov", "Richard Blackwood", "Clara Richter",
    ],
    "role": [
        "oligarch", "intelligence officer", "tech executive", "diplomat",
        "journalist", "banker", "defense contractor", "scientist",
    ],
    "known_for": [
        "opposing the regime", "whistleblowing activities", "controversial deals",
        "intelligence connections", "investigative journalism", "weapons research",
    ],
    "target": [
        "government", "financial", "healthcare", "energy grid", "telecom",
    ],
    "bank": [
        "First Republic", "Silicon Valley Bank", "Credit Suisse", "Deutsche Bank",
    ],
    "capability": [
        "human-level reasoning", "autonomous research", "real-time translation",
        "scientific discovery", "code generation",
    ],
    "achievement": [
        "solving complex problems", "passing expert-level tests",
        "generating novel hypotheses", "autonomous operation",
    ],
    "data_types": [
        "passwords and financial data", "social security numbers",
        "medical records", "private communications",
    ],
    "reason": [
        "OPEC production cuts", "Middle East tensions", "refinery outages",
        "shipping disruptions", "sanctions on Russia",
    ],
    "direction": [
        "hawkish", "dovish", "unexpected", "dramatic",
    ],
    "reaction": [
        "sharp volatility", "relief rally", "panic selling", "cautious optimism",
    ],
    "comparison": [
        "higher than", "lower than", "in line with", "significantly above",
    ],
    "last_seen": [
        "leaving a private meeting", "at an undisclosed airport",
        "entering a foreign embassy", "boarding a yacht",
    ],
    "event": [
        "controversial testimony", "leaked documents publication",
        "secret meeting exposure", "threat allegations",
    ],
}


# =============================================================================
# SYNTHETIC SIGNAL GENERATOR
# =============================================================================

class SyntheticOSINTGenerator:
    """
    Generates realistic fake OSINT signals for testing.
    
    Usage:
        generator = SyntheticOSINTGenerator()
        
        # Generate a single signal
        signal = generator.generate_signal()
        
        # Generate signals of specific type
        signal = generator.generate_signal(category=SignalCategory.GEOPOLITICAL)
        
        # Generate batch
        signals = generator.generate_batch(count=10)
        
        # Generate crisis scenario
        signals = generator.generate_crisis_scenario("taiwan")
    """
    
    def __init__(self, chaos_level: float = 0.5):
        """
        Args:
            chaos_level: 0.0-1.0, higher = more dramatic/urgent signals
        """
        self.chaos_level = chaos_level
        self.generated_count = 0
        self.active_storylines: List[str] = []
    
    def generate_signal(
        self,
        category: Optional[SignalCategory] = None,
        force_high_urgency: bool = False,
        force_mystery: bool = False,
    ) -> OSINTSignal:
        """Generate a single synthetic OSINT signal"""
        
        # Select template pool
        if force_mystery:
            template = random.choice(MYSTERY_TEMPLATES)
            category = SignalCategory.GEOPOLITICAL
        elif category == SignalCategory.CORPORATE:
            template = random.choice(CORPORATE_TEMPLATES)
        elif category == SignalCategory.ECONOMIC:
            template = random.choice(ECONOMIC_TEMPLATES)
        elif category == SignalCategory.TECHNOLOGY:
            template = random.choice(TECHNOLOGY_TEMPLATES)
        else:
            # Mix of all types
            all_templates = (
                GEOPOLITICAL_TEMPLATES + 
                CORPORATE_TEMPLATES + 
                ECONOMIC_TEMPLATES +
                TECHNOLOGY_TEMPLATES
            )
            template = random.choice(all_templates)
            category = template.get("category", SignalCategory.GEOPOLITICAL)
        
        # Fill in template variables
        headline = self._fill_template(template["headline"])
        summary = self._fill_template(template["summary"])
        entities = [self._fill_template(e) for e in template["entities"]]
        
        # Calculate metrics with chaos modifier
        chaos_modifier = random.uniform(0.8, 1.2) * (1 + self.chaos_level * 0.3)
        
        urgency = min(1.0, template["base_urgency"] * chaos_modifier)
        virality = min(1.0, template["base_virality"] * chaos_modifier)
        
        if force_high_urgency:
            urgency = max(urgency, 0.8)
            virality = max(virality, 0.75)
        
        # Create signal
        signal = OSINTSignal(
            source=random.choice([
                SignalSource.NEWS_API,
                SignalSource.TWITTER,
                SignalSource.GOVERNMENT,
            ]),
            headline=headline,
            summary=summary,
            category=category,
            entities=entities,
            urgency=urgency,
            virality_score=virality,
            sentiment=template["sentiment"],
            source_credibility=random.uniform(0.7, 0.95),
        )
        
        self.generated_count += 1
        return signal
    
    def _fill_template(self, text: str) -> str:
        """Fill in template variables with random values"""
        result = text
        
        # Find all {variable} patterns
        import re
        variables = re.findall(r'\{(\w+)\}', text)
        
        for var in variables:
            if var in VARIABLE_POOLS:
                value = random.choice(VARIABLE_POOLS[var])
                result = result.replace(f"{{{var}}}", value, 1)
            elif var == "count":
                result = result.replace("{count}", str(random.randint(3, 50)))
            elif var == "percent":
                result = result.replace("{percent}", f"{random.uniform(2, 15):.1f}")
            elif var == "amount":
                result = result.replace("{amount}", f"{random.uniform(1, 50):.1f}")
            elif var == "price":
                result = result.replace("{price}", str(random.randint(80, 150)))
            elif var == "distance":
                result = result.replace("{distance}", str(random.randint(500, 2000)))
            elif var == "hours":
                result = result.replace("{hours}", str(random.randint(2, 48)))
            elif var == "total":
                result = result.replace("{total}", f"{random.uniform(1, 5):.1f}")
        
        return result
    
    def generate_batch(
        self,
        count: int = 10,
        category_mix: Optional[Dict[SignalCategory, float]] = None
    ) -> List[OSINTSignal]:
        """Generate multiple signals"""
        
        if category_mix is None:
            category_mix = {
                SignalCategory.GEOPOLITICAL: 0.4,
                SignalCategory.CORPORATE: 0.25,
                SignalCategory.ECONOMIC: 0.2,
                SignalCategory.TECHNOLOGY: 0.15,
            }
        
        signals = []
        for _ in range(count):
            # Weighted random category selection
            rand = random.random()
            cumulative = 0
            selected_category = SignalCategory.GEOPOLITICAL
            
            for cat, weight in category_mix.items():
                cumulative += weight
                if rand <= cumulative:
                    selected_category = cat
                    break
            
            signals.append(self.generate_signal(category=selected_category))
        
        return signals
    
    def generate_crisis_scenario(
        self,
        scenario: str = "taiwan"
    ) -> List[OSINTSignal]:
        """
        Generate a series of related signals simulating a crisis.
        Great for testing narrative arc generation.
        """
        
        scenarios = {
            "taiwan": [
                {
                    "headline": "China announces largest military exercise in decades",
                    "summary": "PLA mobilizes forces across Fujian province. Live fire drills scheduled.",
                    "urgency": 0.85, "virality": 0.9,
                },
                {
                    "headline": "US deploys additional carrier group to Western Pacific",
                    "summary": "USS Reagan strike group joins USS Nimitz. Pentagon cites 'regional stability'.",
                    "urgency": 0.8, "virality": 0.85,
                },
                {
                    "headline": "Taiwan activates reserve forces",
                    "summary": "Defense ministry orders partial mobilization. Civil defense drills announced.",
                    "urgency": 0.9, "virality": 0.88,
                },
                {
                    "headline": "Emergency UN Security Council session called",
                    "summary": "Multiple nations request urgent meeting. China threatens veto.",
                    "urgency": 0.85, "virality": 0.8,
                },
                {
                    "headline": "Global markets plunge on Taiwan fears",
                    "summary": "Asian indices down 5%+. Flight to safety as investors dump risk assets.",
                    "urgency": 0.9, "virality": 0.92,
                },
            ],
            "economic_collapse": [
                {
                    "headline": "Major European bank halts withdrawals",
                    "summary": "Liquidity crisis forces emergency measures. ECB monitoring closely.",
                    "urgency": 0.9, "virality": 0.88,
                },
                {
                    "headline": "Contagion fears spread to US regional banks",
                    "summary": "Multiple lenders see deposit flight. FDIC considers emergency action.",
                    "urgency": 0.88, "virality": 0.85,
                },
                {
                    "headline": "Federal Reserve announces emergency rate cut",
                    "summary": "Surprise 50bp cut to stabilize markets. More action promised if needed.",
                    "urgency": 0.85, "virality": 0.9,
                },
                {
                    "headline": "G7 finance ministers hold emergency call",
                    "summary": "Coordinated intervention discussed. Joint statement expected.",
                    "urgency": 0.8, "virality": 0.82,
                },
            ],
            "assassination": [
                {
                    "headline": "Prominent oligarch found dead in London",
                    "summary": "Viktor Petrov discovered in Mayfair residence. Scotland Yard investigating.",
                    "urgency": 0.95, "virality": 0.92,
                },
                {
                    "headline": "Victim had testified against regime",
                    "summary": "Petrov provided evidence to UK inquiry. Security had been increased.",
                    "urgency": 0.85, "virality": 0.88,
                },
                {
                    "headline": "Multiple suspects identified, none apprehended",
                    "summary": "CCTV shows individuals near scene. Some believed to have fled country.",
                    "urgency": 0.8, "virality": 0.85,
                },
                {
                    "headline": "Diplomatic crisis as expulsions begin",
                    "summary": "UK expels 23 diplomats. Retaliation expected within days.",
                    "urgency": 0.85, "virality": 0.87,
                },
            ],
        }
        
        scenario_events = scenarios.get(scenario, scenarios["taiwan"])
        
        signals = []
        for i, event in enumerate(scenario_events):
            signal = OSINTSignal(
                source=SignalSource.NEWS_API,
                headline=event["headline"],
                summary=event["summary"],
                category=SignalCategory.GEOPOLITICAL,
                urgency=event["urgency"],
                virality_score=event["virality"],
                sentiment=-0.7,
                entities=["Crisis", scenario.title()],
                # Stagger timestamps
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=30 * (len(scenario_events) - i)),
            )
            signals.append(signal)
        
        return signals
    
    def generate_mystery_event(self, target_name: Optional[str] = None) -> OSINTSignal:
        """Generate a 'Who Killed X?' style event"""
        return self.generate_signal(force_mystery=True)


# =============================================================================
# SCHEDULED SYNTHETIC FEED
# =============================================================================

class SyntheticOSINTFeed:
    """
    A continuous feed of synthetic OSINT signals.
    Simulates real-world news flow for testing.
    
    Usage:
        feed = SyntheticOSINTFeed(signals_per_minute=2)
        
        async for signal in feed.stream():
            await engine.ingest_signal(signal)
    """
    
    def __init__(
        self,
        signals_per_minute: float = 1.0,
        chaos_level: float = 0.5,
        include_crises: bool = True,
        crisis_probability: float = 0.05,
    ):
        self.generator = SyntheticOSINTGenerator(chaos_level)
        self.signals_per_minute = signals_per_minute
        self.include_crises = include_crises
        self.crisis_probability = crisis_probability
        self.is_running = False
        self.current_crisis: Optional[List[OSINTSignal]] = None
        self.crisis_index = 0
    
    async def stream(self):
        """Async generator that yields signals continuously"""
        self.is_running = True
        interval = 60.0 / self.signals_per_minute
        
        while self.is_running:
            # Check for ongoing crisis
            if self.current_crisis and self.crisis_index < len(self.current_crisis):
                signal = self.current_crisis[self.crisis_index]
                self.crisis_index += 1
                yield signal
            else:
                # Maybe start new crisis
                if self.include_crises and random.random() < self.crisis_probability:
                    crisis_type = random.choice(["taiwan", "economic_collapse", "assassination"])
                    self.current_crisis = self.generator.generate_crisis_scenario(crisis_type)
                    self.crisis_index = 0
                    print(f"🚨 CRISIS SCENARIO TRIGGERED: {crisis_type}")
                else:
                    # Normal signal
                    yield self.generator.generate_signal()
            
            await asyncio.sleep(interval)
    
    def stop(self):
        self.is_running = False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_test_signals(count: int = 10) -> List[OSINTSignal]:
    """Quick way to get test signals"""
    generator = SyntheticOSINTGenerator()
    return generator.generate_batch(count)


def get_crisis_signals(scenario: str = "taiwan") -> List[OSINTSignal]:
    """Quick way to get a crisis scenario"""
    generator = SyntheticOSINTGenerator()
    return generator.generate_crisis_scenario(scenario)


def get_mystery_signal() -> OSINTSignal:
    """Quick way to get a mystery event"""
    generator = SyntheticOSINTGenerator()
    return generator.generate_mystery_event()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def demo_synthetic_feed():
    """Demo the synthetic OSINT feed"""
    print("=" * 60)
    print("📡 SYNTHETIC OSINT FEED DEMO")
    print("=" * 60)
    
    generator = SyntheticOSINTGenerator(chaos_level=0.6)
    
    # Generate some signals
    print("\n📰 Random Signals:")
    for _ in range(5):
        signal = generator.generate_signal()
        print(f"  [{signal.category.value}] {signal.headline[:60]}...")
        print(f"     Urgency: {signal.urgency:.0%} | Virality: {signal.virality_score:.0%}")
    
    # Generate a crisis
    print("\n🚨 Crisis Scenario (Taiwan):")
    crisis = generator.generate_crisis_scenario("taiwan")
    for signal in crisis:
        print(f"  → {signal.headline[:60]}...")
    
    # Generate mystery
    print("\n🔍 Mystery Event:")
    mystery = generator.generate_mystery_event()
    print(f"  {mystery.headline}")
    print(f"  {mystery.summary}")


if __name__ == "__main__":
    asyncio.run(demo_synthetic_feed())

