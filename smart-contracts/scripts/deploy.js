/**
 * Echelon Protocol Deployment Script
 * ===================================
 * 
 * Deploys all Phase 2 contracts and wires permissions:
 * - TimelineShard.sol (ERC-1155 shards)
 * - SabotagePool.sol (FUD mechanics)
 * - HotPotatoEvents.sol (Hot Potato game)
 * - EchelonVRFConsumer.sol (Chainlink VRF)
 * 
 * Usage:
 *   npx hardhat run scripts/deploy.js --network baseSepolia
 *   npx hardhat run scripts/deploy.js --network polygonMumbai
 * 
 * Author: Echelon Protocol
 * Version: 1.0.0
 */

const hre = require("hardhat");

// =============================================================================
// NETWORK CONFIGURATIONS
// =============================================================================

const NETWORK_CONFIG = {
  baseSepolia: {
    name: "Base Sepolia",
    usdc: "0x036CbD53842c5426634e7929541eC2318f3dCF7e", // Test USDC
    vrfCoordinator: "0x8103B0A8A00be2DDC778e6e7eaa21791Cd364625",
    keyHash: "0x474e34a077df58807dbe9c96d3c009b23b3c6d0cce433e59bbf5b34f823bc56c",
    confirmations: 2,
  },
  polygonMumbai: {
    name: "Polygon Mumbai",
    usdc: "0xe11A86849d99F524cAC3E7A0Ec1241828e332C62", // Test USDC
    vrfCoordinator: "0x7a1BaC17Ccc5b313516C5E16fb24f7659aA5ebed",
    keyHash: "0x4b09e658ed251bcafeebbc69400383d49f344ace09b9576fe248bb02c003fe9f",
    confirmations: 5,
  },
  polygon: {
    name: "Polygon Mainnet",
    usdc: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // Real USDC
    vrfCoordinator: "0xAE975071Be8F8eE67addBC1A82488F1C24858067",
    keyHash: "0x6e099d640cde6de9d40ac749b4b594126b0169747122711109c9985d47751f93",
    confirmations: 10,
  },
  base: {
    name: "Base Mainnet",
    usdc: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", // Real USDC
    vrfCoordinator: "0xd5D517aBE5cF79B7e95eC98dB0f0277788aFF634",
    keyHash: "0x9e1344a1247c8a1785d0a4681a27152bffdb43666ae5bf7d14d24a5efd44bf71",
    confirmations: 10,
  },
};

// =============================================================================
// DEPLOYMENT FUNCTIONS
// =============================================================================

async function deployTimelineShard(usdcAddress, treasury, metadataUri) {
  console.log("\n📦 Deploying TimelineShard...");
  
  const TimelineShard = await hre.ethers.getContractFactory("TimelineShard");
  const shard = await TimelineShard.deploy(
    usdcAddress,
    6, // USDC decimals
    treasury,
    metadataUri
  );
  
  await shard.waitForDeployment();
  const address = await shard.getAddress();
  
  console.log(`✅ TimelineShard deployed to: ${address}`);
  return { contract: shard, address };
}

async function deploySabotagePool(shardAddress, usdcAddress) {
  console.log("\n📦 Deploying SabotagePool...");
  
  const SabotagePool = await hre.ethers.getContractFactory("SabotagePool");
  const sabotage = await SabotagePool.deploy(
    shardAddress,
    usdcAddress
  );
  
  await sabotage.waitForDeployment();
  const address = await sabotage.getAddress();
  
  console.log(`✅ SabotagePool deployed to: ${address}`);
  return { contract: sabotage, address };
}

async function deployHotPotato(shardAddress, usdcAddress, treasury) {
  console.log("\n📦 Deploying HotPotatoEvents...");
  
  const HotPotato = await hre.ethers.getContractFactory("HotPotatoEvents");
  const potato = await HotPotato.deploy(
    shardAddress,
    usdcAddress,
    treasury
  );
  
  await potato.waitForDeployment();
  const address = await potato.getAddress();
  
  console.log(`✅ HotPotatoEvents deployed to: ${address}`);
  return { contract: potato, address };
}

async function deployVRFConsumer(vrfCoordinator, subId, keyHash) {
  console.log("\n📦 Deploying EchelonVRFConsumer...");
  
  const VRFConsumer = await hre.ethers.getContractFactory("EchelonVRFConsumer");
  const vrf = await VRFConsumer.deploy(
    vrfCoordinator,
    subId,
    keyHash
  );
  
  await vrf.waitForDeployment();
  const address = await vrf.getAddress();
  
  console.log(`✅ EchelonVRFConsumer deployed to: ${address}`);
  return { contract: vrf, address };
}

// =============================================================================
// PERMISSION WIRING
// =============================================================================

