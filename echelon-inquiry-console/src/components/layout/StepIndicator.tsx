import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { useNavigate } from 'react-router-dom';

const STEPS = [
  { label: 'Signal', path: '/signal-feed' },
  { label: 'Configure', path: '/configure' },
  { label: 'Execute', path: '/execute' },
  { label: 'Certificate', path: '/certificate' },
  { label: 'Tier Gate', path: '/tier-gate' },
] as const;

export function StepIndicator() {
  const [state, dispatch] = useInquiryFlow();
  const navigate = useNavigate();
  const currentStep = state.currentStep;

  function handleStepClick(stepNum: 1 | 2 | 3 | 4 | 5) {
    if (stepNum < currentStep) {
      dispatch({ type: 'GO_TO_STEP', payload: stepNum });
      navigate(STEPS[stepNum - 1].path);
    }
  }

  return (
    <nav className="mb-8 flex items-center justify-center gap-0">
      {STEPS.map((step, idx) => {
        const stepNum = (idx + 1) as 1 | 2 | 3 | 4 | 5;
        const isCompleted = stepNum < currentStep;
        const isCurrent = stepNum === currentStep;
        const isFuture = stepNum > currentStep;

        return (
          <div key={step.label} className="flex items-center">
            {idx > 0 && (
              <div
                className={`mx-2 h-px w-12 ${
                  isCompleted ? 'bg-echelon-navy' : 'border-t border-dashed border-slate-300'
                }`}
              />
            )}
            <button
              onClick={() => handleStepClick(stepNum)}
              disabled={isFuture || isCurrent}
              className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium uppercase tracking-wider transition-colors ${
                isCompleted
                  ? 'cursor-pointer bg-echelon-navy text-white hover:bg-opacity-90'
                  : isCurrent
                    ? 'animate-step-pulse bg-echelon-navy text-white'
                    : 'cursor-default bg-slate-100 text-slate-400'
              }`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                  isCompleted || isCurrent
                    ? 'bg-white/20 text-white'
                    : 'border border-slate-300 text-slate-400'
                }`}
              >
                {stepNum}
              </span>
              {step.label}
            </button>
          </div>
        );
      })}
    </nav>
  );
}
