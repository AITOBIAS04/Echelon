import json
import os
import time  # <--- MAKE SURE THIS IS HERE
from web3 import Web3
from dotenv import load_dotenv

# 1. Load Secrets
load_dotenv()
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# 2. Connect to Base Sepolia
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("❌ Failed to connect to Blockchain")

print(f"✅ Connected to Base Sepolia! Block: {w3.eth.block_number}")

# 3. Load Contract
with open("abi.json", "r") as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

def create_market_on_chain(question, duration_seconds):
    """
    Creates a market and returns the new Market ID.
    """
    print(f"\n🚀 Creating Market: '{question}'...")
    
    tx = contract.functions.createMarket(
        question,
        duration_seconds
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"⏳ Transaction sent! Hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Parse the Logs to find the Market ID
    rich_logs = contract.events.MarketCreated().process_receipt(receipt)
    market_id = rich_logs[0]['args']['marketId']
    
    print(f"✅ Market Created! ID: {market_id}")
    return market_id

def resolve_market_on_chain(market_id):
    """
    Calls the contract to resolve the market using Chainlink VRF.
    """
    print(f"\n⚖️ Resolving Market ID: {market_id}...")
    
    tx = contract.functions.resolveMarket(market_id).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000, 
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"⏳ Resolution request sent! Hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Oracle Request Sent! Chainlink is now calculating the winner...")
    return receipt

# --- NEW FUNCTION ADDED HERE ---
def get_market_outcome(market_id):
    """
    Polls the blockchain until the market is resolved and returns the winner.
    """
    print(f"\nWaiting for Chainlink VRF to resolve Market {market_id}...")
    
    # Loop for up to 60 seconds (Chainlink usually takes 10-30s)
    for i in range(30):
        # Call the 'markets' mapping on the contract
        # markets(id) returns (id, question, endTime, resolved, outcome, ...)
        market_data = contract.functions.markets(market_id).call()
        
        is_resolved = market_data[3] # 4th item is boolean 'resolved'
        outcome = market_data[4]     # 5th item is string 'outcome'
        
        if is_resolved:
            print(f"🎉 Market Resolved! The winner is: {outcome}")
            return outcome
            
        print(f"   ...waiting for oracle (Attempt {i+1}/12)...")
        time.sleep(5) # Wait 5 seconds before checking again
        
    print("❌ Timed out waiting for oracle.")
    return None

# --- Test Run ---
if __name__ == "__main__":
    # 1. Create a market
    new_id = create_market_on_chain("Will Sim-Apple crash?", 3600)
    
    # 2. Wait a moment 
    print("...Simulating time passing...")
    time.sleep(5)
    
    # 3. Trigger the Resolution (Ask Chainlink)
    resolve_market_on_chain(new_id)
    
    # 4. Wait for the "Truth" (Listen for Chainlink)
    get_market_outcome(new_id)