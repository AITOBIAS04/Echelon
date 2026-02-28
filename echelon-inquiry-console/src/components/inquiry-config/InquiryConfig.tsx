import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { ClassSelector } from './ClassSelector';
import { TemplatePanel } from './TemplatePanel';
import { ParameterCommit } from './ParameterCommit';
import { CommitmentHash } from './CommitmentHash';

export function InquiryConfig() {
  const [state, dispatch] = useInquiryFlow();
  const navigate = useNavigate();

  // Navigation guard: redirect if no signal selected
  useEffect(() => {
    if (!state.selectedSignal) {
      navigate('/signal-feed', { replace: true });
    }
  }, [state.selectedSignal, navigate]);

  if (!state.selectedSignal) return null;

  function handleCommit() {
    dispatch({ type: 'COMMIT' });
  }

  function handleProceed() {
    dispatch({ type: 'GO_TO_STEP', payload: 3 as 1 | 2 | 3 | 4 | 5 });
    navigate('/execute');
  }

  return (
    <div className="animate-fade-slide-up space-y-8">
      <div>
        <h2 className="mb-1 text-lg font-semibold text-echelon-navy">
          Inquiry Configuration
        </h2>
        <p className="text-sm text-slate-500">
          Signal:{' '}
          <span className="font-medium text-slate-700">
            {state.selectedSignal.headline}
          </span>
        </p>
      </div>

      {/* Section A: Class Selector */}
      <ClassSelector
        suggestedClass={state.selectedSignal.suggested_class}
        selectedClass={state.selectedClass}
        onSelect={(cls) => dispatch({ type: 'SELECT_CLASS', payload: cls })}
      />

      {/* Section B: Template Panel */}
      {state.selectedClass && (
        <TemplatePanel
          selectedClass={state.selectedClass}
          selectedTemplate={state.selectedTemplate}
          onSelect={(template) =>
            dispatch({ type: 'SELECT_TEMPLATE', payload: template })
          }
        />
      )}

      {/* Section C: Parameter Commit + Hash */}
      {state.selectedTemplate && state.commitmentTarget && (
        <div className="space-y-6">
          <ParameterCommit
            template={state.selectedTemplate}
            isCommitted={state.isCommitted}
            onCommit={handleCommit}
          />

          <CommitmentHash
            commitmentTarget={state.commitmentTarget}
            commitmentHash={state.selectedTemplate.commitment_hash}
            isCommitted={state.isCommitted}
            executionPath={state.selectedTemplate.execution_path}
            onProceed={handleProceed}
          />
        </div>
      )}
    </div>
  );
}
