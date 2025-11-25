const hre = require("hardhat");

async function main() {
  // 1. Get the Subscription ID from .env
  const subscriptionId = process.env.SUBSCRIPTION_ID;
  
  if (!subscriptionId) {
    console.error("Error: SUBSCRIPTION_ID not found in .env file.");
    process.exit(1);
  }

  console.log("Deploying PredictionMarket with Subscription ID:", subscriptionId);

  // 2. Get the contract factory
  const PredictionMarket = await hre.ethers.getContractFactory("PredictionMarket");

  // 3. Deploy the contract (passing the ID to the constructor)
  const predictionMarket = await PredictionMarket.deploy(subscriptionId);

  // 4. Wait for it to be mined
  await predictionMarket.waitForDeployment();

  const address = await predictionMarket.getAddress();
  console.log(`SUCCESS! PredictionMarket deployed to: ${address}`);
  
  console.log("\nIMPORTANT NEXT STEP:");
  console.log(`Go to vrf.chain.link and ADD this address (${address}) as a 'Consumer' to your subscription!`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});