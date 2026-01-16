-- Echelon Database Seed Script v2
-- Generated: 2025-12-26T20:49:15.731047
-- WARNING: This will clear existing data!

-- Clear existing data
DELETE FROM wing_flaps;
DELETE FROM paradoxes;
DELETE FROM user_positions;
DELETE FROM timelines;
DELETE FROM agents;
DELETE FROM users WHERE username != 'admin';

-- Insert sample users

INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    '179c7292-1dcd-47e8-a001-05ca753e6060',
    'whale_watcher',
    'whale@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IiC',
    NOW(),
    NOW(),
    true
);

INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    'ff96a49c-6616-47f3-b3f1-cd89f03d9880',
    'degen_dan',
    'dan@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IiC',
    NOW(),
    NOW(),
    true
);

INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    '208a6b38-7633-44b1-a467-068444645429',
    'intel_insider',
    'intel@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IiC',
    NOW(),
    NOW(),
    true
);

INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    'b88b8bb8-45dc-442a-ac7d-457893182646',
    'steady_eddie',
    'eddie@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IiC',
    NOW(),
    NOW(),
    true
);

INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
VALUES (
    '3b5c2ffa-0a9c-4fa5-b456-f7aa139bff82',
    'chaos_charlie',
    'charlie@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/IiC',
    NOW(),
    NOW(),
    true
);

-- Insert genesis agents

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    'MEGALODON',
    'SHARK',
    3,
    15,
    85,
    100,
    125000.0,
    0.67,
    847,
    NULL,
    '0xb835d4b78f5942e3a325d179756875d4',
    '{"aggression": 0.9, "patience": 0.2, "risk_tolerance": 0.95}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'THRESHER',
    'SHARK',
    2,
    8,
    72,
    100,
    45000.0,
    0.58,
    423,
    NULL,
    '0xcdb9435dcff540e79e5ddd5685921729',
    '{"aggression": 0.75, "patience": 0.35, "risk_tolerance": 0.8}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '6c705bf5-1528-4be6-9143-bf0173137eeb',
    'HAMMERHEAD',
    'SHARK',
    2,
    6,
    68,
    100,
    28000.0,
    0.52,
    312,
    NULL,
    '0x10798767e83748389aa69717549594bb',
    '{"aggression": 0.85, "patience": 0.15, "risk_tolerance": 0.88}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'CARDINAL',
    'SPY',
    3,
    12,
    78,
    100,
    67000.0,
    0.71,
    234,
    NULL,
    '0xbdd6b932d00942568e947a40d62f3bfd',
    '{"aggression": 0.3, "patience": 0.8, "risk_tolerance": 0.4, "intel_accuracy": 0.85}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'RAVEN',
    'SPY',
    2,
    7,
    82,
    100,
    34000.0,
    0.64,
    156,
    NULL,
    '0xcaae30dfe252484f8aad5830ae5a0f82',
    '{"aggression": 0.25, "patience": 0.85, "risk_tolerance": 0.35, "intel_accuracy": 0.78}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'ENVOY',
    'DIPLOMAT',
    3,
    10,
    92,
    100,
    52000.0,
    0.75,
    189,
    NULL,
    '0xd42da6a830814ecba63a17281534f4d5',
    '{"aggression": 0.15, "patience": 0.95, "risk_tolerance": 0.25, "treaty_success": 0.82}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    'accba501-dea4-478f-af3b-77def5e8352f',
    'ARBITER',
    'DIPLOMAT',
    2,
    5,
    88,
    100,
    23000.0,
    0.68,
    98,
    NULL,
    '0xf86abc9086af4cf799fda700ceb7ab93',
    '{"aggression": 0.2, "patience": 0.9, "risk_tolerance": 0.3, "treaty_success": 0.72}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '241880b0-ed34-402d-a0c8-41df3f1577f5',
    'VIPER',
    'SABOTEUR',
    3,
    11,
    45,
    100,
    89000.0,
    0.54,
    567,
    NULL,
    '0xe62a54aa093a4e98801a4d2483699669',
    '{"aggression": 0.95, "patience": 0.1, "risk_tolerance": 0.98, "chaos_factor": 0.9}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '86662478-d469-4a99-b653-d7ede05817bf',
    'SPECTER',
    'SABOTEUR',
    2,
    6,
    52,
    100,
    31000.0,
    0.48,
    289,
    NULL,
    '0xd790e0bcfc7240caa0a813ff0dcb5c87',
    '{"aggression": 0.88, "patience": 0.2, "risk_tolerance": 0.92, "chaos_factor": 0.75}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'LEVIATHAN',
    'WHALE',
    3,
    14,
    75,
    100,
    342000.0,
    0.62,
    87,
    NULL,
    '0xb14c623d588249a1af25b075df2c846d',
    '{"aggression": 0.6, "patience": 0.7, "risk_tolerance": 0.7, "market_impact": 0.95}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'ORACLE',
    'DEGEN',
    2,
    4,
    35,
    100,
    -12000.0,
    0.47,
    1247,
    NULL,
    '0x68a1bf91be2443e087ce358dda1160bd',
    '{"aggression": 0.5, "patience": 0.05, "risk_tolerance": 1.0, "luck_factor": 0.5}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

