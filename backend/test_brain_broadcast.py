"""
Test script for Hierarchical Brain Router - Shark Broadcast
"""
import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from backend.api.brain_router import HierarchicalBrain, TaskType

async def test_shark_broadcast():
    """Test Shark broadcast generation with real API."""
    print("=" * 80)
    print("TESTING SHARK BROADCAST GENERATION")
    print("=" * 80)
    print()
    
    # Initialize brain
    brain = HierarchicalBrain()
    
    print("🧠 Initializing Hierarchical Brain...")
    print(f"   Mistral API Key: {'✅ Set' if os.getenv('MISTRAL_API_KEY') else '❌ Missing'}")
    print(f"   Anthropic API Key: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"   Groq API Key: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Missing'}")
    print()
    
    # Test Shark broadcast
    print("🦈 Generating MEGALODON broadcast...")
    print("   Agent: MEGALODON")
    print("   Action: BUY")
    print("   Size: $5,000")
    print("   Market: Oil Futures")
    print("   Price: 0.65")
    print("   Confidence: 87%")
    print()
    
    try:
        result = await brain.generate_broadcast(
            agent_id="MEGALODON",
            action="BUY",
            size=5000,
            market="Oil Futures",
            price=0.65,
            confidence=87,
        )
        
        print("=" * 80)
        print("✅ BROADCAST GENERATED")
        print("=" * 80)
        print()
        print(f"📢 Result:")
        print(f"   {result}")
        print()
        
        # Get stats
        stats = brain.get_stats()
        print("📊 Brain Stats:")
        print(f"   Layer 1.5 calls: {stats['layer_1_5_calls']}")
        print(f"   Total cost: ${stats['total_cost']:.6f}")
        print(f"   Provider used: {stats.get('provider_used', 'N/A')}")
        print()
        
        print("✅ Test complete!")
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_shark_broadcast())

