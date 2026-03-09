/**
 * CreateInvestigationPage — Route wrapper for the investigation creation wizard.
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { CreateInvestigationWizard } from '../components/investigation/CreateInvestigationWizard';

export function CreateInvestigationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const buildPostCreateHref = (investigationId?: string) => {
    const next = new URLSearchParams();
    if (investigationId) {
      next.set('investigation', investigationId);
      next.set('created', '1');
    }

    [
      'source_surface',
      'signal_id',
      'signal_title',
      'signal_class',
      'signal_region',
      'signal_category',
      'signal_source',
      'source_investigation',
      'theatre_id',
      'construct_id',
    ].forEach((key) => {
      const value = searchParams.get(key);
      if (value) next.set(key, value);
    });

    const query = next.toString();
    return query ? `/investigation?${query}` : '/investigation';
  };

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <CreateInvestigationWizard
        onComplete={(investigationId) => navigate(buildPostCreateHref(investigationId))}
        onCancel={() => navigate('/investigation')}
      />
    </div>
  );
}
