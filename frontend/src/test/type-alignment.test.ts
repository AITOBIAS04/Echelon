/**
 * Type Alignment Regression Test
 *
 * Validates that frontend TypeScript types stay aligned with
 * backend Pydantic schemas. Checks key field names to catch drift.
 */
import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

const FRONTEND_ROOT = path.resolve(__dirname, '..');
const BACKEND_ROOT = path.resolve(__dirname, '../../../backend');

function readFile(filePath: string): string {
  return fs.readFileSync(filePath, 'utf-8');
}

function extractFields(content: string, interfaceName: string): string[] {
  // Match interface or export interface blocks
  const regex = new RegExp(
    `(?:export\\s+)?interface\\s+${interfaceName}\\s*(?:extends\\s+[^{]+)?\\{([^}]+)\\}`,
    's',
  );
  const match = content.match(regex);
  if (!match) return [];

  return match[1]
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('//') && !line.startsWith('*') && !line.startsWith('/**'))
    .map((line) => line.split(/[?:]/)[0].trim())
    .filter((field) => field.length > 0 && !field.startsWith('import'));
}

function extractPydanticFields(content: string, className: string): string[] {
  // Find class block and extract field assignments
  const classRegex = new RegExp(
    `class\\s+${className}\\s*\\([^)]*\\):\\s*\\n((?:\\s+.*\\n)*)`,
  );
  const match = content.match(classRegex);
  if (!match) return [];

  return match[1]
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && !line.startsWith('"""') && !line.startsWith('class'))
    .map((line) => line.split(/[:=]/)[0].trim())
    .filter((field) => field.length > 0 && !field.startsWith('def') && !field.startsWith('@'));
}

describe('Type Alignment: Portfolio', () => {
  it('UserPosition fields match backend UserPosition', () => {
    const feContent = readFile(path.join(FRONTEND_ROOT, 'types/portfolio.ts'));
    const beContent = readFile(path.join(BACKEND_ROOT, 'schemas/user_schemas.py'));

    const feFields = extractFields(feContent, 'UserPosition');
    const beFields = extractPydanticFields(beContent, 'UserPosition');

    // Core fields that MUST exist in both (frontend has no 'id' — uses timeline_id)
    const coreFields = [
      'timeline_id', 'timeline_name', 'side',
      'shards_held', 'current_price', 'unrealised_pnl_usd',
    ];

    for (const field of coreFields) {
      expect(feFields, `Frontend UserPosition missing '${field}'`).toContain(field);
      expect(beFields, `Backend UserPosition missing '${field}'`).toContain(field);
    }
  });
});

describe('Type Alignment: Agents', () => {
  it('Agent fields match backend Agent model core fields', () => {
    const feContent = readFile(path.join(FRONTEND_ROOT, 'types/agents.ts'));
    const beContent = readFile(path.join(BACKEND_ROOT, 'api/agents_routes.py'));

    const feFields = extractFields(feContent, 'Agent');
    const beFields = extractPydanticFields(beContent, 'AgentResponse');

    const coreFields = [
      'id', 'name', 'archetype', 'sanity', 'max_sanity',
      'is_alive', 'total_pnl_usd', 'win_rate', 'trades_count',
    ];

    for (const field of coreFields) {
      expect(feFields, `Frontend Agent missing '${field}'`).toContain(field);
      expect(beFields, `Backend AgentResponse missing '${field}'`).toContain(field);
    }
  });
});

describe('Type Alignment: Paradox', () => {
  it('Paradox fields match backend Paradox schema', () => {
    const feContent = readFile(path.join(FRONTEND_ROOT, 'types/index.ts'));
    const beContent = readFile(path.join(BACKEND_ROOT, 'schemas/paradox_schemas.py'));

    const feFields = extractFields(feContent, 'Paradox');
    const beFields = extractPydanticFields(beContent, 'Paradox');

    const coreFields = [
      'id', 'timeline_id', 'timeline_name', 'status',
      'severity_class', 'logic_gap', 'spawned_at',
      'time_remaining_seconds', 'decay_multiplier',
    ];

    for (const field of coreFields) {
      expect(feFields, `Frontend Paradox missing '${field}'`).toContain(field);
      expect(beFields, `Backend Paradox missing '${field}'`).toContain(field);
    }
  });
});

describe('Type Alignment: Timeline', () => {
  it('Timeline fields match backend TimelineHealth schema', () => {
    const feContent = readFile(path.join(FRONTEND_ROOT, 'types/index.ts'));
    const beContent = readFile(path.join(BACKEND_ROOT, 'schemas/butterfly_schemas.py'));

    const feFields = extractFields(feContent, 'Timeline');
    const beFields = extractPydanticFields(beContent, 'TimelineHealth');

    const coreFields = [
      'id', 'name', 'stability',
      'price_yes', 'price_no', 'logic_gap',
      'has_active_paradox',
    ];

    for (const field of coreFields) {
      expect(feFields, `Frontend Timeline missing '${field}'`).toContain(field);
      expect(beFields, `Backend TimelineHealth missing '${field}'`).toContain(field);
    }
  });
});

describe('Mock Purge Audit', () => {
  it('Sprint 1 hooks have zero mock data imports', () => {
    const hookFiles = [
      'hooks/usePortfolio.ts',
      'hooks/useMarketplace.ts',
      'hooks/useAgents.ts',
      'hooks/useBreaches.ts',
      'hooks/useWatchlist.ts',
    ];

    const mockPatterns = [
      /from.*mocks\//,
      /getMock[A-Z]/,
      /MOCK_DATA/,
      /useDemoBreaches/,
      /demoStore/,
    ];

    for (const hookFile of hookFiles) {
      const content = readFile(path.join(FRONTEND_ROOT, hookFile));
      for (const pattern of mockPatterns) {
        expect(
          pattern.test(content),
          `${hookFile} contains mock import matching ${pattern}`,
        ).toBe(false);
      }
    }
  });

  it('BreachConsolePage has no demo/mock imports', () => {
    const content = readFile(path.join(FRONTEND_ROOT, 'pages/BreachConsolePage.tsx'));
    expect(content).not.toContain('demoStore');
    expect(content).not.toContain('useDemoBreaches');
    expect(content).not.toContain('useDemoEnabled');
    expect(content).not.toContain('getMockBreaches');
    expect(content).not.toContain('STATIC_ACTIVE');
    expect(content).not.toContain('STATIC_HISTORY');
  });
});
