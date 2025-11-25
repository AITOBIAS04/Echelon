console.log("RPC URL:", process.env.BASE_SEPOLIA_RPC_URL);
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config(); // Load the .env file

// MAKE SURE THIS MATCHES YOUR .ENV EXACTLY
const BASE_SEPOLIA_RPC_URL = process.env.BASE_SEPOLIA_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;

module.exports = {
  solidity: "0.8.19",
  networks: {
    baseSepolia: {
      url: BASE_SEPOLIA_RPC_URL, // This was undefined before
      accounts: [PRIVATE_KEY],
      chainId: 84532,
    },
  },
};