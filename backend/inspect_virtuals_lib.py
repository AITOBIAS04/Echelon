import virtuals_acp
import virtuals_acp.client
import pkgutil
import inspect

print("--- 📦 INSPECTING VIRTUALS SDK ---")

# 1. List everything in the main client module
print(f"\n[virtuals_acp.client] contains:")
for name, obj in inspect.getmembers(virtuals_acp.client):
    if inspect.isclass(obj):
        print(f" - Class: {name}")

# 2. Look for sub-packages (where the Contract Client might be hiding)
print(f"\n[Sub-modules in virtuals_acp]:")
package_path = virtuals_acp.__path__
for _, name, _ in pkgutil.iter_modules(package_path):
    print(f" - {name}")

# 3. Check contract_clients module
print(f"\n[Checking contract_clients module]:")
try:
    import virtuals_acp.contract_clients
    for name, obj in inspect.getmembers(virtuals_acp.contract_clients):
        if inspect.isclass(obj) and not name.startswith('_'):
            print(f" - Class: {name}")
            if issubclass(obj, virtuals_acp.client.BaseAcpContractClient) and obj != virtuals_acp.client.BaseAcpContractClient:
                print(f"   -> Concrete implementation of BaseAcpContractClient!")
                print(f"   -> __init__ signature: {inspect.signature(obj.__init__)}")
except Exception as e:
    print(f"   Error: {e}")

# 4. Check BaseAcpContractClient signature
print(f"\n[BaseAcpContractClient details]:")
from virtuals_acp.client import BaseAcpContractClient
print(f" - __init__ signature: {inspect.signature(BaseAcpContractClient.__init__)}")
print(f" - Is abstract: {inspect.isabstract(BaseAcpContractClient)}")

print("\n--------------------------------")

