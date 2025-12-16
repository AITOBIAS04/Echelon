# NPM Install Troubleshooting Guide

## Issue
npm install hangs when trying to install packages, including `@xyflow/react`.

## Solutions to Try

### Option 1: Use npm with timeout flags
```bash
cd frontend
npm install @xyflow/react --fetch-timeout=300000 --fetch-retries=2
```

### Option 2: Clear npm cache and retry
```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Option 3: Install with verbose logging to see where it hangs
```bash
cd frontend
npm install @xyflow/react --loglevel=verbose 2>&1 | tee npm-install.log
```
Then check `npm-install.log` to see where it's hanging.

### Option 4: Use a different registry temporarily
```bash
cd frontend
npm install @xyflow/react --registry=https://registry.npmjs.org/ --fetch-timeout=300000
```

### Option 5: Manual installation (if npm completely fails)
1. Download the package manually:
```bash
cd frontend
curl -L https://registry.npmjs.org/@xyflow/react/-/react-12.9.2.tgz -o xyflow-react.tgz
```

2. Extract and copy to node_modules:
```bash
mkdir -p node_modules/@xyflow/react
tar -xzf xyflow-react.tgz -C node_modules/@xyflow/react --strip-components=1
```

3. Update package-lock.json manually or run:
```bash
npm install --package-lock-only
```

### Option 6: Check for network/proxy issues
```bash
# Check if you can reach npm registry
curl -I https://registry.npmjs.org/

# Check npm config
npm config list

# Check for proxy settings
npm config get proxy
npm config get https-proxy
```

### Option 7: Reset npm configuration
```bash
# Backup current config
cp ~/.npmrc ~/.npmrc.backup

# Remove auth tokens (if any)
nano ~/.npmrc
# Remove lines with: _auth, _authToken, //registry.npmjs.org/:_authToken

# Try install again
cd frontend
npm install @xyflow/react
```

## Current Status
- ✅ Package is already in `package.json` as `"@xyflow/react": "^12.0.0"`
- ✅ npm registry is accessible (verified with curl)
- ✅ Package exists and is available
- ⚠️ npm install command hangs

## Recommended Next Steps
1. Try Option 1 first (timeout flags)
2. If that fails, try Option 2 (clean cache)
3. If still failing, use Option 5 (manual installation) as a workaround
4. Check npm logs for specific error messages

## Note
The NetworkGraph component will work once `@xyflow/react` is installed. Until then, you may see import errors, but the rest of the Situation Room integration should work fine.



