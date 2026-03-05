/**
 * Mock Purge Audit — Sprint 3 Acceptance Test
 *
 * Verifies that Sprint 3 pages contain zero mock/demo/fake imports.
 * These pages must use only real API hooks or static content.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

const SPRINT_3_FILES = [
  'src/pages/HomePage.tsx',
  'src/pages/BlackboxPage.tsx',
  'src/pages/RLMFPage.tsx',
  'src/pages/VRFPage.tsx',
  'src/hooks/useOpsBoard.ts',
  'src/hooks/useBlackbox.ts',
  'src/api/opsBoard.ts',
];

const BANNED_PATTERNS = [
  /import.*from.*['"].*demo/,
  /import.*from.*['"].*mock/,
  /import.*from.*['"].*fake/,
  /demoStore/,
  /useDemoEnabled/,
  /useDemoExports/,
  /useDemoLaunchFeed/,
  /Math\.random\(\)/,
  /faker\b/,
];

describe('Mock Purge Audit', () => {
  SPRINT_3_FILES.forEach((filePath) => {
    it(`${filePath} contains no mock/demo/fake imports`, () => {
      const fullPath = resolve(__dirname, '..', '..', filePath);
      const source = readFileSync(fullPath, 'utf-8');

      for (const pattern of BANNED_PATTERNS) {
        const match = source.match(pattern);
        expect(
          match,
          `Found banned pattern ${pattern} in ${filePath}: "${match?.[0]}"`,
        ).toBeNull();
      }
    });
  });
});
