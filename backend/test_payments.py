"""
Quick test script for Coinbase Commerce integration
====================================================
Run this to verify your payment setup is working.
"""
import asyncio
import os
from .coinbase_commerce import (
    get_commerce_client,
    get_payment_handler,
    CommerceConfig
)

async def test_setup():
    print("=" * 60)
    print("🧪 Testing Coinbase Commerce Integration")
    print("=" * 60)
    
    # Check configuration
    config = CommerceConfig()
    
    print("\n📋 Configuration Check:")
    print(f"   API Key: {'✅ Set' if config.api_key else '❌ Missing'}")
    print(f"   Webhook Secret: {'✅ Set' if config.webhook_secret else '❌ Missing'}")
    print(f"   Settlement Wallet: {config.settlement_wallet[:10]}...")
    print(f"   API Base URL: {config.api_base_url}")
    
    if not config.api_key:
        print("\n⚠️  No API key found. Set COINBASE_COMMERCE_API_KEY in .env")
        return
    
    # Test client initialization
    print("\n🔌 Testing Client Connection...")
    client = get_commerce_client()
    
    try:
        # Try to list charges (this will test API connectivity)
        print("   Attempting to connect to Coinbase Commerce API...")
        charges = await client.list_charges(limit=1)
        print(f"   ✅ Connection successful! Found {len(charges)} recent charge(s)")
        
        # Test charge creation (simulation mode if API fails)
        print("\n📄 Testing Charge Creation...")
        try:
            test_charge = await client.create_deposit_charge(
                user_id="test_user_001",
                amount=1.00,
                redirect_url="https://pizzint.app/test"
            )
            print(f"   ✅ Charge created successfully!")
            print(f"      ID: {test_charge.id}")
            print(f"      Code: {test_charge.code}")
            print(f"      URL: {test_charge.hosted_url}")
            print(f"      Status: {test_charge.status.value}")
        except Exception as e:
            print(f"   ⚠️  Charge creation failed: {e}")
            print("   (This might be expected if using test keys)")
        
        # Test payment handler
        print("\n💳 Testing Payment Handler...")
        handler = get_payment_handler()
        test_balance = handler.get_user_balance("test_user_001")
        print(f"   ✅ Payment handler initialized")
        print(f"      Test user balance: ${test_balance:.2f}")
        
        print("\n" + "=" * 60)
        print("✅ Integration test complete!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   1. Start your backend: python3 -m backend.main")
        print("   2. Start your frontend: npm run dev")
        print("   3. Visit http://localhost:3000/wallet")
        print("   4. Connect your wallet and test a deposit")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n   Troubleshooting:")
        print("   - Verify your API key is correct")
        print("   - Check your internet connection")
        print("   - Ensure Coinbase Commerce account is active")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_setup())