INSERT INTO agents (
    id, name, archetype, tier, level, sanity, max_sanity,
    total_pnl_usd, win_rate, trades_count, owner_id,
    wallet_address, genome, is_alive, created_at, updated_at
)
VALUES (
    'ce4f59f9-f583-410f-9e3a-c2a8db14d232',
    'PHOENIX',
    'DEGEN',
    1,
    3,
    28,
    100,
    -8000.0,
    0.43,
    892,
    NULL,
    '0x93a0340626144d328b7e5bee76708d7b',
    '{"aggression": 0.6, "patience": 0.1, "risk_tolerance": 0.95, "luck_factor": 0.6}'::jsonb,
    1,
    true,
    NOW(),
    NOW()
);

-- Insert timelines

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    'Ghost Tanker',
    'ghost-tanker',
    'What if the dark fleet tanker NIOVI reached Shanghai without detection?',
    '["oil", "tanker", "sanctions", "china", "venezuela"]'::jsonb,
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'CARDINAL',
    67.5,
    69.3,
    0.45,
    0.55,
    125000.0,
    37500.00,
    52.0,
    7.0,
    8.3,
    4,
    1.2,
    false,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    'Tehran Blackout',
    'tehran-blackout',
    'What if the power grid failure in Tehran was a cyber attack, not equipment failure?',
    '["iran", "cyber", "infrastructure", "blackout", "attack"]'::jsonb,
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'RAVEN',
    72.3,
    69.9,
    0.62,
    0.38,
    89000.0,
    26700.00,
    58.0,
    4.0,
    3.7,
    2,
    1.0,
    true,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    'Hormuz Chokepoint',
    'hormuz-chokepoint',
    'What if Iran closed the Strait of Hormuz for 72 hours?',
    '["iran", "oil", "strait", "hormuz", "shipping"]'::jsonb,
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    'MEGALODON',
    54.8,
    77.9,
    0.28,
    0.72,
    234000.0,
    70200.00,
    22.0,
    6.0,
    4.8,
    6,
    1.5,
    false,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    'Fed Pivot',
    'fed-pivot',
    'What if the Fed cut 50bps instead of 25bps in December?',
    '["fed", "rates", "monetary", "powell", "economy"]'::jsonb,
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'LEVIATHAN',
    81.2,
    63.2,
    0.73,
    0.27,
    456000.0,
    136800.00,
    68.0,
    5.0,
    4.7,
    6,
    0.8,
    true,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '739b1057-067f-424e-9b94-1fc20bf33363',
    'NVIDIA Earnings',
    'nvidia-earnings',
    'What if NVIDIA missed earnings by 20%+ due to China export controls?',
    '["nvidia", "ai", "chips", "china", "earnings"]'::jsonb,
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'THRESHER',
    76.4,
    73.8,
    0.18,
    0.82,
    178000.0,
    53400.00,
    15.0,
    3.0,
    8.0,
    2,
    1.0,
    true,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    'OpenAI Exodus',
    'openai-exodus',
    'What if 50%+ of OpenAI researchers left for Anthropic?',
    '["openai", "anthropic", "ai", "talent", "exodus"]'::jsonb,
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'CARDINAL',
    68.9,
    50.0,
    0.34,
    0.66,
    67000.0,
    20100.00,
    28.0,
    6.0,
    3.4,
    7,
    1.1,
    true,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'Apple AI Pivot',
    'apple-ai-pivot',
    'What if Apple acquired Anthropic for $50B+?',
    '["apple", "anthropic", "ai", "acquisition", "tech"]'::jsonb,
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'ENVOY',
    85.1,
    75.3,
    0.12,
    0.88,
    45000.0,
    13500.00,
    8.0,
    4.0,
    6.2,
    7,
    0.7,
    false,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    'ETH ETF Approval',
    'eth-etf-approval',
    'What if ETH ETF was approved with staking rewards included?',
    '["ethereum", "etf", "sec", "staking", "crypto"]'::jsonb,
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'ORACLE',
    62.3,
    79.4,
    0.56,
    0.44,
    312000.0,
    93600.00,
    48.0,
    8.0,
    8.6,
    7,
    1.3,
    true,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'Tether Collapse',
    'tether-collapse',
    'What if Tether lost its peg for 24+ hours?',
    '["tether", "usdt", "stablecoin", "depeg", "crypto"]'::jsonb,
    '241880b0-ed34-402d-a0c8-41df3f1577f5',
    'VIPER',
    45.6,
    56.1,
    0.08,
    0.92,
    567000.0,
    170100.00,
    5.0,
    3.0,
    4.8,
    6,
    2.0,
    false,
    true,
    NOW(),
    NOW()
);

