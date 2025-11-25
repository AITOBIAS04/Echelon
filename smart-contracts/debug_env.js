const fs = require("fs");
const dotenv = require("dotenv");

// 1. Read the file directly to see what is physically written
try {
    const envFile = fs.readFileSync(".env");
    const envConfig = dotenv.parse(envFile);
    
    console.log("\n🔍 DEBUGGING YOUR .ENV FILE:");
    console.log("--------------------------------");
    console.log("Keys found inside .env:", Object.keys(envConfig));
    console.log("--------------------------------");

    // 2. Check specifically for the key we need
    if (envConfig.BASE_SEPOLIA_RPC_URL) {
        console.log("✅ BASE_SEPOLIA_RPC_URL is present.");
    } else {
        console.log("❌ BASE_SEPOLIA_RPC_URL is MISSING.");
        console.log("   (Did you name it SEPOLIA_RPC_URL by mistake?)");
    }
} catch (e) {
    console.log("❌ Error: Could not read .env file. Does it exist?");
}