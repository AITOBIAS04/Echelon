/**
 * Deploy EchelonCommitment to Base Sepolia.
 *
 * Usage:
 *   npx hardhat run scripts/deploy_echelon_commitment.js --network baseSepolia
 *
 * Requires:
 *   BASE_SEPOLIA_RPC_URL and PRIVATE_KEY in .env
 */
const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying EchelonCommitment with account:", deployer.address);

  const EchelonCommitment = await ethers.getContractFactory(
    "EchelonCommitment"
  );
  const contract = await EchelonCommitment.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("EchelonCommitment deployed to:", address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