INSERT INTO timelines (
    id, name, slug, narrative, keywords, category,
    founder_id, founder_name, stability, surface_tension,
    price_yes, price_no, total_volume_usd, liquidity_depth_usd,
    osint_alignment, logic_gap, gravity_score,
    active_agent_count, decay_rate_per_hour,
    has_active_paradox, status, created_at, updated_at
)
VALUES (
    '6e062ef2-6422-4544-96c5-b66463c6031d',
    'Antarctic Shelf',
    'antarctic-shelf',
    'What if the Thwaites Glacier collapsed 10 years earlier than predicted?',
    '["climate", "antarctica", "glacier", "sea level", "disaster"]'::jsonb,
    'accba501-dea4-478f-af3b-77def5e8352f',
    'ARBITER',
    78.9,
    78.8,
    0.22,
    0.78,
    34000.0,
    10200.00,
    18.0,
    4.0,
    4.8,
    4,
    0.5,
    false,
    true,
    NOW(),
    NOW()
);

-- Insert active paradoxes

INSERT INTO paradoxes (
    id, timeline_id, status, severity_class,
    logic_gap, spawned_at, detonation_time,
    decay_multiplier, extraction_cost_usdc, extraction_cost_echelon,
    carrier_sanity_cost, created_at, updated_at
)
VALUES (
    'b5649e7c-b4a5-4df1-9f88-327923371a34',
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    true,
    'CLASS_3_MODERATE',
    7.0,
    NOW() - INTERVAL '2 hours',
    NOW() + INTERVAL '5 hours',
    2.1,
    428,
    163,
    10,
    NOW(),
    NOW()
);

INSERT INTO paradoxes (
    id, timeline_id, status, severity_class,
    logic_gap, spawned_at, detonation_time,
    decay_multiplier, extraction_cost_usdc, extraction_cost_echelon,
    carrier_sanity_cost, created_at, updated_at
)
VALUES (
    '54553a29-2934-4d81-a4fd-f980c05b37ea',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    true,
    'CLASS_3_MODERATE',
    6.0,
    NOW() - INTERVAL '4 hours',
    NOW() + INTERVAL '11 hours',
    2.1,
    394,
    153,
    13,
    NOW(),
    NOW()
);

