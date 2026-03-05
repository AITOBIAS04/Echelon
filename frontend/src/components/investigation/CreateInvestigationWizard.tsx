/**
 * CreateInvestigationWizard — 5-step wizard for creating investigations.
 *
 * Steps: Inquiry → Template → Domain Filters → Stop Condition → Review & Commit
 * POSTs to /api/v1/investigations/ on submit.
 */

import { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DomainFilterSelector } from './DomainFilterSelector';
import { StopConditionConfigurator } from './StopConditionConfigurator';
import { useCreateInvestigation } from '../../hooks/useInvestigation';
import type { DomainFilterId } from './DomainFilterSelector';
import type { StopCondition } from '../../types/investigation';

const STEPS = [
  'Inquiry Question',
  'Template',
  'Domain Filters',
  'Stop Condition',
  'Review & Commit',
] as const;

const INQUIRY_CLASSES = [
  { id: 'INVESTIGATIVE', label: 'Investigative', description: 'Full evidence-based investigation with claim graph' },
  { id: 'MONITORING', label: 'Monitoring', description: 'Ongoing surveillance of entity or market activity' },
  { id: 'VERIFICATION', label: 'Verification', description: 'Fact-checking of specific claims or assertions' },
] as const;

const TEMPLATES = [
  { id: 'blank', label: 'Blank Investigation', description: 'Start from scratch with custom configuration' },
  { id: 'corporate_due_diligence', label: 'Corporate Due Diligence', description: 'Standard KYC/AML investigation template' },
  { id: 'market_event', label: 'Market Event Analysis', description: 'Pre-configured for financial market events' },
  { id: 'regulatory_action', label: 'Regulatory Action Tracking', description: 'Monitor regulatory proceedings and outcomes' },
] as const;

interface WizardState {
  inquiryQuestion: string;
  inquiryClass: string;
  template: string;
  theatreId: string;
  constructId: string;
  domainFilters: DomainFilterId[];
  stopCondition: StopCondition;
  stopConfig: Record<string, unknown>;
}

const INITIAL_STATE: WizardState = {
  inquiryQuestion: '',
  inquiryClass: 'INVESTIGATIVE',
  template: 'blank',
  theatreId: '',
  constructId: '',
  domainFilters: [],
  stopCondition: 'OUTCOME_RESOLUTION',
  stopConfig: {},
};

interface CreateInvestigationWizardProps {
  onComplete?: () => void;
  onCancel?: () => void;
}

