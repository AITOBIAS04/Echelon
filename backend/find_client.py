import pkgutil
import inspect
import importlib
import virtuals_acp

# 1. Find the Abstract Base Class first
BaseClient = None
print("--- 🔍 SCANNING FOR BASE CLASS ---")
try:
    from virtuals_acp.client import BaseAcpContractClient
    BaseClient = BaseAcpContractClient
    print(f"✅ Found Base Class: {BaseAcpContractClient}")
    print(f"   📍 Location: {BaseAcpContractClient.__module__}")
    print(f"   🛠️ Constructor: {inspect.signature(BaseAcpContractClient.__init__)}")
    print(f"   🔒 Is Abstract: {inspect.isabstract(BaseAcpContractClient)}")
except ImportError as e:
    print(f"❌ Could not import BaseAcpContractClient: {e}")

# 2. Check if BaseAcpContractClient can be instantiated directly
print("\n--- 🧪 TESTING DIRECT INSTANTIATION ---")
try:
    from virtuals_acp.client import BASE_SEPOLIA_CONFIG
    # Try to create with dummy values
    test_client = BaseAcpContractClient("0x0000000000000000000000000000000000000000", BASE_SEPOLIA_CONFIG)
    print(f"✅ BaseAcpContractClient CAN be instantiated directly!")
except Exception as e:
    print(f"❌ Cannot instantiate directly: {e}")

# 3. Recursive Search for Subclasses
print("\n--- 🕵️ SCANNING FOR CONCRETE CLIENTS ---")
package = virtuals_acp
prefix = package.__name__ + "."

found_classes = []
for _, name, _ in pkgutil.walk_packages(package.__path__, prefix):
    try:
        module = importlib.import_module(name)
        for cls_name, cls_obj in inspect.getmembers(module):
            if inspect.isclass(cls_obj):
                # Check if it looks like a client
                if "ContractClient" in cls_name or "Client" in cls_name:
                    if BaseClient and issubclass(cls_obj, BaseClient) and cls_obj != BaseClient:
                        print(f"🎯 FOUND SUBCLASS: {cls_name}")
                        print(f"   📍 Import Path: {name}")
                        print(f"   🛠️ Constructor args: {inspect.signature(cls_obj.__init__)}")
                        found_classes.append((name, cls_name))
                    elif "ContractClient" in cls_name and cls_name != "BaseAcpContractClient":
                        print(f"🎯 FOUND CANDIDATE: {cls_name}")
                        print(f"   📍 Import Path: {name}")
                        print(f"   🛠️ Constructor args: {inspect.signature(cls_obj.__init__)}")
                        found_classes.append((name, cls_name))
    except Exception as e:
        continue

# 4. Check for factory functions
print("\n--- 🏭 CHECKING FOR FACTORY FUNCTIONS ---")
try:
    from virtuals_acp.client import VirtualsACP
    for name, obj in inspect.getmembers(VirtualsACP):
        if "factory" in name.lower() or "create" in name.lower():
            print(f"🏭 Found factory method: {name}")
except Exception as e:
    print(f"Error checking factory: {e}")

if not found_classes:
    print("\n⚠️ No concrete implementations found. BaseAcpContractClient may be instantiated directly.")