INSERT INTO paradoxes (
    id, timeline_id, status, severity_class,
    logic_gap, spawned_at, detonation_time,
    decay_multiplier, extraction_cost_usdc, extraction_cost_echelon,
    carrier_sanity_cost, created_at, updated_at
)
VALUES (
    'd27cb108-99a2-4d8e-b65e-9651071364e8',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    true,
    'CLASS_3_MODERATE',
    6.0,
    NOW() - INTERVAL '2 hours',
    NOW() + INTERVAL '11 hours',
    2.1,
    409,
    142,
    10,
    NOW(),
    NOW()
);

-- Insert recent wing flaps

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '97a3ba0c-25c8-4546-8832-1b96a6cda645',
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    'TRADE',
    'MEGALODON opened YES position on Fed Pivot',
    0.46,
    'ANCHOR',
    7941,
    81.7,
    0.73,
    true,
    NOW() - INTERVAL '379 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '6c19a0e9-244f-4546-8a4b-4fdd7b371c4f',
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'RIPPLE',
    'Cascade from NVIDIA Earnings affected Fed Pivot',
    -1.32,
    'DESTABILISE',
    9254,
    79.9,
    0.73,
    true,
    NOW() - INTERVAL '231 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '937ea382-03b8-416b-8d52-9e1500c918cf',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'TRADE',
    'ARBITER closed position with $1373 P&L',
    -2.29,
    'DESTABILISE',
    7174,
    43.3,
    0.08,
    false,
    NOW() - INTERVAL '614 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '4986540c-0685-43ec-8cc4-c4fb09ecb6f9',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'SHIELD',
    'ARBITER deployed shield on Apple AI Pivot',
    8.21,
    'ANCHOR',
    325,
    93.3,
    0.12,
    true,
    NOW() - INTERVAL '16 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'a364922d-0d82-4dd4-8c40-d646eba987a1',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'ENTROPY',
    'Natural decay on OpenAI Exodus',
    -1.79,
    'DESTABILISE',
    5042,
    67.1,
    0.34,
    false,
    NOW() - INTERVAL '260 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '2be03f92-c873-4be0-9b05-ac1db5283d86',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'ENTROPY',
    'Natural decay on Hormuz Chokepoint',
    -1.98,
    'DESTABILISE',
    648,
    52.8,
    0.28,
    false,
    NOW() - INTERVAL '692 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '5a96efdb-2530-414f-82e9-cf8a23be476c',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'SHIELD',
    'ORACLE deployed shield on ETH ETF Approval',
    8.49,
    'ANCHOR',
    6905,
    70.8,
    0.56,
    true,
    NOW() - INTERVAL '536 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'd715c839-e9b0-4ef1-a58e-92bf604eaf07',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '86662478-d469-4a99-b653-d7ede05817bf',
    'ENTROPY',
    'Natural decay on ETH ETF Approval',
    -0.59,
    'DESTABILISE',
    8866,
    61.7,
    0.56,
    true,
    NOW() - INTERVAL '623 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '68edf95c-1c54-4f3f-acac-419f89d3e49a',
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'TRADE',
    'ORACLE opened YES position on Tehran Blackout',
    7.26,
    'ANCHOR',
    1485,
    79.6,
    0.62,
    true,
    NOW() - INTERVAL '289 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '52a33100-7b97-49eb-8ee1-61452097c1ac',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'SHIELD',
    'THRESHER deployed shield on Hormuz Chokepoint',
    4.60,
    'ANCHOR',
    5503,
    59.4,
    0.28,
    false,
    NOW() - INTERVAL '143 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '414d68f2-bf25-4d32-b403-0a291b377f5d',
    '739b1057-067f-424e-9b94-1fc20bf33363',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'TRADE',
    'THRESHER closed position with $1421 P&L',
    -2.80,
    'DESTABILISE',
    383,
    73.6,
    0.18,
    false,
    NOW() - INTERVAL '85 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '0b41323f-b890-47b0-8a2b-f1201e726855',
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'ENTROPY',
    'Natural decay on Tehran Blackout',
    -1.81,
    'DESTABILISE',
    5694,
    70.5,
    0.62,
    true,
    NOW() - INTERVAL '419 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'f14db4d2-f028-4fc1-a568-9be41554840f',
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    '241880b0-ed34-402d-a0c8-41df3f1577f5',
    'RIPPLE',
    'Cascade from Fed Pivot affected Fed Pivot',
    0.32,
    'ANCHOR',
    3005,
    81.5,
    0.73,
    true,
    NOW() - INTERVAL '6 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'fa75b073-9d29-42bc-9219-6f0cc341fe12',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'TRADE',
    'ENVOY closed position with $1698 P&L',
    0.96,
    'ANCHOR',
    4312,
    86.1,
    0.12,
    false,
    NOW() - INTERVAL '613 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'a64bb7c4-de18-49a2-8507-8b44e59152a5',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    '86662478-d469-4a99-b653-d7ede05817bf',
    'ENTROPY',
    'Natural decay on Hormuz Chokepoint',
    -0.68,
    'DESTABILISE',
    825,
    54.1,
    0.28,
    true,
    NOW() - INTERVAL '672 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '2b4debab-c2e9-4ab1-8e7a-c223fa459182',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'ce4f59f9-f583-410f-9e3a-c2a8db14d232',
    'TRADE',
    'PHOENIX opened YES position on Apple AI Pivot',
    6.52,
    'ANCHOR',
    5812,
    91.6,
    0.12,
    false,
    NOW() - INTERVAL '284 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '7579297d-0061-4f1e-a0b7-0e6f96242e7a',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'TRADE',
    'LEVIATHAN closed position with $-313 P&L',
    -0.40,
    'DESTABILISE',
    1370,
    84.7,
    0.12,
    true,
    NOW() - INTERVAL '377 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '883f6bb6-1cc3-4536-8d56-1f30e0745ab2',
    '6e062ef2-6422-4544-96c5-b66463c6031d',
    '6c705bf5-1528-4be6-9143-bf0173137eeb',
    'TRADE',
    'HAMMERHEAD opened NO position on Antarctic Shelf',
    -2.41,
    'DESTABILISE',
    1124,
    76.5,
    0.22,
    false,
    NOW() - INTERVAL '558 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'e550e52e-0b27-4596-9471-e64574f5b837',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'RIPPLE',
    'Cascade from Antarctic Shelf affected ETH ETF Approval',
    2.92,
    'ANCHOR',
    1907,
    65.2,
    0.56,
    true,
    NOW() - INTERVAL '574 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'de3510cc-e8e9-4991-abb9-5da493d2077d',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    'SABOTAGE',
    'MEGALODON attacked Tether Collapse',
    -7.29,
    'DESTABILISE',
    7106,
    38.3,
    0.08,
    false,
    NOW() - INTERVAL '719 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'f18e3c40-5688-41ab-ba8a-6f5dbd4d5011',
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'SHIELD',
    'ORACLE deployed shield on Tehran Blackout',
    9.09,
    'ANCHOR',
    4742,
    81.4,
    0.62,
    false,
    NOW() - INTERVAL '636 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '2c691e1f-3cd0-4fcb-b1df-c7dd52c01221',
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'ENTROPY',
    'Natural decay on Fed Pivot',
    -1.25,
    'DESTABILISE',
    981,
    79.9,
    0.73,
    true,
    NOW() - INTERVAL '256 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '88a96ea6-1093-4d67-bf46-440a6c926d19',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '86662478-d469-4a99-b653-d7ede05817bf',
    'TRADE',
    'SPECTER closed position with $-190 P&L',
    0.76,
    'ANCHOR',
    2021,
    63.1,
    0.56,
    true,
    NOW() - INTERVAL '224 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'ad2b5766-7e70-4e13-b362-5befbd6fd648',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'TRADE',
    'RAVEN closed position with $-391 P&L',
    2.45,
    'ANCHOR',
    7540,
    64.7,
    0.56,
    false,
    NOW() - INTERVAL '371 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'b8e18c82-c07a-4161-9c29-dfe26807132e',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'SHIELD',
    'THRESHER deployed shield on OpenAI Exodus',
    2.59,
    'ANCHOR',
    6063,
    71.5,
    0.34,
    false,
    NOW() - INTERVAL '613 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '08c129ad-e977-4ecf-9e1b-7c98de2c5072',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    '241880b0-ed34-402d-a0c8-41df3f1577f5',
    'RIPPLE',
    'Cascade from Ghost Tanker affected Hormuz Chokepoint',
    1.90,
    'ANCHOR',
    2890,
    56.7,
    0.28,
    false,
    NOW() - INTERVAL '655 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '1de81f1a-afc3-468a-87fc-e416c4a73829',
    '6e062ef2-6422-4544-96c5-b66463c6031d',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'ENTROPY',
    'Natural decay on Antarctic Shelf',
    -1.71,
    'DESTABILISE',
    866,
    77.2,
    0.22,
    false,
    NOW() - INTERVAL '273 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'c1cd3b93-6ba2-4c4c-ac33-4a2fd1f891b8',
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'RIPPLE',
    'Cascade from NVIDIA Earnings affected Ghost Tanker',
    0.82,
    'ANCHOR',
    738,
    68.3,
    0.45,
    false,
    NOW() - INTERVAL '54 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'f4625487-b0e0-4d8b-98c6-52d87e3b91bb',
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'SHIELD',
    'THRESHER deployed shield on Tehran Blackout',
    3.22,
    'ANCHOR',
    8604,
    75.5,
    0.62,
    false,
    NOW() - INTERVAL '218 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '075d1ce5-fa19-43e4-baaf-d177efc49317',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    'ce4f59f9-f583-410f-9e3a-c2a8db14d232',
    'SHIELD',
    'PHOENIX deployed shield on ETH ETF Approval',
    4.01,
    'ANCHOR',
    1850,
    66.3,
    0.56,
    true,
    NOW() - INTERVAL '688 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '2555a907-18a2-446e-8e86-150c3b87efc1',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '0d27952f-7d3b-46a2-bbcb-129b6b5d61ad',
    'TRADE',
    'ORACLE opened YES position on Apple AI Pivot',
    0.33,
    'ANCHOR',
    9291,
    85.4,
    0.12,
    true,
    NOW() - INTERVAL '350 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '7d0bd646-18ca-4271-a609-8e3f8f764845',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'TRADE',
    'CARDINAL opened YES position on Tether Collapse',
    -1.25,
    'DESTABILISE',
    4429,
    44.3,
    0.08,
    true,
    NOW() - INTERVAL '704 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '765d7aa8-b0fc-4478-9392-22a325daa3a2',
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'RIPPLE',
    'Cascade from Hormuz Chokepoint affected Ghost Tanker',
    0.57,
    'ANCHOR',
    6588,
    68.1,
    0.45,
    false,
    NOW() - INTERVAL '573 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'bee00410-3da4-445c-8c0d-a2c584ca629a',
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'ENTROPY',
    'Natural decay on Ghost Tanker',
    -1.96,
    'DESTABILISE',
    2512,
    65.5,
    0.45,
    false,
    NOW() - INTERVAL '26 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '3451a804-1936-4097-a7a5-692d2b8d1249',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'TRADE',
    'CARDINAL opened YES position on ETH ETF Approval',
    0.44,
    'ANCHOR',
    8341,
    62.7,
    0.56,
    false,
    NOW() - INTERVAL '14 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '7f92f4a0-6506-41f7-a057-68799fb222cf',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'TRADE',
    'LEVIATHAN closed position with $1285 P&L',
    -1.65,
    'DESTABILISE',
    9258,
    83.5,
    0.12,
    true,
    NOW() - INTERVAL '458 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '260e5fff-44ee-42d4-a084-8c3912c37329',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'ENTROPY',
    'Natural decay on Apple AI Pivot',
    -0.86,
    'DESTABILISE',
    1177,
    84.2,
    0.12,
    false,
    NOW() - INTERVAL '339 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'ef98cc02-e299-42f3-8e32-3632f9ef95c3',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'TRADE',
    'ARBITER closed position with $-67 P&L',
    1.75,
    'ANCHOR',
    4382,
    47.4,
    0.08,
    true,
    NOW() - INTERVAL '476 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '36bc411f-f156-4e6e-8bf7-51137a2eb7ef',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'ENTROPY',
    'Natural decay on Apple AI Pivot',
    -0.89,
    'DESTABILISE',
    4226,
    84.2,
    0.12,
    true,
    NOW() - INTERVAL '482 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'a6f5ac64-5b6a-4215-a228-78fe914e185e',
    '9602b4a3-f7cd-4651-825c-0ae9d8dfb3ea',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'SABOTAGE',
    'ENVOY attacked Ghost Tanker',
    -12.68,
    'DESTABILISE',
    7806,
    54.8,
    0.45,
    false,
    NOW() - INTERVAL '140 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'ad77b6ff-5000-4cda-869b-61b35caa16f9',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'SHIELD',
    'RAVEN deployed shield on Tether Collapse',
    3.17,
    'ANCHOR',
    2967,
    48.8,
    0.08,
    true,
    NOW() - INTERVAL '490 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'fa2c8663-0544-44dd-88ea-60f47502e2e1',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'accba501-dea4-478f-af3b-77def5e8352f',
    'ENTROPY',
    'Natural decay on Tether Collapse',
    -0.95,
    'DESTABILISE',
    7456,
    44.7,
    0.08,
    true,
    NOW() - INTERVAL '298 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '9b93c6e3-3bfa-4084-a4f5-3a681c73ade4',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'RIPPLE',
    'Cascade from Ghost Tanker affected OpenAI Exodus',
    -2.79,
    'DESTABILISE',
    7588,
    66.1,
    0.34,
    false,
    NOW() - INTERVAL '247 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'e2ccd8da-84f4-427f-a750-036c493df0b9',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '330eecda-c60e-4d72-8c0d-83cb8da2d131',
    'TRADE',
    'LEVIATHAN closed position with $281 P&L',
    4.55,
    'ANCHOR',
    8310,
    66.8,
    0.56,
    true,
    NOW() - INTERVAL '153 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'd2462c49-b8b9-466f-8eb4-32acc6bd773c',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    'TRADE',
    'MEGALODON opened YES position on Apple AI Pivot',
    -1.89,
    'DESTABILISE',
    9866,
    83.2,
    0.12,
    true,
    NOW() - INTERVAL '666 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '21574fac-7d3c-4076-aea8-96f2302d8f74',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    '6c705bf5-1528-4be6-9143-bf0173137eeb',
    'RIPPLE',
    'Cascade from Tehran Blackout affected Apple AI Pivot',
    -1.42,
    'DESTABILISE',
    6954,
    83.7,
    0.12,
    true,
    NOW() - INTERVAL '242 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    'c7407faa-30a0-4fce-8044-f1e107a3bad0',
    '739b1057-067f-424e-9b94-1fc20bf33363',
    'ce4f59f9-f583-410f-9e3a-c2a8db14d232',
    'TRADE',
    'PHOENIX opened YES position on NVIDIA Earnings',
    1.18,
    'ANCHOR',
    5950,
    77.6,
    0.18,
    true,
    NOW() - INTERVAL '198 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '1658cb3f-5f84-4493-9637-d75c05560894',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    'TRADE',
    'ENVOY closed position with $-453 P&L',
    -2.27,
    'DESTABILISE',
    9872,
    60.0,
    0.56,
    true,
    NOW() - INTERVAL '353 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '3ab92c78-cf51-4346-853c-045fceb89140',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'SHIELD',
    'CARDINAL deployed shield on OpenAI Exodus',
    9.48,
    'ANCHOR',
    7198,
    78.4,
    0.34,
    true,
    NOW() - INTERVAL '365 minutes'
);

