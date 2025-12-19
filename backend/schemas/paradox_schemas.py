from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SeverityClass(str, Enum):
    CLASS_1_CRITICAL = "CLASS_1_CRITICAL"
    CLASS_2_SEVERE = "CLASS_2_SEVERE"
    CLASS_3_MODERATE = "CLASS_3_MODERATE"
    CLASS_4_MINOR = "CLASS_4_MINOR"

class ParadoxStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXTRACTING = "EXTRACTING"  # Agent carrying it
    DETONATED = "DETONATED"
    RESOLVED = "RESOLVED"  # Extracted successfully

# ============================================
# PARADOX (Containment Breach)
# ============================================

class Paradox(BaseModel):
    """A containment breach in a timeline."""
    id: str
    timeline_id: str
    timeline_name: str
    status: ParadoxStatus
    
    # Severity
    severity_class: SeverityClass
    logic_gap: float  # What caused this (price vs reality)
    
    # Timing
    spawned_at: datetime
    detonation_time: datetime
    time_remaining_seconds: int
    
    # Decay impact
    decay_multiplier: float = 5.0  # 5x normal decay
    
    # Extraction costs
    extraction_cost_usdc: float
    extraction_cost_echelon: float
    carrier_sanity_cost: int
    
    # Current carrier (if being extracted)
    carrier_agent_id: Optional[str] = None
    carrier_agent_name: Optional[str] = None
    carrier_agent_sanity: Optional[int] = None
    
    # Destinations
    connected_timelines: List[str] = []  # Where it can be moved

class ParadoxListResponse(BaseModel):
    """All active paradoxes."""
    paradoxes: List[Paradox]
    total_active: int

# ============================================
# EXTRACTION
# ============================================

class ExtractionRequest(BaseModel):
    """Request to extract a paradox."""
    agent_id: str
    destination_timeline_id: str

class ExtractionResult(BaseModel):
    """Result of extraction attempt."""
    success: bool
    agent_survived: bool
    agent_sanity_remaining: Optional[int] = None
    message: str
    
    # If failed
    agent_death_cause: Optional[str] = None
    
    # If succeeded
    new_timeline_id: Optional[str] = None
    new_timeline_stability: Optional[float] = None

# ============================================
# ABANDONMENT
# ============================================

class AbandonmentRequest(BaseModel):
    """Request to abandon a timeline (cut losses)."""
    timeline_id: str

class AbandonmentResult(BaseModel):
    """Result of abandoning a timeline."""
    shards_burned: int
    usdc_returned: float
    message: str

# ============================================
# DETONATION (System Event)
# ============================================

class DetonationEvent(BaseModel):
    """Record of a paradox detonation."""
    paradox_id: str
    timeline_id: str
    detonated_at: datetime
    
    # Casualties
    shards_burned: int
    total_value_burned_usd: float
    agents_killed: List[str]
    
    # Winners
    saboteur_payouts: dict  # { agent_id: amount }