async function wirePermissions(shard, sabotage, potato, vrf) {
  console.log("\n🔧 Wiring permissions...");
  
  // Get role hashes
  const TIMELINE_MANAGER_ROLE = await shard.contract.TIMELINE_MANAGER_ROLE();
  const DECAY_ROLE = await shard.contract.DECAY_ROLE();
  const REAPER_ROLE = await shard.contract.REAPER_ROLE();
  const AGENT_ROLE = await shard.contract.AGENT_ROLE();
  
  // VRF Consumer can trigger decay
  console.log("  - Granting DECAY_ROLE to VRF Consumer...");
  await shard.contract.grantRole(DECAY_ROLE, vrf.address);
  
  // VRF Consumer can reap timelines (OSINT kill)
  console.log("  - Granting REAPER_ROLE to VRF Consumer...");
  await shard.contract.grantRole(REAPER_ROLE, vrf.address);
  
  // Hot Potato can manage timelines
  console.log("  - Granting TIMELINE_MANAGER_ROLE to Hot Potato...");
  await shard.contract.grantRole(TIMELINE_MANAGER_ROLE, potato.address);
  
  // Sabotage Pool can interact with shards
  console.log("  - Granting AGENT_ROLE to Sabotage Pool...");
  await shard.contract.grantRole(AGENT_ROLE, sabotage.address);
  
  // Set references in VRF Consumer (if methods exist)
  try {
    console.log("  - Setting TimelineShard reference in VRF Consumer...");
    await vrf.contract.setTimelineShard(shard.address);
    
    console.log("  - Setting SabotagePool reference in VRF Consumer...");
    await vrf.contract.setSabotagePool(sabotage.address);
  } catch (e) {
    console.log("  ⚠️  VRF Consumer setter methods not found (may need manual configuration)");
  }
  
  console.log("✅ Permissions configured!");
}

// =============================================================================
// MAIN DEPLOYMENT
// =============================================================================

async function main() {
  console.log("🚀 Starting Echelon Protocol Deployment...");
  console.log("=".repeat(50));
  
  // Get network
  const network = hre.network.name;
  const config = NETWORK_CONFIG[network];
  
  if (!config) {
    console.error(`❌ Unknown network: ${network}`);
    console.log("Supported networks:", Object.keys(NETWORK_CONFIG).join(", "));
    process.exit(1);
  }
  
  console.log(`\n📡 Network: ${config.name}`);
  
  // Get deployer
  const [deployer] = await hre.ethers.getSigners();
  console.log(`👤 Deployer: ${deployer.address}`);
  
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`💰 Balance: ${hre.ethers.formatEther(balance)} ETH`);
  
  // Configuration
  const USDC_ADDRESS = process.env.USDC_ADDRESS || config.usdc;
  const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS || deployer.address;
  const VRF_SUB_ID = process.env.VRF_SUB_ID || "1234";
  const METADATA_URI = process.env.METADATA_URI || "https://api.echelon.market/metadata/";
  
  console.log(`\n⚙️  Configuration:`);
  console.log(`   USDC: ${USDC_ADDRESS}`);
  console.log(`   Treasury: ${TREASURY_ADDRESS}`);
  console.log(`   VRF Subscription: ${VRF_SUB_ID}`);
  console.log(`   Metadata URI: ${METADATA_URI}`);
  
  // Deploy contracts
  console.log("\n" + "=".repeat(50));
  console.log("DEPLOYING CONTRACTS");
  console.log("=".repeat(50));
  
  const shard = await deployTimelineShard(
    USDC_ADDRESS,
    TREASURY_ADDRESS,
    METADATA_URI
  );
  
  const sabotage = await deploySabotagePool(
    shard.address,
    USDC_ADDRESS
  );
  
  const potato = await deployHotPotato(
    shard.address,
    USDC_ADDRESS,
    TREASURY_ADDRESS
  );
  
  const vrf = await deployVRFConsumer(
    config.vrfCoordinator,
    VRF_SUB_ID,
    config.keyHash
  );
  
  // Wire permissions
  console.log("\n" + "=".repeat(50));
  console.log("WIRING PERMISSIONS");
  console.log("=".repeat(50));
  
  await wirePermissions(shard, sabotage, potato, vrf);
  
  // Output summary
  console.log("\n" + "=".repeat(50));
  console.log("🎉 DEPLOYMENT COMPLETE!");
  console.log("=".repeat(50));
  
  console.log("\n📋 Contract Addresses (add to .env):\n");
  console.log(`TIMELINE_SHARD_ADDRESS=${shard.address}`);
  console.log(`SABOTAGE_POOL_ADDRESS=${sabotage.address}`);
  console.log(`HOT_POTATO_ADDRESS=${potato.address}`);
  console.log(`VRF_CONSUMER_ADDRESS=${vrf.address}`);
  
  // Verification commands
  console.log("\n📝 Verification Commands:\n");
  console.log(`npx hardhat verify --network ${network} ${shard.address} "${USDC_ADDRESS}" 6 "${TREASURY_ADDRESS}" "${METADATA_URI}"`);
  console.log(`npx hardhat verify --network ${network} ${sabotage.address} "${shard.address}" "${USDC_ADDRESS}"`);
  console.log(`npx hardhat verify --network ${network} ${potato.address} "${shard.address}" "${USDC_ADDRESS}" "${TREASURY_ADDRESS}"`);
  console.log(`npx hardhat verify --network ${network} ${vrf.address} "${config.vrfCoordinator}" "${VRF_SUB_ID}" "${config.keyHash}"`);
  
  // Next steps
  console.log("\n📌 Next Steps:");
  console.log("1. Add contract addresses to your .env file");
  console.log("2. Fund VRF subscription at vrf.chain.link");
  console.log("3. Add VRF Consumer as consumer to your subscription");
  console.log("4. Verify contracts on block explorer");
  console.log("5. Update Python backend with contract addresses");
  
  return {
    timelineShard: shard.address,
    sabotagePool: sabotage.address,
    hotPotato: potato.address,
    vrfConsumer: vrf.address,
  };
}

// =============================================================================
// EXECUTE
// =============================================================================

main()
  .then((addresses) => {
    console.log("\n✅ Deployment successful!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n❌ Deployment failed:", error);
    process.exit(1);
  });

module.exports = { main };