export function CreateInvestigationWizard({
  onComplete,
  onCancel,
}: CreateInvestigationWizardProps) {
  const [searchParams] = useSearchParams();

  // Prefill from URL search params (set by SignalFeedPanel "Create from signal")
  const initialState = useMemo((): WizardState => {
    const signalClass = searchParams.get('signal_class');
    const sourceInv = searchParams.get('source_investigation');
    if (!signalClass) return INITIAL_STATE;
    return {
      ...INITIAL_STATE,
      inquiryQuestion: `Follow-up investigation: ${signalClass} signal detected${sourceInv ? ` in ${sourceInv}` : ''}`,
      inquiryClass: 'VERIFICATION',
    };
  }, [searchParams]);

  const [step, setStep] = useState(0);
  const [state, setState] = useState<WizardState>(initialState);
  const [submitted, setSubmitted] = useState(false);

  const createMutation = useCreateInvestigation();

  const canAdvance = (): boolean => {
    switch (step) {
      case 0:
        return state.inquiryQuestion.trim().length > 0 && state.inquiryClass.length > 0;
      case 1:
        return state.template.length > 0;
      case 2:
        return state.domainFilters.length > 0;
      case 3:
        return true; // Stop condition always has a default
      case 4:
        return !submitted;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    try {
      await createMutation.mutateAsync({
        theatre_id: state.theatreId || undefined,
        construct_id: state.constructId || undefined,
        inquiry_class: state.inquiryClass,
        domain_filters: state.domainFilters,
        stop_condition: state.stopCondition,
        stop_config: Object.keys(state.stopConfig).length > 0 ? state.stopConfig : undefined,
      });
      onComplete?.();
    } catch {
      setSubmitted(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-1">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-1">
            <div
              className={`flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-mono ${
                i === step
                  ? 'bg-echelon-cyan text-terminal-bg font-bold'
                  : i < step
                    ? 'bg-echelon-cyan/20 text-echelon-cyan'
                    : 'bg-terminal-surface text-terminal-text-muted border border-terminal-border'
              }`}
            >
              {i < step ? '✓' : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`w-8 h-px ${
                  i < step ? 'bg-echelon-cyan/40' : 'bg-terminal-border'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step title */}
      <div>
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
          Step {step + 1}: {STEPS[step]}
        </h3>
      </div>

      {/* Step content */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl p-5">
        {/* Step 0: Inquiry Question */}
        {step === 0 && (
          <div className="space-y-4">
            <label className="block">
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
                Inquiry Question
              </span>
              <textarea
                value={state.inquiryQuestion}
                onChange={(e) =>
                  setState((s) => ({ ...s, inquiryQuestion: e.target.value }))
                }
                placeholder="What are you investigating? e.g., 'Will Company X complete its merger by Q3 2026?'"
                rows={3}
                className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2 text-xs text-terminal-text placeholder-terminal-text-muted resize-none"
              />
            </label>
            <div>
              <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
                Inquiry Class
              </span>
              <div className="mt-2 space-y-2">
                {INQUIRY_CLASSES.map((ic) => (
                  <button
                    key={ic.id}
                    type="button"
                    onClick={() => setState((s) => ({ ...s, inquiryClass: ic.id }))}
                    className={`w-full text-left px-3 py-2 rounded-lg border transition-colors ${
                      state.inquiryClass === ic.id
                        ? 'border-echelon-cyan/50 bg-echelon-cyan/5'
                        : 'border-terminal-border hover:border-terminal-border/80 bg-terminal-surface'
                    }`}
                  >
                    <div className="text-xs font-semibold text-terminal-text">
                      {ic.label}
                    </div>
                    <div className="text-[10px] text-terminal-text-muted">
                      {ic.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Template */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="text-xs text-terminal-text-muted">
              Choose a template to pre-configure domain filters and stop conditions, or start blank.
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {TEMPLATES.map((tmpl) => (
                <button
                  key={tmpl.id}
                  type="button"
                  onClick={() => setState((s) => ({ ...s, template: tmpl.id }))}
                  className={`text-left p-4 rounded-lg border transition-colors ${
                    state.template === tmpl.id
                      ? 'border-echelon-cyan/50 bg-echelon-cyan/5'
                      : 'border-terminal-border hover:border-terminal-border/80 bg-terminal-surface'
                  }`}
                >
                  <div className="text-xs font-semibold text-terminal-text mb-1">
                    {tmpl.label}
                  </div>
                  <div className="text-[10px] text-terminal-text-muted">
                    {tmpl.description}
                  </div>
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-[10px] text-terminal-text-muted">
                  Theatre ID (optional)
                </span>
                <input
                  type="text"
                  value={state.theatreId}
                  onChange={(e) =>
                    setState((s) => ({ ...s, theatreId: e.target.value }))
                  }
                  placeholder="TH_..."
                  className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono placeholder-terminal-text-muted"
                />
              </label>
              <label className="block">
                <span className="text-[10px] text-terminal-text-muted">
                  Construct ID (optional)
                </span>
                <input
                  type="text"
                  value={state.constructId}
                  onChange={(e) =>
                    setState((s) => ({ ...s, constructId: e.target.value }))
                  }
                  placeholder="CON_..."
                  className="mt-1 w-full bg-terminal-bg border border-terminal-border rounded px-2 py-1.5 text-xs text-terminal-text font-mono placeholder-terminal-text-muted"
                />
              </label>
            </div>
          </div>
        )}

        {/* Step 2: Domain Filters */}
        {step === 2 && (
          <DomainFilterSelector
            selected={state.domainFilters}
            onChange={(domainFilters) => setState((s) => ({ ...s, domainFilters }))}
          />
        )}

        {/* Step 3: Stop Condition */}
        {step === 3 && (
          <StopConditionConfigurator
            condition={state.stopCondition}
            config={state.stopConfig}
            onConditionChange={(stopCondition) =>
              setState((s) => ({ ...s, stopCondition }))
            }
            onConfigChange={(stopConfig) =>
              setState((s) => ({ ...s, stopConfig }))
            }
          />
        )}

        {/* Step 4: Review & Commit */}
        {step === 4 && (
          <div className="space-y-4">
            {/* Immutability warning */}
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
              <div className="text-xs font-semibold text-amber-400 mb-1">
                Immutability Warning
              </div>
              <div className="text-[10px] text-amber-400/80">
                Once committed, the investigation parameters cannot be changed. The inquiry class,
                domain filters, and stop condition are sealed into the investigation certificate.
              </div>
            </div>

            {/* Review summary */}
            <div className="space-y-3">
              <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
                <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                  Inquiry
                </div>
                <div className="text-xs text-terminal-text">
                  {state.inquiryQuestion}
                </div>
                <div className="mt-1 text-[10px] font-mono text-echelon-cyan">
                  {state.inquiryClass}
                </div>
              </div>

              <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
                <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                  Domain Filters ({state.domainFilters.length})
                </div>
                <div className="flex flex-wrap gap-1">
                  {state.domainFilters.map((f) => (
                    <span
                      key={f}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-terminal-bg text-terminal-text border border-terminal-border"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
                <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                  Stop Condition
                </div>
                <div className="text-xs font-mono text-terminal-text">
                  {state.stopCondition}
                </div>
                {Object.keys(state.stopConfig).length > 0 && (
                  <pre className="mt-2 text-[10px] text-terminal-text-muted font-mono">
                    {JSON.stringify(state.stopConfig, null, 2)}
                  </pre>
                )}
              </div>

              {(state.theatreId || state.constructId) && (
                <div className="bg-terminal-surface rounded-lg p-3 border border-terminal-border">
                  <div className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
                    Scope
                  </div>
                  <div className="text-xs text-terminal-text font-mono">
                    {state.theatreId && <div>Theatre: {state.theatreId}</div>}
                    {state.constructId && <div>Construct: {state.constructId}</div>}
                  </div>
                </div>
              )}
            </div>

            {createMutation.error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400">
                Failed to create investigation: {createMutation.error.message}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={step === 0 ? onCancel : () => setStep((s) => s - 1)}
          className="px-4 py-2 text-xs text-terminal-text-muted hover:text-terminal-text border border-terminal-border rounded-lg transition-colors"
        >
          {step === 0 ? 'Cancel' : 'Back'}
        </button>
        <div className="flex gap-2">
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              disabled={!canAdvance()}
              className="px-4 py-2 text-xs font-semibold bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/30 rounded-lg hover:bg-echelon-cyan/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canAdvance() || createMutation.isPending}
              className="px-4 py-2 text-xs font-semibold bg-echelon-cyan text-terminal-bg rounded-lg hover:bg-echelon-cyan/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? 'Creating...' : 'Commit Investigation'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
