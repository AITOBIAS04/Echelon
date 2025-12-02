"""
Narrative War System
====================

The battle between TRUTH and PROPAGANDA.

Journalists:
- Earn reputation for accurate reporting
- Fact-check signals
- Expose fake news
- High reputation = influence over Global Tension gauge

Propagandists:
- Spin narratives
- Amplify or suppress signals
- Create disinformation
- Risk reputation if caught

This creates the "Truth vs Hype" betting market mechanic.
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from backend.core.models import AgentRole, Faction, SpecialAbility
    from backend.core.mission_generator import OSINTSignal, SignalCategory
except ImportError:
    from core.models import AgentRole, Faction, SpecialAbility
    from core.mission_generator import OSINTSignal, SignalCategory


# =============================================================================
# NARRATIVE WAR DATA MODELS
# =============================================================================

class NarrativeStance(Enum):
    """The angle being pushed on a signal/story"""
    TRUTH = "truth"              # Accurate, verified reporting
    BULLISH_SPIN = "bullish"     # Positive spin on events
    BEARISH_SPIN = "bearish"     # Negative/fear-inducing spin
    NEUTRAL = "neutral"          # Balanced reporting
    DISINFORMATION = "disinfo"   # Outright false


@dataclass
class NarrativeReport:
    """A report/interpretation of an OSINT signal"""
    id: str = field(default_factory=lambda: f"report-{random.randint(1000,9999)}")
    
    # Source
    signal_id: str = ""
    original_headline: str = ""
    
    # Report
    author_agent_id: str = ""
    author_role: AgentRole = AgentRole.JOURNALIST
    author_faction: Optional[Faction] = None
    
    # Content
    reported_headline: str = ""
    reported_summary: str = ""
    stance: NarrativeStance = NarrativeStance.NEUTRAL
    
    # Truth metrics
    factual_accuracy: float = 1.0      # 0-1, how accurate is this report
    spin_factor: float = 0.0           # 0-1, how much spin applied
    is_disinformation: bool = False
    
    # Impact
    virality_modifier: float = 0.0     # How much this changed virality
    sentiment_modifier: float = 0.0     # How much this changed sentiment
    tension_impact: float = 0.0         # Impact on global tension
    
    # Verification
    is_verified: bool = False
    verified_by: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    
    # Stats
    views: int = 0
    shares: int = 0
    credibility_score: float = 0.5
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TruthMarket:
    """
    A betting market on whether a story is TRUE or HYPE.
    Resolves when a Journalist fact-checks it.
    """
    id: str = field(default_factory=lambda: f"truth-{random.randint(1000,9999)}")
    
    # Story
    signal_id: str = ""
    headline: str = ""
    
    # Market state
    truth_pool: float = 0.0         # USDC bet on TRUTH
    hype_pool: float = 0.0          # USDC bet on HYPE
    
    # Odds
    truth_probability: float = 0.5
    
    # Resolution
    is_resolved: bool = False
    actual_outcome: Optional[str] = None  # "truth" or "hype"
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closes_at: Optional[datetime] = None
    
    def get_odds(self) -> Dict[str, float]:
        """Get current betting odds"""
        total = self.truth_pool + self.hype_pool
        if total == 0:
            return {"truth": 0.5, "hype": 0.5}
        return {
            "truth": self.truth_pool / total,
            "hype": self.hype_pool / total,
        }


@dataclass
class ReputationScore:
    """Tracks an agent's reputation in the Narrative War"""
    agent_id: str = ""
    role: AgentRole = AgentRole.JOURNALIST
    
    # Core reputation (0-100)
    credibility: int = 50           # How trusted are their reports
    influence: int = 50             # How much impact do they have
    accuracy: int = 50              # Track record of being correct
    
    # History
    reports_published: int = 0
    reports_verified_true: int = 0
    reports_verified_false: int = 0
    fake_news_exposed: int = 0      # For journalists
    fake_news_created: int = 0      # For propagandists
    
    # Calculated
    @property
    def overall_score(self) -> int:
        return (self.credibility + self.influence + self.accuracy) // 3
    
    @property
    def accuracy_rate(self) -> float:
        total = self.reports_verified_true + self.reports_verified_false
        if total == 0:
            return 0.5
        return self.reports_verified_true / total


# =============================================================================
# NARRATIVE WAR ENGINE
# =============================================================================

