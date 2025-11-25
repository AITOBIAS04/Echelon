import httpx

from virtuals_acp.client import VirtualsACP
from eth_account.messages import encode_defunct

async def fetch_paid_content(url: str, acp_client: VirtualsACP):
    """
    Fetches data from an x402-protected API.
    Automatically handles the '402 Payment Required' challenge using EIP-191 signing.
    """
    async with httpx.AsyncClient() as client:
        # 1. Try to get the data normally
        print(f"📡 Requesting content from: {url}")
        response = await client.get(url)

        # 2. If we get a 402 (Payment Required)
        if response.status_code == 402:
            print("💰 402 Payment Required! Initiating payment flow...")
            payment_request = response.json() 
            
            # 3. Sign the challenge
            # We use the first available contract client to sign
            contract_client = acp_client.acp_contract_clients[0]
            
            # Encode the message (EIP-191 standard)
            message_text = payment_request['message']
            eth_message = encode_defunct(text=message_text)
            
            # Sign with the underlying account
            print(f"✍️  Signing message: '{message_text}'")
            signed_message = contract_client.account.sign_message(eth_message)
            signature = signed_message.signature.hex()
            
            # 4. Retry with the payment authorization attached
            headers = {
                "Authorization": f"Signature {signature}",
                "X-Payment-Token": payment_request['token']
            }
            
            print("💸 Sending payment proof...")
            paid_response = await client.get(url, headers=headers)
            
            if paid_response.status_code == 200:
                print("✅ Payment accepted! Content unlocked.")
            else:
                print(f"❌ Payment failed: {paid_response.status_code}")
                
            return paid_response.json()
            
        return response.json()
