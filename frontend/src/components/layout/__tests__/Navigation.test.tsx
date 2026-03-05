import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../Sidebar';

// Suppress lucide-react icon warnings in test
vi.mock('lucide-react', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('lucide-react');
  return actual;
});

function renderSidebar(path = '/home') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar mobileOpen={true} />
    </MemoryRouter>,
  );
}

describe('Navigation', () => {
  it('renders all primary nav items', () => {
    renderSidebar();

    expect(screen.getAllByText('Dashboard').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Marketplace').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Investigations').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Analytics').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Portfolio').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Agents').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('RLMF Exports').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Verify').length).toBeGreaterThanOrEqual(1);
  });

  it('shows investigation subnav when on investigation routes', () => {
    renderSidebar('/investigation');

    // Mobile drawer shows subnav
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Signal Feed')).toBeInTheDocument();
    expect(screen.getByText('Create')).toBeInTheDocument();
  });

  it('shows agents subnav when on agents routes', () => {
    renderSidebar('/agents');

    expect(screen.getByText('Breach Console')).toBeInTheDocument();
    expect(screen.getByText('Export Console')).toBeInTheDocument();
  });

  it('does not show investigation subnav on non-investigation routes', () => {
    renderSidebar('/marketplace');

    expect(screen.queryByText('Signal Feed')).not.toBeInTheDocument();
    expect(screen.queryByText('Active')).not.toBeInTheDocument();
  });

  it('all nav links point to valid routes', () => {
    renderSidebar('/investigation');

    const validRoutes = [
      '/home', '/marketplace', '/investigation', '/analytics',
      '/portfolio', '/agents', '/rlmf', '/verify',
      '/investigation/signals', '/investigation/create',
    ];

    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href'));

    for (const route of validRoutes) {
      expect(hrefs).toContain(route);
    }
  });
});
