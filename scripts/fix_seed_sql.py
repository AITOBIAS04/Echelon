#!/usr/bin/env python3
"""
Fix seed_v2.sql to match the actual database schema.
"""

import re

# Read the original SQL file
with open('seed_v2.sql', 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix 1: hashed_password -> password_hash
    line = line.replace('hashed_password', 'password_hash')
    
    # Fix 2: Remove is_active from users INSERT
    if 'INSERT INTO users' in line and 'is_active' in line:
        # Remove is_active from column list
        line = line.replace(', is_active', '')
        # Find the corresponding VALUES line and remove the true value
        if i + 1 < len(lines) and 'VALUES' in lines[i + 1]:
            # Look ahead for the true value
            for j in range(i + 2, min(i + 10, len(lines))):
                if 'true' in lines[j] and ');' in lines[j]:
                    lines[j] = lines[j].replace(', true', '').replace('true,', '').replace('true', '')
                    break
    
    # Fix 3: Remove generation from agents
    line = line.replace(', generation,', ',')
    if 'INSERT INTO agents' in line and 'generation' in line:
        line = line.replace('generation,', '')
    
    # Fix 4: Remove slug, category, founder_name from timelines
    if 'INSERT INTO timelines' in line:
        line = line.replace(', slug,', ',')
        line = line.replace(', category,', ',')
        line = line.replace(', founder_name,', ',')
        line = line.replace(', status,', ', is_active,')
    
    # Fix 5: Remove status value and replace with is_active boolean
    if "'ACTIVE'" in line or "'INACTIVE'" in line:
        line = line.replace("'ACTIVE'", 'true')
        line = line.replace("'INACTIVE'", 'false')
    
    # Fix 6: Remove created_at, updated_at from paradoxes
    if 'INSERT INTO paradoxes' in line:
        line = line.replace(', created_at, updated_at', '')
    
    # Fix 7: created_at -> timestamp for wing_flaps
    if 'INSERT INTO wing_flaps' in line:
        line = line.replace(', created_at', ', timestamp')
    
    # Fix 8: positions -> user_positions
    line = line.replace('DELETE FROM positions;', 'DELETE FROM user_positions;')
    line = line.replace('INSERT INTO positions (', 'INSERT INTO user_positions (')
    
    # Fix 9: Fix user_positions column names
    if 'INSERT INTO user_positions' in line:
        line = line.replace('agent_id,', 'user_id,')
        line = line.replace('shares,', 'shards_held,')
        line = line.replace('average_price,', 'average_entry_price,')
        line = line.replace('current_value, unrealised_pnl,', '')
    
    # Fix 10: Remove founder_name values from timeline inserts
    # This is complex - need to find the value after founder_id
    if 'INSERT INTO timelines' in line or (i > 0 and 'INSERT INTO timelines' in lines[i-1]):
        # Look for founder_name value pattern
        if "'" in line and any(name in line for name in ['CARDINAL', 'RAVEN', 'MEGALODON', 'LEVIATHAN', 'THRESHER', 'ENVOY', 'ARBITER', 'ORACLE', 'VIPER']):
            # This is likely a founder_name value, skip it
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('--'):
                # Check if next line is a value
                next_line = lines[i + 1]
                if any(name in next_line for name in ['CARDINAL', 'RAVEN', 'MEGALODON', 'LEVIATHAN', 'THRESHER', 'ENVOY', 'ARBITER', 'ORACLE', 'VIPER']):
                    # Skip this line (founder_name value)
                    i += 1
                    continue
    
    # Fix 11: Remove slug, category values
    if any(slug in line for slug in ['ghost-tanker', 'tehran-blackout', 'hormuz-chokepoint', 'fed-pivot', 'nvidia-earnings', 'openai-exodus', 'apple-ai-pivot', 'eth-etf-approval', 'tether-collapse', 'antarctic-shelf']):
        # This is likely a slug value, check context
        if i > 0 and 'INSERT INTO timelines' in ''.join(lines[max(0, i-5):i]):
            # Skip slug line
            i += 1
            continue
    
    if any(cat in line for cat in ["'GEOPOLITICAL'", "'FINANCIAL'", "'TECH'", "'CRYPTO'", "'SCIENCE'"]):
        # This is likely a category value, skip it
        i += 1
        continue
    
    # Fix 12: Remove current_value and unrealised_pnl values from positions
    if 'INSERT INTO user_positions' in ''.join(lines[max(0, i-2):i+2]):
        # Count commas to find which value to remove
        if re.search(r'\d+,\s*-- current_value', line):
            line = re.sub(r',\s*\d+,\s*-- current_value', '', line)
        if re.search(r'[\d.-]+,\s*-- unrealised_pnl', line):
            line = re.sub(r',\s*[\d.-]+,\s*-- unrealised_pnl', '', line)
    
    # Fix 13: Remove created_at, updated_at values from paradoxes
    if 'INSERT INTO paradoxes' in ''.join(lines[max(0, i-5):i]):
        if 'NOW(),' in line and 'NOW()' in line:
            # Remove both NOW() calls
            line = re.sub(r',\s*NOW\(\),\s*NOW\(\)', '', line)
    
    fixed_lines.append(line)
    i += 1

# Write fixed file
with open('seed_v2_fixed.sql', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Created seed_v2_fixed.sql")
print("⚠️  Note: Some manual fixes may still be needed. Please review the file.")


