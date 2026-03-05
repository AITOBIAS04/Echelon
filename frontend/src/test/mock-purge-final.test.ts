/**
 * Final Mock Purge Audit — Sprint 5
 *
 * Scans ALL Sprint 5 production source files for banned patterns.
 * Zero mock/demo/fake data allowed in production code paths.
 */

import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { resolve } from 'path';

const SPRINT_5_FILES = [
  // Task 5.1: Convergence Map
  'src/components/convergence/ConvergenceMap.tsx',
  'src/components/convergence/ConvergenceCell.tsx',
  // Task 5.2: Agent Performance Analytics
  'src/components/agents/AgentPerformanceDashboard.tsx',
  'src/components/agents/ArchetypeComparison.tsx',
  'src/components/agents/TradeHistory.tsx',
  'src/components/agents/GenomeViewer.tsx',
  'src/components/agents/AgentDetail.tsx',
  // Task 5.3: WebSocket Integration
  'src/hooks/useWebSocket.ts',
  'src/hooks/useRealtimeInvestigation.ts',
  // Task 5.4: Responsive Layout + Loading States + Polish
  'src/components/common/LoadingSkeleton.tsx',
  'src/components/common/ErrorRetry.tsx',
  'src/components/layout/AppLayout.tsx',
  'src/pages/ConvergencePage.tsx',
  'src/pages/InvestigationPage.tsx',
];

const BANNED_PATTERNS = [
  /\bdemoStore\b/,
  /\bMath\.random\b/,
  /\bfaker\b/i,
  /\bDEMO_/,
  /\bMOCK_DATA\b/,
  /\bhardcoded\b/i,
  /\bplaceholder data\b/i,
  /\bfake.*data\b/i,
  /\bsetInterval.*Math\.random\b/,
];

describe('Final Mock Purge Audit (Sprint 5)', () => {
  for (const filePath of SPRINT_5_FILES) {
    it(`${filePath} — no banned patterns`, () => {
      const fullPath = resolve(__dirname, '..', '..', filePath);
      expect(existsSync(fullPath), `File should exist: ${filePath}`).toBe(true);

      const content = readFileSync(fullPath, 'utf-8');
      for (const pattern of BANNED_PATTERNS) {
        const match = content.match(pattern);
        expect(match, `Banned pattern ${pattern} found in ${filePath}: "${match?.[0]}"`).toBeNull();
      }
    });
  }
});