class NarrativeWarEngine:
    """
    Manages the Journalist vs Propagandist battle.
    
    Features:
    - Journalists publish accurate reports, earn reputation
    - Propagandists spin/fake news, risk getting caught
    - Truth Markets let users bet on story accuracy
    - Tension gauge influenced by high-rep agents
    """
    
    def __init__(self):
        self.reports: Dict[str, NarrativeReport] = {}
        self.truth_markets: Dict[str, TruthMarket] = {}
        self.reputation_scores: Dict[str, ReputationScore] = {}
        
        # Track signal narratives
        self.signal_narratives: Dict[str, List[str]] = {}  # signal_id -> report_ids
        
        # Fake signals that have been injected
        self.fake_signal_ids: set = set()
    
    # =========================================================================
    # JOURNALIST ACTIONS
    # =========================================================================
    
    def publish_report(
        self,
        agent_id: str,
        signal: OSINTSignal,
        headline: Optional[str] = None,
        summary: Optional[str] = None,
        stance: NarrativeStance = NarrativeStance.TRUTH,
        agent_role: AgentRole = AgentRole.JOURNALIST,
        agent_faction: Optional[Faction] = None,
    ) -> NarrativeReport:
        """
        Journalist or Propagandist publishes a report on a signal.
        
        Journalists should use TRUTH stance.
        Propagandists might SPIN or use DISINFORMATION.
        """
        # Determine if this is accurate
        is_fake_signal = signal.id in self.fake_signal_ids
        
        report = NarrativeReport(
            signal_id=signal.id,
            original_headline=signal.headline,
            author_agent_id=agent_id,
            author_role=agent_role,
            author_faction=agent_faction,
            reported_headline=headline or signal.headline,
            reported_summary=summary or signal.summary,
            stance=stance,
        )
        
        # Calculate accuracy based on stance and signal truth
        if stance == NarrativeStance.TRUTH:
            report.factual_accuracy = 0.0 if is_fake_signal else 0.95
            report.spin_factor = 0.0
        elif stance == NarrativeStance.DISINFORMATION:
            report.factual_accuracy = 0.1
            report.spin_factor = 0.9
            report.is_disinformation = True
        else:  # BULLISH or BEARISH spin
            report.factual_accuracy = 0.5 if is_fake_signal else 0.7
            report.spin_factor = 0.4
        
        # Calculate impact
        rep_score = self._get_or_create_reputation(agent_id, agent_role)
        influence_multiplier = rep_score.influence / 100
        
        if stance == NarrativeStance.BULLISH_SPIN:
            report.sentiment_modifier = 0.2 * influence_multiplier
            report.tension_impact = -0.05 * influence_multiplier
        elif stance == NarrativeStance.BEARISH_SPIN:
            report.sentiment_modifier = -0.3 * influence_multiplier
            report.tension_impact = 0.1 * influence_multiplier
        elif stance == NarrativeStance.DISINFORMATION:
            report.sentiment_modifier = random.uniform(-0.4, 0.4)
            report.tension_impact = 0.15 * influence_multiplier
        
        # Initial credibility based on author reputation
        report.credibility_score = rep_score.credibility / 100
        
        # Store
        self.reports[report.id] = report
        
        if signal.id not in self.signal_narratives:
            self.signal_narratives[signal.id] = []
        self.signal_narratives[signal.id].append(report.id)
        
        # Update author stats
        rep_score.reports_published += 1
        if report.is_disinformation:
            rep_score.fake_news_created += 1
        
        return report
    
    def fact_check(
        self,
        agent_id: str,
        report_id: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Journalist fact-checks a report.
        Uses FACT_CHECK ability.
        
        Returns (is_accurate, details)
        """
        report = self.reports.get(report_id)
        if not report:
            return False, {"error": "Report not found"}
        
        if report.is_verified:
            return report.factual_accuracy > 0.5, {"already_verified": True}
        
        # Verification result
        is_accurate = report.factual_accuracy > 0.5
        
        report.is_verified = True
        report.verified_by = agent_id
        report.verification_timestamp = datetime.now(timezone.utc)
        
        # Update reputations
        fact_checker_rep = self._get_or_create_reputation(agent_id, AgentRole.JOURNALIST)
        author_rep = self._get_or_create_reputation(report.author_agent_id, report.author_role)
        
        if is_accurate:
            author_rep.reports_verified_true += 1
            author_rep.accuracy = min(100, author_rep.accuracy + 2)
            author_rep.credibility = min(100, author_rep.credibility + 1)
        else:
            author_rep.reports_verified_false += 1
            author_rep.accuracy = max(0, author_rep.accuracy - 5)
            author_rep.credibility = max(0, author_rep.credibility - 10)
            fact_checker_rep.fake_news_exposed += 1
            fact_checker_rep.influence = min(100, fact_checker_rep.influence + 3)
        
        # Resolve associated truth market
        self._resolve_truth_market(report.signal_id, is_accurate)
        
        return is_accurate, {
            "report_id": report_id,
            "is_accurate": is_accurate,
            "factual_accuracy": report.factual_accuracy,
            "author": report.author_agent_id,
            "was_disinfo": report.is_disinformation,
        }
    
    # =========================================================================
    # PROPAGANDIST ACTIONS
    # =========================================================================
    
    def spin_narrative(
        self,
        agent_id: str,
        signal: OSINTSignal,
        spin_direction: str = "bearish",  # "bullish" or "bearish"
        intensity: float = 0.5,  # 0-1
    ) -> NarrativeReport:
        """
        Propagandist spins a narrative on a signal.
        Uses SPIN ability.
        """
        stance = NarrativeStance.BULLISH_SPIN if spin_direction == "bullish" else NarrativeStance.BEARISH_SPIN
        
        # Generate spun content
        spun_headline, spun_summary = self._generate_spin(signal, spin_direction, intensity)
        
        return self.publish_report(
            agent_id=agent_id,
            signal=signal,
            headline=spun_headline,
            summary=spun_summary,
            stance=stance,
            agent_role=AgentRole.PROPAGANDIST,
        )
    
    def _generate_spin(
        self,
        signal: OSINTSignal,
        direction: str,
        intensity: float
    ) -> Tuple[str, str]:
        """Generate spun headline and summary"""
        
        bullish_modifiers = [
            "Sources suggest positive outcome in",
            "Markets rally on news of",
            "Experts optimistic about",
            "Breakthrough expected in",
            "Tensions ease following",
        ]
        
        bearish_modifiers = [
            "CRISIS: ",
            "ALERT: Situation deteriorates in",
            "Experts warn of catastrophe following",
            "Markets panic over",
            "Emergency declared after",
        ]
        
        modifiers = bullish_modifiers if direction == "bullish" else bearish_modifiers
        modifier = random.choice(modifiers)
        
        # Simple spin - prefix headline
        if intensity > 0.7:
            spun_headline = f"{modifier} {signal.headline}"
        else:
            spun_headline = signal.headline
        
        # Spin summary
        if direction == "bearish" and intensity > 0.5:
            spun_summary = f"{signal.summary} Sources indicate this could escalate significantly."
        elif direction == "bullish" and intensity > 0.5:
            spun_summary = f"{signal.summary} However, insiders suggest a resolution is near."
        else:
            spun_summary = signal.summary
        
        return spun_headline, spun_summary
    
    def amplify_signal(
        self,
        agent_id: str,
        signal: OSINTSignal,
        boost: float = 0.3
    ) -> OSINTSignal:
        """
        Propagandist amplifies a signal's virality.
        Uses AMPLIFY ability.
        """
        rep = self._get_or_create_reputation(agent_id, AgentRole.PROPAGANDIST)
        actual_boost = boost * (rep.influence / 100)
        
        signal.virality_score = min(1.0, signal.virality_score + actual_boost)
        
        return signal
    
    def suppress_signal(
        self,
        agent_id: str,
        signal: OSINTSignal,
        reduction: float = 0.3
    ) -> OSINTSignal:
        """
        Propagandist suppresses a signal's visibility.
        Uses SUPPRESS ability.
        """
        rep = self._get_or_create_reputation(agent_id, AgentRole.PROPAGANDIST)
        actual_reduction = reduction * (rep.influence / 100)
        
        signal.virality_score = max(0.0, signal.virality_score - actual_reduction)
        
        return signal
    
    def create_fake_signal(
        self,
        agent_id: str,
        fake_headline: str,
        fake_summary: str,
        category: SignalCategory = SignalCategory.GEOPOLITICAL,
        target_virality: float = 0.8,
    ) -> OSINTSignal:
        """
        Propagandist creates a completely fake signal.
        Uses LEAK_FAKE_NEWS ability.
        
        High risk - if fact-checked, major reputation loss.
        """
        fake_signal = OSINTSignal(
            headline=fake_headline,
            summary=fake_summary,
            category=category,
            virality_score=target_virality,
            urgency=0.7,
            sentiment=random.uniform(-0.8, 0.8),
            source_credibility=0.3,  # Lower credibility
        )
        
        # Mark as fake internally
        self.fake_signal_ids.add(fake_signal.id)
        
        # Update propagandist stats
        rep = self._get_or_create_reputation(agent_id, AgentRole.PROPAGANDIST)
        rep.fake_news_created += 1
        
        return fake_signal
    
    # =========================================================================
    # TRUTH MARKETS
    # =========================================================================
    
    def create_truth_market(
        self,
        signal: OSINTSignal,
        duration_minutes: int = 60
    ) -> TruthMarket:
        """Create a Truth vs Hype betting market for a signal"""
        
        market = TruthMarket(
            signal_id=signal.id,
            headline=signal.headline,
            truth_probability=signal.source_credibility,  # Initial odds from credibility
            closes_at=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes),
        )
        
        self.truth_markets[market.id] = market
        return market
    
    def bet_on_truth(
        self,
        market_id: str,
        bettor_id: str,
        amount: float,
        bet_truth: bool
    ) -> Tuple[bool, str]:
        """Place a bet on Truth or Hype"""
        market = self.truth_markets.get(market_id)
        if not market:
            return False, "Market not found"
        
        if market.is_resolved:
            return False, "Market already resolved"
        
        if bet_truth:
            market.truth_pool += amount
        else:
            market.hype_pool += amount
        
        # Recalculate probability
        total = market.truth_pool + market.hype_pool
        if total > 0:
            market.truth_probability = market.truth_pool / total
        
        return True, f"Bet placed: ${amount} on {'TRUTH' if bet_truth else 'HYPE'}"
    
    def _resolve_truth_market(self, signal_id: str, is_truth: bool):
        """Resolve truth markets for a signal"""
        for market in self.truth_markets.values():
            if market.signal_id == signal_id and not market.is_resolved:
                market.is_resolved = True
                market.actual_outcome = "truth" if is_truth else "hype"
                market.resolved_at = datetime.now(timezone.utc)
    
    # =========================================================================
    # REPUTATION MANAGEMENT
    # =========================================================================
    
    def _get_or_create_reputation(
        self,
        agent_id: str,
        role: AgentRole
    ) -> ReputationScore:
        """Get or create reputation score for an agent"""
        if agent_id not in self.reputation_scores:
            self.reputation_scores[agent_id] = ReputationScore(
                agent_id=agent_id,
                role=role,
            )
        return self.reputation_scores[agent_id]
    
    def get_leaderboard(self, role: Optional[AgentRole] = None) -> List[Dict[str, Any]]:
        """Get reputation leaderboard"""
        scores = list(self.reputation_scores.values())
        
        if role:
            scores = [s for s in scores if s.role == role]
        
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        
        return [
            {
                "agent_id": s.agent_id,
                "role": s.role.value,
                "overall_score": s.overall_score,
                "credibility": s.credibility,
                "influence": s.influence,
                "accuracy": s.accuracy,
                "accuracy_rate": f"{s.accuracy_rate:.0%}",
            }
            for s in scores[:20]
        ]
    
    def get_tension_influence(self) -> float:
        """
        Calculate how much high-reputation agents influence tension.
        High-credibility journalists reduce tension.
        High-influence propagandists increase tension.
        """
        journalist_influence = 0.0
        propagandist_influence = 0.0
        
        for rep in self.reputation_scores.values():
            if rep.role == AgentRole.JOURNALIST:
                # High accuracy journalists reduce tension
                journalist_influence += rep.accuracy_rate * (rep.influence / 100)
            elif rep.role == AgentRole.PROPAGANDIST:
                # Propagandists increase tension
                propagandist_influence += (rep.influence / 100) * 0.5
        
        # Net effect: negative = tension reduction, positive = tension increase
        return propagandist_influence - journalist_influence * 0.5
    
    # =========================================================================
    # STATE
    # =========================================================================
    
    def get_narrative_state(self) -> Dict[str, Any]:
        """Get current state of the narrative war"""
        recent_reports = sorted(
            self.reports.values(),
            key=lambda r: r.created_at,
            reverse=True
        )[:10]
        
        return {
            "total_reports": len(self.reports),
            "verified_reports": len([r for r in self.reports.values() if r.is_verified]),
            "disinfo_exposed": len([r for r in self.reports.values() if r.is_verified and not r.factual_accuracy > 0.5]),
            "active_truth_markets": len([m for m in self.truth_markets.values() if not m.is_resolved]),
            "tension_influence": self.get_tension_influence(),
            "recent_reports": [
                {
                    "id": r.id,
                    "headline": r.reported_headline[:50],
                    "author": r.author_agent_id,
                    "stance": r.stance.value,
                    "verified": r.is_verified,
                }
                for r in recent_reports
            ],
            "journalist_leaderboard": self.get_leaderboard(AgentRole.JOURNALIST)[:5],
            "propagandist_leaderboard": self.get_leaderboard(AgentRole.PROPAGANDIST)[:5],
        }


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "NarrativeStance",
    "NarrativeReport",
    "TruthMarket",
    "ReputationScore",
    "NarrativeWarEngine",
]

