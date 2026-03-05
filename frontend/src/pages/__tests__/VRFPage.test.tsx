import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VRFPage } from '../VRFPage';

describe('VRFPage', () => {
  it('renders documentation content (no simulated data)', () => {
    render(<VRFPage />);

    // Header
    expect(screen.getByText('VRF Integrity System')).toBeInTheDocument();

    // Application points
    expect(screen.getByText('Commit-Reveal Windows')).toBeInTheDocument();
    expect(screen.getByText('Circuit Breaker Thresholds')).toBeInTheDocument();
    expect(screen.getByText('Market Data Validation')).toBeInTheDocument();
    expect(screen.getByText('RLMF Episode Sampling')).toBeInTheDocument();
    expect(screen.getByText('Risk Fee Jitter')).toBeInTheDocument();
    expect(screen.getByText('Oracle Failover')).toBeInTheDocument();

    // Roadmap
    expect(screen.getByText('Implementation Roadmap')).toBeInTheDocument();
    expect(screen.getByText(/Phase 1: Core Protocol/)).toBeInTheDocument();
    expect(screen.getByText(/Phase 2: VRF Integration Design/)).toBeInTheDocument();
    expect(screen.getByText(/Phase 3: Live VRF Deployment/)).toBeInTheDocument();
  });

  it('has no useState/useEffect hooks (pure static page)', async () => {
    // VRFPage should be a pure render — no hooks, no timers, no mock data
    const source = await import('../VRFPage');
    const componentStr = source.VRFPage.toString();
    expect(componentStr).not.toContain('useState');
    expect(componentStr).not.toContain('useEffect');
    expect(componentStr).not.toContain('setInterval');
  });
});
