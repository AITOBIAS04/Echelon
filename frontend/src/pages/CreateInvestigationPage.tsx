/**
 * CreateInvestigationPage — Route wrapper for the investigation creation wizard.
 */

import { useNavigate } from 'react-router-dom';
import { CreateInvestigationWizard } from '../components/investigation/CreateInvestigationWizard';

export function CreateInvestigationPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-5xl mx-auto p-6">
      <CreateInvestigationWizard
        onComplete={() => navigate('/investigation')}
        onCancel={() => navigate('/investigation')}
      />
    </div>
  );
}
