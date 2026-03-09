import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import { RLMFPage } from '../RLMFPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <RLMFPage />
    </MemoryRouter>,
  );
}

describe('RLMFPage', () => {
  it('renders the honest staged delivery header', () => {
    renderPage();

    expect(screen.getByText('RLMF Exports')).toBeInTheDocument();
    expect(screen.getByText('Delivery-ready export catalog')).toBeInTheDocument();
    expect(
      screen.getByText(/delivery api still pending/i),
    ).toBeInTheDocument();
  });

  it('renders the two backend-available package families', () => {
    renderPage();

    expect(screen.getByText('RLMF Training Export')).toBeInTheDocument();
    expect(screen.getByText('Sponsor Delivery Package')).toBeInTheDocument();
    expect(screen.getAllByText('Backend service ready').length).toBeGreaterThanOrEqual(2);
  });

  it('renders staged package families without fake live actions', () => {
    renderPage();

    expect(screen.getByText('Calibration Dataset')).toBeInTheDocument();
    expect(screen.getByText('Evaluation Holdout Set')).toBeInTheDocument();
    expect(screen.getAllByText('API Pending').length).toBeGreaterThanOrEqual(4);
  });
});
