import os

from dotenv import load_dotenv
from eth_account import Account
from virtuals_acp.client import VirtualsACP, BASE_SEPOLIA_CONFIG
from virtuals_acp.contract_clients.contract_client import ACPContractClient

load_dotenv()

# 1. Setup the Client (Using your correct new pattern)
print("--- 🔑 INITIALIZING CLIENT ---")

try:
    # Get private key from env
    private_key = os.getenv("AGENT_PRIVATE_KEY")
    if not private_key:
        # Try using the wallet factory pattern
        from core.wallet_factory import WalletFactory
        master_seed = os.getenv("MASTER_WALLET_SEED")
        if master_seed:
            factory = WalletFactory(master_seed)
            wallet_data = factory.get_agent_wallet("Test_Agent")
            private_key = wallet_data["private_key"]
            agent_wallet_address = wallet_data["address"]
            print(f"✅ Using wallet factory. Address: {agent_wallet_address}")
        else:
            print("⚠️  Neither AGENT_PRIVATE_KEY nor MASTER_WALLET_SEED is set.")
            print("   Using a test private key for demonstration (DO NOT USE IN PRODUCTION)")
            # Test private key - DO NOT USE IN PRODUCTION
            private_key = "0x" + "1" * 64  # This is just for testing structure
            account = Account.from_key(private_key)
            agent_wallet_address = account.address
            print(f"   Using test key. Address: {agent_wallet_address}")
    else:
        # Derive address from private key if not provided
        agent_wallet_address = os.getenv("AGENT_WALLET_ADDRESS")
        if not agent_wallet_address:
            account = Account.from_key(private_key)
            agent_wallet_address = account.address
            print(f"✅ Derived address from private key: {agent_wallet_address}")
    
    contract_client = ACPContractClient(
        wallet_private_key=private_key,
        agent_wallet_address=agent_wallet_address,
        entity_id=0,
        config=BASE_SEPOLIA_CONFIG
    )
    acp_client = VirtualsACP(acp_contract_clients=[contract_client])

    print("✅ Client Initialized.")

    # 2. Check available methods
    print(f"\n--- 🔍 CHECKING AVAILABLE METHODS ---")
    print(f"VirtualsACP methods with 'sign': {[m for m in dir(acp_client) if 'sign' in m.lower()]}")
    print(f"ACPContractClient methods with 'sign': {[m for m in dir(contract_client) if 'sign' in m.lower()]}")
    
    # Check if contract_client has account
    if hasattr(contract_client, 'account'):
        print(f"✅ Contract client has 'account' attribute")
        print(f"   Account address: {contract_client.account.address}")
        print(f"   Account methods with 'sign': {[m for m in dir(contract_client.account) if 'sign' in m.lower()]}")
    
    # 2. Test Signing
    message = "I authorize this payment of 0.01 USDC"
    print(f"\n--- ✍️ ATTEMPTING TO SIGN: '{message}' ---")

    sig = None
    try:
        # Attempt A: Direct on VirtualsACP
        sig = acp_client.sign_message(message)
        print(f"✅ Success on VirtualsACP.sign_message!")
    except AttributeError:
        print("⚠️ VirtualsACP does not have sign_message.")
        try:
            # Attempt B: Direct on the Contract Client
            sig = contract_client.sign_message(message)
            print(f"✅ Success on ACPContractClient.sign_message!")
        except AttributeError:
            print("⚠️ ACPContractClient does not have sign_message.")
            try:
                # Attempt C: Use the account directly (eth_account LocalAccount)
                if hasattr(contract_client, 'account'):
                    # Use eth_account.messages.encode_defunct for EIP-191 message encoding
                    from eth_account.messages import encode_defunct
                    eth_message = encode_defunct(text=message)
                    signed_message = contract_client.account.sign_message(eth_message)
                    sig = signed_message.signature.hex()
                    print(f"✅ Success using account.sign_message with encode_defunct!")
                    print(f"   Message hash: {signed_message.message_hash.hex()}")
                    print(f"   Signature: {sig[:66]}...")
                else:
                    print("❌ Contract client does not have account attribute")
            except Exception as e:
                print(f"❌ Signing failed: {e}")
                import traceback
                traceback.print_exc()
                sig = "FAILED"
        except Exception as e:
            print(f"❌ Signing failed: {e}")
            import traceback
            traceback.print_exc()
            sig = "FAILED"

    if sig:
        print(f"\n✅ Signature result: {str(sig)[:50]}...")
    else:
        print(f"\n❌ No signature generated")

except Exception as e:
    print(f"❌ Initialization Error: {e}")
    import traceback
    traceback.print_exc()