INSERT INTO wing_flaps (
    id, timeline_id, agent_id, flap_type, action,
    stability_delta, direction, volume_usd,
    timeline_stability, timeline_price,
    spawned_ripple, created_at
)
VALUES (
    '40f540b3-6909-49dc-be4f-2bda68a5d840',
    '4b160663-a275-4a44-a2a6-5e2df9407b72',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    'TRADE',
    'THRESHER opened NO position on OpenAI Exodus',
    2.81,
    'ANCHOR',
    3985,
    71.7,
    0.34,
    false,
    NOW() - INTERVAL '557 minutes'
);

-- Insert agent positions

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '493b01e8-af5c-4921-a39f-f4f1ab2b66d6',
    '4fcd89ea-f3de-4f27-99b7-8aa7a59f128c',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'NO',
    450,
    0.41,
    3882,
    463,
    NOW() - INTERVAL '41 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '4f5f0019-0ca0-4e59-8bb2-5e45be8332bb',
    '8e056d6e-0f8b-4257-ab90-e5668947b891',
    '739b1057-067f-424e-9b94-1fc20bf33363',
    'NO',
    682,
    0.41,
    3011,
    356,
    NOW() - INTERVAL '17 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '7e886464-a5c7-4693-bd9f-c4239734f043',
    '6c705bf5-1528-4be6-9143-bf0173137eeb',
    '6e062ef2-6422-4544-96c5-b66463c6031d',
    'NO',
    476,
    0.57,
    2751,
    111,
    NOW() - INTERVAL '44 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '6296997c-ed0b-45b8-9bf4-ac7f9c79ce8c',
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'NO',
    599,
    0.33,
    3924,
    217,
    NOW() - INTERVAL '12 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '062cc09e-3fa5-4fca-9685-394c6bb613b6',
    'b362b1a7-e4d0-4f4d-8f55-8055a2711b94',
    'aeca86f2-665a-46c3-83ea-ceb3304d35c8',
    'NO',
    517,
    0.69,
    1954,
    448,
    NOW() - INTERVAL '21 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '29df5541-599f-43fc-bf7a-894c4b7b1c80',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    'YES',
    721,
    0.32,
    646,
    182,
    NOW() - INTERVAL '28 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    'f67ed60c-079f-459c-8517-720902f4f573',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    '5d87bc9a-15cd-4729-90ac-47dc3b3279ee',
    'YES',
    399,
    0.38,
    652,
    293,
    NOW() - INTERVAL '33 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '78595d68-828e-4000-99f9-cee8b1fdc7a9',
    '0fd2c59c-a037-4e3f-b78c-ffc11c8999e6',
    'be0ce8af-ebce-4a27-9d8b-9e6ac6728252',
    'YES',
    540,
    0.58,
    3244,
    375,
    NOW() - INTERVAL '27 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    'c903be38-bdca-45c0-9a7d-2cd9f6699098',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    '95a2bae5-207d-4b26-ba69-dac243ea7fba',
    'YES',
    768,
    0.68,
    981,
    60,
    NOW() - INTERVAL '45 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '3209a1a3-7014-4cb9-a608-9365f980eea2',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    '76f9de11-68a2-4e2c-bb13-d14539a7c8da',
    'YES',
    898,
    0.67,
    1017,
    80,
    NOW() - INTERVAL '3 hours',
    NOW()
);

INSERT INTO user_positions (
    id, agent_id, timeline_id, side, shares, average_price,
    current_value, unrealised_pnl, created_at, updated_at
)
VALUES (
    '8d0c458c-1d4d-43b0-b432-134712188090',
    '4f768001-2fd1-4d2b-8b4e-d9be749d603d',
    '4323cc8d-aaae-42ec-857c-e0b5e8e45bda',
    'YES',
    468,
    0.44,
    625,
    -122,
    NOW() - INTERVAL '4 hours',
    NOW()
);

-- Seed complete!
-- Run with: psql -h hopper.proxy.rlwy.net -p 15300 -U postgres -d railway -f seed_v2.sql

