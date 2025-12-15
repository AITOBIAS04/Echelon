"""
OSINT Master Registry
======================
Combines all alternative data signal sources into a unified system.

Categories:
1. WAR ROOM (Geopolitics & Conflict)
   - VIP Aircraft Tracking
   - Marine Traffic (AIS)
   - Night Lights (Satellite)
   - Internet Outages

2. THE ALPHA (Financial Markets)
   - Satellite Supply Chain
   - Job Postings
   - App Store Rankings
   - Corporate Jet Tracking

3. THE EDGE (Sports)
   - Stadium Weather
   - Player Social Sentiment
   - Team Travel/Fatigue
   - Lineup Intelligence

Usage:
    from backend.core.osint_registry import OSINTRegistry
    
    registry = OSINTRegistry()
    signals = await registry.scan_all()
    
    # Or scan by category
    geopolitical = await registry.scan_category("war_room")
    financial = await registry.scan_category("alpha")
    sports = await registry.scan_category("sports")
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import all source modules
from backend.core.signal_detector import (
    SignalDetector, Signal, SignalSource, RegionOfInterest,
    DEFCONLevel, Mission, get_detector
)
from backend.core.osint_sources_situation_room import get_situation_room_sources
from backend.core.osint_sources_financial import get_financial_sources
from backend.core.osint_sources_sports import get_sports_sources
try:
    from backend.core.osint_sources_extended import get_extended_sources
except ImportError:
    get_extended_sources = lambda: []
try:
    from backend.core.persistence_manager import get_persistence_manager
except ImportError:
    get_persistence_manager = None


class SignalCategory(Enum):
    """Categories of OSINT signals."""
    WAR_ROOM = "war_room"      # Geopolitics & Conflict
    ALPHA = "alpha"            # Financial Markets
    SPORTS = "sports"          # Sports Betting Edge
    ALL = "all"


@dataclass
class CategoryStats:
    """Statistics for a signal category."""
    category: str
    sources_count: int
    signals_detected: int
    avg_confidence: float
    top_severity: str


class OSINTRegistry:
    """
    Master registry for all OSINT signal sources.
    
    Provides unified access to:
    - War Room signals (geopolitics)
    - Alpha signals (financial)
    - Sports Edge signals
    
    Also provides:
    - Cross-category correlation
    - Priority ranking
    - Mission generation
    """
    
    def __init__(self):
        # Get the base signal detector
        self.base_detector = get_detector()
        
        # Initialize all source categories
        self.war_room_sources = get_situation_room_sources()
        self.financial_sources = get_financial_sources()
        self.sports_sources = get_sports_sources()
        self.extended_sources = get_extended_sources()
        
        # Combine with base detector sources
        self.all_sources = (
            self.base_detector.sources +
            self.war_room_sources +
            self.financial_sources +
            self.sports_sources +
            self.extended_sources
        )
        
        # Active signals from all categories
        self.active_signals: List[Signal] = []
        
        # Stats
        self.stats = {
            "total_scans": 0,
            "signals_by_category": {
                "war_room": 0,
                "alpha": 0,
                "sports": 0,
                "extended": 0,
                "base": 0,
            },
            "missions_generated": 0,
        }
        
        # --- NEW: PERSISTENCE ---
        if get_persistence_manager is not None:
            try:
                self.persistence = get_persistence_manager()
                self._load_state()
            except Exception as e:
                print(f"⚠️ Failed to initialize persistence: {e}")
                self.persistence = None
        else:
            self.persistence = None
    
    async def scan_all(self, regions: List[RegionOfInterest] = None) -> List[Signal]:
        """
        Scan all OSINT sources across all categories.
        
        Args:
            regions: Specific regions to scan (None = all)
        
        Returns:
            List of all detected signals
        """
        self.stats["total_scans"] += 1
        
        if regions is None:
            regions = self.base_detector.monitored_regions
        
        all_signals = []
        
        # Scan base detector
        base_signals = await self.base_detector.scan_all_sources()
        all_signals.extend(base_signals)
        self.stats["signals_by_category"]["base"] += len(base_signals)
        
        # Scan War Room
        war_signals = await self._scan_sources(self.war_room_sources, regions)
        all_signals.extend(war_signals)
        self.stats["signals_by_category"]["war_room"] += len(war_signals)
        
        # Scan Financial (Alpha)
        alpha_signals = await self._scan_sources(self.financial_sources, regions)
        all_signals.extend(alpha_signals)
        self.stats["signals_by_category"]["alpha"] += len(alpha_signals)
        
        # Scan Sports
        sports_signals = await self._scan_sources(self.sports_sources, regions)
        all_signals.extend(sports_signals)
        self.stats["signals_by_category"]["sports"] += len(sports_signals)
        
        # Scan Extended (Crypto, Legislative, FIRMS, Trends)
        extended_signals = await self._scan_sources(self.extended_sources, regions)
        all_signals.extend(extended_signals)
        self.stats["signals_by_category"]["extended"] += len(extended_signals)
        
        # Update active signals
        self._update_active_signals(all_signals)
        
        # --- NEW: Save to disk ---
        if self.persistence:
            self._save_state()
        
        return all_signals
    
    async def scan_category(
        self, 
        category: SignalCategory,
        regions: List[RegionOfInterest] = None
    ) -> List[Signal]:
        """Scan a specific category of sources."""
        
        if regions is None:
            regions = self.base_detector.monitored_regions
        
        if category == SignalCategory.WAR_ROOM:
            sources = self.war_room_sources
        elif category == SignalCategory.ALPHA:
            sources = self.financial_sources
        elif category == SignalCategory.SPORTS:
            sources = self.sports_sources
        else:
            return await self.scan_all(regions)
        
        return await self._scan_sources(sources, regions)
    
    async def _scan_sources(self, sources: List, regions: List[RegionOfInterest]) -> List[Signal]:
        """Scan a list of sources across regions."""
        signals = []
        
        for source in sources:
            for region in regions:
                try:
                    region_signals = await source.scan(region)
                    signals.extend(region_signals)
                except Exception as e:
                    print(f"⚠️ Error scanning {source.__class__.__name__}: {e}")
        
        return signals
    
    def _update_active_signals(self, new_signals: List[Signal]):
        """Update active signals list, removing expired ones."""
        now = datetime.now(timezone.utc)
        
        # Remove expired
        self.active_signals = [s for s in self.active_signals if s.expires_at > now]
        
        # Add new (avoiding duplicates)
        existing_ids = {s.id for s in self.active_signals}
        for signal in new_signals:
            if signal.id not in existing_ids:
                self.active_signals.append(signal)
    
    def _load_state(self):
        """Load signals from disk."""
        if not self.persistence:
            return
        
        data = self.persistence.load("osint_state", default={})
        
        # Load stats if they exist
        if "stats" in data:
            self.stats = data["stats"]
            
        if data and "signals" in data:
            self.active_signals = []
            for s_data in data["signals"]:
                try:
                    # 1. CLEANUP: Remove computed fields that aren't in __init__
                    if "severity" in s_data:
                        del s_data["severity"]
                    if "is_expired" in s_data:
                        del s_data["is_expired"]
                        
                    # 2. RESTORE ENUMS
                    # We need to handle cases where they might be strings or Enum objects
                    if isinstance(s_data["source"], str):
                        s_data["source"] = SignalSource(s_data["source"])
                    if isinstance(s_data["region"], str):
                        s_data["region"] = RegionOfInterest(s_data["region"])
                        
                    # 3. RESTORE DATETIMES
                    if isinstance(s_data["timestamp"], str):
                        s_data["timestamp"] = datetime.fromisoformat(s_data["timestamp"])
                    if isinstance(s_data["expires_at"], str):
                        s_data["expires_at"] = datetime.fromisoformat(s_data["expires_at"])
                    
                    # 4. Ensure required fields exist
                    if "raw_data" not in s_data:
                        s_data["raw_data"] = {}
                    if "correlated_signals" not in s_data:
                        s_data["correlated_signals"] = []
                    
                    # 5. Reconstruct
                    self.active_signals.append(Signal(**s_data))
                    
                except Exception as e:
                    # Print the specific error to help debug future issues
                    print(f"⚠️ Error restoring signal {s_data.get('id', 'unknown')}: {e}")
            
            print(f"📂 OSINT Registry: Loaded {len(self.active_signals)} active signals")
    
    def _save_state(self):
        """Save signals to disk."""
        if not self.persistence:
            return
        
        # Convert signals to dicts (include raw_data which to_dict() might not have)
        signals_data = []
        for s in self.active_signals:
            sig_dict = s.to_dict()
            # Add raw_data if it exists
            if hasattr(s, 'raw_data'):
                sig_dict["raw_data"] = s.raw_data
            signals_data.append(sig_dict)
        
        state = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "signals": signals_data,
            "stats": self.stats
        }
        self.persistence.save("osint_state", state)
    
    def get_signals_by_category(self) -> Dict[str, List[Signal]]:
        """Get active signals grouped by source category."""
        categorized = {
            "war_room": [],
            "alpha": [],
            "sports": [],
            "other": [],
        }
        
        for signal in self.active_signals:
            # Categorize by source type
            if signal.source in [SignalSource.FLIGHT_RADAR, SignalSource.SHIPPING_PATTERN,
                                SignalSource.SATELLITE_PROXY, SignalSource.POWER_GRID]:
                if any(r in str(signal.raw_data) for r in ["stadium", "retail", "parking"]):
                    categorized["alpha"].append(signal)
                elif any(r in str(signal.raw_data) for r in ["weather", "player", "team"]):
                    categorized["sports"].append(signal)
                else:
                    categorized["war_room"].append(signal)
            elif signal.source == SignalSource.SOCIAL_CHATTER:
                if any(r in str(signal.raw_data) for r in ["ticker", "jobs", "app"]):
                    categorized["alpha"].append(signal)
                elif any(r in str(signal.raw_data) for r in ["player", "team", "sport"]):
                    categorized["sports"].append(signal)
                else:
                    categorized["war_room"].append(signal)
            else:
                categorized["other"].append(signal)
        
        return categorized
    
    def get_priority_signals(self, limit: int = 10) -> List[Signal]:
        """Get highest priority signals across all categories."""
        # Sort by level * confidence
        sorted_signals = sorted(
            self.active_signals,
            key=lambda s: s.level * s.confidence,
            reverse=True
        )
        return sorted_signals[:limit]
    
    def get_category_stats(self) -> Dict[str, CategoryStats]:
        """Get statistics for each category."""
        categorized = self.get_signals_by_category()
        stats = {}
        
        for category, signals in categorized.items():
            if signals:
                avg_conf = sum(s.confidence for s in signals) / len(signals)
                top_sev = max(signals, key=lambda s: s.level).severity
            else:
                avg_conf = 0
                top_sev = "NONE"
            
            stats[category] = CategoryStats(
                category=category,
                sources_count=len(self._get_category_sources(category)),
                signals_detected=len(signals),
                avg_confidence=round(avg_conf, 2),
                top_severity=top_sev,
            )
        
        return stats
    
    def _get_category_sources(self, category: str) -> List:
        """Get sources for a category."""
        if category == "war_room":
            return self.war_room_sources
        elif category == "alpha":
            return self.financial_sources
        elif category == "sports":
            return self.sports_sources
        return []
    
    def get_full_status(self) -> Dict:
        """Get comprehensive status report."""
        categorized = self.get_signals_by_category()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "defcon_level": self.base_detector.defcon_level.value,
            "defcon_name": self.base_detector.defcon_level.name,
            "total_active_signals": len(self.active_signals),
            "signals_by_category": {
                cat: len(sigs) for cat, sigs in categorized.items()
            },
            "top_signals": [s.to_dict() for s in self.get_priority_signals(5)],
            "source_counts": {
                "war_room": len(self.war_room_sources),
                "alpha": len(self.financial_sources),
                "sports": len(self.sports_sources),
                "extended": len(self.extended_sources),
                "base": len(self.base_detector.sources),
                "total": len(self.all_sources),
            },
            "stats": self.stats,
        }
    
    def generate_domain_missions(self, domain: str) -> List[Mission]:
        """
        Generate missions for a specific domain.
        
        Args:
            domain: "geopolitics", "financial", or "sports"
        """
        missions = []
        
        if domain == "geopolitics":
            # Use base detector for geopolitics
            missions = self.base_detector.generate_missions_from_defcon()
        
        elif domain == "financial":
            # Generate financial "alpha" missions from signals
            categorized = self.get_signals_by_category()
            for signal in categorized.get("alpha", []):
                if signal.level >= 0.6:
                    mission = self._create_financial_mission(signal)
                    if mission:
                        missions.append(mission)
        
        elif domain == "sports":
            # Generate sports edge missions
            categorized = self.get_signals_by_category()
            for signal in categorized.get("sports", []):
                if signal.level >= 0.5:
                    mission = self._create_sports_mission(signal)
                    if mission:
                        missions.append(mission)
        
        self.stats["missions_generated"] += len(missions)
        return missions
    
    def _create_financial_mission(self, signal: Signal) -> Optional[Mission]:
        """Create a financial mission from a signal."""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        # Extract company/ticker if available
        ticker = signal.raw_data.get("ticker", "UNKNOWN")
        company = signal.raw_data.get("company", "Unknown Company")
        
        codenames = ["ALPHA STRIKE", "MARKET MAKER", "PROFIT HUNTER", "YIELD SEEKER"]
        
        return Mission(
            id=f"fin_mission_{signal.id}",
            codename=f"OPERATION {codenames[hash(signal.id) % len(codenames)]}",
            title=f"Will {ticker} Move on This Signal?",
            description=signal.description,
            source_signals=[signal.id],
            region=signal.region,
            mission_type="financial_alpha",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            duration_hours=24,
            outcomes=["PRICE_UP", "PRICE_DOWN", "NO_MOVE"],
            initial_odds={"PRICE_UP": 0.40, "PRICE_DOWN": 0.35, "NO_MOVE": 0.25},
            virality_score=int(signal.level * 100),
            intel_required=signal.level >= 0.8,
            intel_cost_usd=0.25 if signal.level >= 0.8 else 0,
        )
    
    def _create_sports_mission(self, signal: Signal) -> Optional[Mission]:
        """Create a sports mission from a signal."""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        team = signal.raw_data.get("team", "Unknown Team")
        sport = signal.raw_data.get("sport", "Unknown")
        
        codenames = ["GAME CHANGER", "EDGE FINDER", "STAT HUNTER", "LINE MOVER"]
        
        return Mission(
            id=f"sports_mission_{signal.id}",
            codename=f"OPERATION {codenames[hash(signal.id) % len(codenames)]}",
            title=f"Will This Affect {team}'s Game?",
            description=signal.description,
            source_signals=[signal.id],
            region=signal.region,
            mission_type="sports_edge",
            created_at=now,
            expires_at=now + timedelta(hours=12),
            duration_hours=12,
            outcomes=["COVERS", "FAILS", "PUSH"],
            initial_odds={"COVERS": 0.45, "FAILS": 0.45, "PUSH": 0.10},
            virality_score=int(signal.level * 100),
            intel_required=False,
            intel_cost_usd=0,
        )


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_registry_instance: Optional[OSINTRegistry] = None


def get_osint_registry() -> OSINTRegistry:
    """Get or create global OSINT registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = OSINTRegistry()
    return _registry_instance


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def comprehensive_demo():
        print("=" * 70)
        print("🕵️ OSINT MASTER REGISTRY - Comprehensive Demo")
        print("=" * 70)
        
        registry = get_osint_registry()
        
        print("\n📡 SCANNING ALL OSINT SOURCES...")
        print("-" * 50)
        
        # Run multiple scans
        for i in range(3):
            signals = await registry.scan_all()
            print(f"Scan {i+1}: Found {len(signals)} new signals")
        
        # Get status
        status = registry.get_full_status()
        
        print(f"\n🚨 DEFCON Level: {status['defcon_level']} ({status['defcon_name']})")
        print(f"📊 Total Active Signals: {status['total_active_signals']}")
        
        print("\n📁 SIGNALS BY CATEGORY:")
        for category, count in status['signals_by_category'].items():
            emoji = {"war_room": "🎖️", "alpha": "💰", "sports": "🏈", "other": "📌"}.get(category, "•")
            print(f"   {emoji} {category.upper()}: {count} signals")
        
        print("\n🔌 SOURCE COUNTS:")
        for source_type, count in status['source_counts'].items():
            print(f"   {source_type}: {count} sources")
        
        if status['top_signals']:
            print("\n⚡ TOP PRIORITY SIGNALS:")
            for sig in status['top_signals']:
                print(f"   [{sig['severity']}] {sig['source']}")
                print(f"      {sig['description'][:60]}...")
        
        # Generate missions for each domain
        print("\n🎯 GENERATING MISSIONS BY DOMAIN:")
        
        for domain in ["geopolitics", "financial", "sports"]:
            missions = registry.generate_domain_missions(domain)
            print(f"\n   {domain.upper()}: {len(missions)} missions")
            for m in missions[:2]:  # Show first 2
                print(f"      - {m.codename}: {m.title[:40]}...")
        
        print("\n" + "=" * 70)
        print("✅ OSINT Registry fully operational!")
        print(f"   Total sources: {status['source_counts']['total']}")
        print(f"   Scanning {len(registry.base_detector.monitored_regions)} regions")
        print("=" * 70)
    
    asyncio.run(comprehensive_demo())

