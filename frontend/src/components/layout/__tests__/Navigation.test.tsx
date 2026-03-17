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
  it('renders primary nav items', () => {
    renderSidebar();

    expect(screen.getAllByText('Home').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Mission Control').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Workspace').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Analytics').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Verify').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('RLMF Exports').length).toBeGreaterThanOrEqual(1);
  });

  it('all nav links point to valid routes', () => {
    renderSidebar('/workspace');

    const validRoutes = [
      '/', '/home', '/workspace', '/analytics',
      '/portfolio', '/rlmf', '/verify',
    ];

    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href'));

    for (const route of validRoutes) {
      expect(hrefs).toContain(route);
    }
  });
});
