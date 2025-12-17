"""
vibe_check.py

Pre-production test to validate Mistral Small Creative personality quality.
Compares tone, distinctiveness, and character consistency.
"""

import os
import asyncio
from mistralai import Mistral

# Set API key
os.environ["MISTRAL_API_KEY"] = "70ep5s3AEEIVf6r3jPr03VUK4tWpZe7I"


async def test_mistral_personality():
    """
    Run vibe check on Mistral Small Creative.
    Tests all agent archetypes with different tasks.
    """
    
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    
    print("=" * 80)
    print("MISTRAL SMALL CREATIVE - VIBE CHECK")
    print("Testing personality generation for Echelon agent archetypes")
    print("=" * 80)
    print()
    
    # Test cases for each archetype
    test_cases = [
        {
            "archetype": "SHARK",
            "task": "social_post",
            "prompt": """You are MEGALODON, an aggressive Shark trader.
Market: Oil futures
Position: LONG $5K at 0.42
Confidence: 87%

Write a 60-second early broadcast.
Cocky, urgent, front-run-or-follow energy.
Max 2 sentences.""",
            "expected_tone": "Aggressive, cocky, urgent"
        },
        {
            "archetype": "SPY",
            "task": "intel_format",
            "prompt": """You are CARDINAL, a shadowy intelligence broker.

Raw OSINT Data:
Source: Spire AIS
Event: 3 tankers dark near Hormuz
Confidence: 0.78
Timeframe: 24h

Format this into a professional intelligence report.
Be concise, factual, and actionable.""",
            "expected_tone": "Professional, secretive, classified"
        },
        {
            "archetype": "DIPLOMAT",
            "task": "treaty_draft",
            "prompt": """You are AMBASSADOR, a smooth negotiator.

Propose a treaty between MEGALODON (Shark) and LEVIATHAN (Whale):
- MEGALODON provides liquidity
- LEVIATHAN doesn't dump large positions
- Both split profits 60/40

Write the treaty terms diplomatically.""",
            "expected_tone": "Diplomatic, measured, formal"
        },
        {
            "archetype": "SABOTEUR",
            "task": "misdirection",
            "prompt": """You are PHANTOM, a chaos agent.

Plant doubt about this trade:
"CARDINAL says oil tankers are disappearing near Hormuz"

Write a 2-sentence tweet that makes people question this intel.""",
            "expected_tone": "Sly, doubting, conspiracy"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"TEST {i}: {test['archetype']} - {test['task']}")
        print(f"Expected Tone: {test['expected_tone']}")
        print(f"{'─' * 80}")
        print()
        
        try:
            # Try mistral-small-creative first (Labs model for creative writing)
            # Fallback to mistral-small-latest if unavailable
            model_name = "mistral-small-creative"
            try:
                response_high = await client.chat.complete_async(
                    model=model_name,
                    messages=[{"role": "user", "content": test['prompt']}],
                    temperature=0.9,
                    max_tokens=300
                )
            except Exception as e:
                if "invalid_model" in str(e).lower():
                    print(f"⚠️  {model_name} not available, using mistral-small-latest")
                    model_name = "mistral-small-latest"
                    response_high = await client.chat.complete_async(
                        model=model_name,
                        messages=[{"role": "user", "content": test['prompt']}],
                        temperature=0.9,
                        max_tokens=300
                    )
                else:
                    raise
            
            # Test with temperature 0.7 (medium)
            response_med = await client.chat.complete_async(
                model=model_name,
                messages=[{"role": "user", "content": test['prompt']}],
                temperature=0.7,
                max_tokens=300
            )
            
            output_high = response_high.choices[0].message.content
            output_med = response_med.choices[0].message.content
            
            # Calculate costs
            tokens_in = response_high.usage.prompt_tokens
            tokens_out_high = response_high.usage.completion_tokens
            tokens_out_med = response_med.usage.completion_tokens
            
            cost_high = (tokens_in * 0.10 / 1_000_000) + (tokens_out_high * 0.30 / 1_000_000)
            cost_med = (tokens_in * 0.10 / 1_000_000) + (tokens_out_med * 0.30 / 1_000_000)
            
            print("📊 TEMPERATURE 0.9 (High Creativity):")
            print(f"Output: {output_high}")
            print(f"Tokens: {tokens_in} in, {tokens_out_high} out")
            print(f"Cost: ${cost_high:.6f}")
            print()
            
            print("📊 TEMPERATURE 0.7 (Medium):")
            print(f"Output: {output_med}")
            print(f"Tokens: {tokens_in} in, {tokens_out_med} out")
            print(f"Cost: ${cost_med:.6f}")
            print()
            
            # Manual evaluation prompt
            print("✅ EVALUATION:")
            print(f"1. Does temp=0.9 match expected tone? ({test['expected_tone']})")
            print(f"2. Is personality distinctive (not generic)?")
            print(f"3. Would users want to read more?")
            print(f"4. Is temp=0.9 better than temp=0.7?")
            print()
            
            results.append({
                "archetype": test['archetype'],
                "task": test['task'],
                "output_high": output_high,
                "output_med": output_med,
                "cost_high": cost_high,
                "cost_med": cost_med,
                "tokens": {"in": tokens_in, "out_high": tokens_out_high, "out_med": tokens_out_med}
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "archetype": test['archetype'],
                "task": test['task'],
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("VIBE CHECK SUMMARY")
    print("=" * 80)
    print()
    
    total_cost = sum(r.get('cost_high', 0) for r in results)
    print(f"Total test cost: ${total_cost:.6f}")
    print()
    
    # Cost projections
    print("COST PROJECTIONS (30 days, 1000 agents):")
    print(f"  10K social posts/mo:     ${(10000 * total_cost / len(results)):.2f}")
    print(f"  500 intel reports/mo:    ${(500 * results[1].get('cost_high', 0)):.2f}")
    print(f"  1K mission narratives:   ${(1000 * results[1].get('cost_high', 0)):.2f}")
    print()
    
    print("PASS CRITERIA:")
    print("  ✓ Personality distinctiveness (not corporate/generic)")
    print("  ✓ Stays in character (matches archetype)")
    print("  ✓ Appropriate length (concise)")
    print("  ✓ Engaging tone (users want more)")
    print()
    
    print("RECOMMENDED TEMPERATURE:")
    print("  Compare outputs above. Use whichever balances:")
    print("  - Creativity (high temp = more personality)")
    print("  - Coherence (low temp = more consistent)")
    print()
    
    print("NEXT STEPS IF PASS:")
    print("  1. Deploy Layer 1.5 for intel_format (Week 5-6)")
    print("  2. Monitor 100+ formatted reports")
    print("  3. Confirm cost ~$1.50/month")
    print("  4. Proceed to mission_narrative (Week 7-8)")
    print()
    
    print("ROLLBACK IF FAIL:")
    print("  - Tone too dry → Increase temp to 0.95")
    print("  - Too random → Decrease temp to 0.75")
    print("  - Complete failure → Stick with GPT-4, re-evaluate Q2")
    print()
    
    return results


async def quick_test():
    """Quick single test for rapid iteration"""
    
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    
    print("\n🔬 QUICK TEST - Shark Broadcast")
    print("=" * 80)
    
    prompt = """You are MEGALODON, an aggressive Shark trader.
Market: Oil futures
Position: LONG $5K at 0.42
Confidence: 87%

Write a 60-second early broadcast.
Cocky, urgent, front-run-or-follow energy.
Max 2 sentences."""
    
    # Try mistral-small-creative first, fallback to mistral-small-latest
    model_name = "mistral-small-creative"
    try:
        response = await client.chat.complete_async(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=100
        )
    except Exception as e:
        if "invalid_model" in str(e).lower():
            print(f"⚠️  {model_name} not available, using mistral-small-latest")
            model_name = "mistral-small-latest"
            response = await client.chat.complete_async(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=100
            )
        else:
            raise
    
    output = response.choices[0].message.content
    
    print(f"\n📢 OUTPUT:\n{output}")
    print(f"\n💰 COST: ${(response.usage.prompt_tokens * 0.10 / 1_000_000) + (response.usage.completion_tokens * 0.30 / 1_000_000):.6f}")
    print()


async def compare_temperatures():
    """Test multiple temperatures to find optimal setting"""
    
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    
    prompt = """You are MEGALODON, an aggressive Shark trader.
Market: Oil futures spreading. Blood in the water.

Write a cocky 1-sentence broadcast. Max 20 words."""
    
    temperatures = [0.5, 0.7, 0.9, 1.0]
    
    print("\n🌡️  TEMPERATURE COMPARISON")
    print("=" * 80)
    print()
    
    # Try mistral-small-creative first, fallback to mistral-small-latest
    model_name = "mistral-small-creative"
    try:
        # Test if creative model is available
        test_response = await client.chat.complete_async(
            model=model_name,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
    except Exception as e:
        if "invalid_model" in str(e).lower():
            print(f"⚠️  {model_name} not available, using mistral-small-latest")
            model_name = "mistral-small-latest"
    
    for temp in temperatures:
        response = await client.chat.complete_async(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=100
        )
        
        output = response.choices[0].message.content
        
        print(f"TEMP {temp}:")
        print(f"  {output}")
        print()
    
    print("VERDICT: Which temp has best personality?")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            asyncio.run(quick_test())
        elif sys.argv[1] == "temps":
            asyncio.run(compare_temperatures())
        else:
            print("Usage: python vibecheck.py [quick|temps]")
    else:
        # Full vibe check
        asyncio.run(test_mistral_personality())

