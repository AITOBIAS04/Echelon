/**
 * CreateInvestigationWizard — bounded inquiry creation flow.
 *
 * Steps:
 * 1. Inquiry Question
 * 2. Template
 * 3. Domain Filters
 * 4. Stop Condition
 * 5. Review & Commit
 */

import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  FileSearch,
  Filter,
  LockKeyhole,
  Radar,
  SearchCheck,
  ShieldCheck,
} from 'lucide-react';
import { DomainFilterSelector } from './DomainFilterSelector';
import { StopConditionConfigurator } from './StopConditionConfigurator';
import { useCreateInvestigation } from '../../hooks/useInvestigation';
import { useTheatreDetail } from '../../hooks/useTheatreDetail';
import { useInvestigationTemplates, useInvestigationTemplateDetail } from '../../hooks/useInvestigationTemplates';
import type { DomainFilterId } from './DomainFilterSelector';
import type { StopCondition } from '../../types/investigation';
import type { InvestigationTemplateListItem } from '../../api/investigationTemplates';

const STEPS = [
  'Inquiry Question',
  'Template',
  'Domain Filters',
  'Stop Condition',
  'Review & Commit',
] as const;

const STEP_ICONS = [
  SearchCheck,
  FileSearch,
  Filter,
  Radar,
  ShieldCheck,
] as const;

const INQUIRY_CLASSES = [
  {
    id: 'INVESTIGATIVE',
    label: 'Investigative',
    description: 'Full evidence-based inquiry with a claim graph and certificate-ready stop condition path.',
  },
  {
    id: 'INSPECTION',
    label: 'Inspection',
    description: 'Bias toward registries, filings, and identity/provenance verification with structured checks.',
  },
  {
    id: 'SCRUTINY',
    label: 'Scrutiny',
    description: 'Focused regulatory and compliance review with formal status change tracking.',
  },
  {
    id: 'SURVEY',
    label: 'Survey',
    description: 'Broad sweep across domain filters for pattern detection and landscape mapping.',
  },
  {
    id: 'COUNTERFACTUAL',
    label: 'Counterfactual',
    description: 'What-if analysis exploring alternative outcomes against the committed evidence base.',
  },
] as const;

/**
 * Signal-origin mapping: resolves URL search params against the backend
 * template list to determine which template to prefill.
 */
function inferTemplateFromSignalOrigin(
  searchParams: URLSearchParams,
  domainFilters: DomainFilterId[],
  templates: InvestigationTemplateListItem[],
): string {
  const signalCategory = searchParams.get('signal_category')?.toLowerCase();
  const signalClass = searchParams.get('signal_class')?.toLowerCase();

  let targetId = 'blank';

  if (signalCategory?.includes('regulatory') || signalClass === 'regulatory_clearance') {
    targetId = 'regulatory_action';
  } else if (domainFilters.includes('finance_and_markets')) {
    targetId = 'market_event';
  } else if (domainFilters.includes('corporate_and_entity') || domainFilters.includes('court_and_legal')) {
    targetId = 'corporate_due_diligence';
  }

  // Validate against fetched template list — if not found (e.g. DRAFT), fallback to blank
  const found = templates.some((t) => t.template_id === targetId);
  if (!found) {
    const blankExists = templates.some((t) => t.template_id === 'blank');
    return blankExists ? 'blank' : (templates[0]?.template_id ?? 'blank');
  }

  return targetId;
}

/**
 * Signal-origin domain filter mapping — maps signal params to backend DomainFilter enum values.
 */
const SIGNAL_CLASS_DOMAIN_FILTERS: Partial<Record<string, DomainFilterId[]>> = {
  official_denial: ['corporate_and_entity'],
  regulatory_clearance: ['court_and_legal'],
  market_contradiction: ['finance_and_markets'],
  source_retraction: ['corporate_and_entity'],
  temporal_inconsistency: ['corporate_and_entity'],
  methodology_challenge: ['satellite_and_earth_observation'],
  data_quality_flag: ['satellite_and_earth_observation'],
  competing_evidence: ['corporate_and_entity'],
  expert_dissent: ['satellite_and_earth_observation'],
  statistical_anomaly: ['finance_and_markets'],
  provenance_dispute: ['corporate_and_entity'],
};

const SIGNAL_CATEGORY_DOMAIN_FILTERS: Partial<Record<string, DomainFilterId[]>> = {
  finance_markets: ['finance_and_markets'],
  finance: ['finance_and_markets'],
  corporate_entity: ['corporate_and_entity'],
  corporate: ['corporate_and_entity'],
  maritime: ['maritime'],
  airspace: ['airspace'],
  geopolitical_conflict: ['geopolitical_and_conflict'],
  geopolitical: ['geopolitical_and_conflict'],
  cyber_threat: ['cyber_threat'],
  court_legal: ['court_and_legal'],
  property_land: ['property_and_land'],
  satellite_earth_observation: ['satellite_and_earth_observation'],
};

function uniqFilters(filters: DomainFilterId[]) {
  return [...new Set(filters)];
}

function inferDomainFilters(searchParams: URLSearchParams): DomainFilterId[] {
  const signalClass = searchParams.get('signal_class')?.toLowerCase();
  const signalCategory = searchParams.get('signal_category')?.toLowerCase();
  const signalSource = searchParams.get('signal_source')?.toLowerCase() ?? '';

  const inferred: DomainFilterId[] = [];

  if (signalClass && SIGNAL_CLASS_DOMAIN_FILTERS[signalClass]) {
    inferred.push(...(SIGNAL_CLASS_DOMAIN_FILTERS[signalClass] ?? []));
  }

  if (signalCategory && SIGNAL_CATEGORY_DOMAIN_FILTERS[signalCategory]) {
    inferred.push(...(SIGNAL_CATEGORY_DOMAIN_FILTERS[signalCategory] ?? []));
  }

  if (signalSource.includes('companies house') || signalSource.includes('opencorporates')) {
    inferred.push('corporate_and_entity');
  }
  if (
    signalSource.includes('sec') ||
    signalSource.includes('edgar') ||
    signalSource.includes('earnings')
  ) {
    inferred.push('finance_and_markets');
  }
  if (
    signalSource.includes('reuters') ||
    signalSource.includes('ap ') ||
    signalSource.includes('bloomberg') ||
    signalSource.includes('news')
  ) {
    inferred.push('corporate_and_entity');
  }
  if (
    signalSource.includes('ofac') ||
    signalSource.includes('sanctions') ||
    signalSource.includes('marinetraffic') ||
    signalSource.includes('flightradar')
  ) {
    inferred.push('geopolitical_and_conflict');
  }

  return uniqFilters(inferred);
}

function inferInquiryQuestion(searchParams: URLSearchParams): string {
  const signalTitle = searchParams.get('signal_title');
  const signalClass = searchParams.get('signal_class');
  const signalRegion = searchParams.get('signal_region');
  const sourceInv = searchParams.get('source_investigation');

  if (signalTitle) {
    return `Investigate signal: ${signalTitle}${signalRegion ? ` (${signalRegion})` : ''}`;
  }

  if (signalClass) {
    return `Follow-up investigation: ${signalClass} signal detected${sourceInv ? ` in ${sourceInv}` : ''}`;
  }

  return '';
}

function buildOriginContext(searchParams: URLSearchParams) {
  const signalId = searchParams.get('signal_id');
  const signalTitle = searchParams.get('signal_title');
  const signalClass = searchParams.get('signal_class');
  const signalRegion = searchParams.get('signal_region');
  const sourceSurface = searchParams.get('source_surface');
  const sourceInvestigation = searchParams.get('source_investigation');
  const theatreId = searchParams.get('theatre_id');
  const constructId = searchParams.get('construct_id');

  if (
    !signalId &&
    !signalTitle &&
    !signalClass &&
    !signalRegion &&
    !sourceSurface &&
    !sourceInvestigation &&
    !theatreId &&
    !constructId
  ) {
    return null;
  }

  return {
    signalId,
    signalTitle,
    signalClass,
    signalRegion,
    sourceSurface,
    sourceInvestigation,
    theatreId,
    constructId,
  };
}

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
  onComplete?: (investigationId?: string) => void;
  onCancel?: () => void;
}

function formatStopConditionLabel(condition: StopCondition): string {
  return condition
    .toLowerCase()
    .split('_')
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ');
}

export function CreateInvestigationWizard({
  onComplete,
  onCancel,
}: CreateInvestigationWizardProps) {
  const [searchParams] = useSearchParams();
  const { templates, isLoading: templatesLoading } = useInvestigationTemplates();

  // Compute initial state from URL params (without template inference — deferred until templates load)
  const baseInitialState = useMemo((): WizardState => {
    const signalClass = searchParams.get('signal_class');
    const theatreId = searchParams.get('theatre_id');
    const constructId = searchParams.get('construct_id');
    const domainFilters = inferDomainFilters(searchParams);

    if (!signalClass && !theatreId && !constructId) return INITIAL_STATE;

    return {
      ...INITIAL_STATE,
      inquiryQuestion: inferInquiryQuestion(searchParams),
      inquiryClass: signalClass ? 'INVESTIGATIVE' : INITIAL_STATE.inquiryClass,
      template: 'blank', // Will be resolved once templates load
      theatreId: theatreId ?? '',
      constructId: constructId ?? '',
      domainFilters,
    };
  }, [searchParams]);

  const [step, setStep] = useState(0);
  const [state, setState] = useState<WizardState>(baseInitialState);
  const [templateResolved, setTemplateResolved] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const createMutation = useCreateInvestigation();
  const originContext = useMemo(() => buildOriginContext(searchParams), [searchParams]);
  const { theatre: linkedTheatre } = useTheatreDetail(state.theatreId || null);

  // Fetch detail for the selected template to populate defaults
  const { template: selectedTemplateDetail } = useInvestigationTemplateDetail(
    state.template && state.template !== 'blank' ? state.template : null,
  );

  // Once templates load, resolve the signal-origin template inference
  useEffect(() => {
    if (templates.length > 0 && !templateResolved) {
      const signalClass = searchParams.get('signal_class');
      const theatreId = searchParams.get('theatre_id');
      const constructId = searchParams.get('construct_id');

      if (signalClass || theatreId || constructId) {
        const domainFilters = inferDomainFilters(searchParams);
        const templateId = inferTemplateFromSignalOrigin(searchParams, domainFilters, templates);
        setState((current) => ({ ...current, template: templateId }));
      }
      setTemplateResolved(true);
    }
  }, [templates, templateResolved, searchParams]);

  // Apply template detail defaults when detail loads after a new template selection
  const [lastAppliedTemplateId, setLastAppliedTemplateId] = useState<string | null>(null);
  useEffect(() => {
    if (
      selectedTemplateDetail &&
      selectedTemplateDetail.template_id !== lastAppliedTemplateId
    ) {
      setState((current) => ({
        ...current,
        inquiryClass: selectedTemplateDetail.inquiry_class || current.inquiryClass,
        domainFilters: (selectedTemplateDetail.domain_filters as DomainFilterId[]).length > 0
          ? (selectedTemplateDetail.domain_filters as DomainFilterId[])
          : current.domainFilters,
        stopCondition: (selectedTemplateDetail.default_stop_condition as StopCondition) || current.stopCondition,
        stopConfig: selectedTemplateDetail.default_time_window_days
          ? { ...current.stopConfig, time_window_days: selectedTemplateDetail.default_time_window_days }
          : current.stopConfig,
      }));
      setLastAppliedTemplateId(selectedTemplateDetail.template_id);
    }
  }, [selectedTemplateDetail, lastAppliedTemplateId]);

  const handleTemplateSelect = (templateId: string) => {
    if (templateId === 'blank') {
      // Reset to initial defaults — clear any previously applied template state
      setState((current) => ({
        ...current,
        template: 'blank',
        inquiryClass: 'INVESTIGATIVE',
        domainFilters: [],
        stopCondition: 'OUTCOME_RESOLUTION' as StopCondition,
        stopConfig: {},
      }));
      setLastAppliedTemplateId('blank');
    } else {
      setState((current) => ({ ...current, template: templateId }));
      setLastAppliedTemplateId(null); // Reset so defaults are applied when detail loads
    }
  };

  const stepSummaryLabel = (wizardState: WizardState, stepIndex: number): string => {
    switch (stepIndex) {
      case 0:
        return wizardState.inquiryQuestion.trim()
          ? wizardState.inquiryQuestion.trim()
          : 'Define the inquiry and choose its operating mode.';
      case 1: {
        const tmpl = templates.find((t) => t.template_id === wizardState.template);
        return tmpl?.name ?? 'Choose a template';
      }
      case 2:
        return wizardState.domainFilters.length > 0
          ? `${wizardState.domainFilters.length} committed domain filter${wizardState.domainFilters.length === 1 ? '' : 's'}`
          : 'No domain filters selected yet';
      case 3:
        return wizardState.stopCondition.replaceAll('_', ' ');
      case 4:
        return 'Review the immutable investigation receipt before commit';
      default:
        return '';
    }
  };

  const canAdvance = (): boolean => {
    switch (step) {
      case 0:
        return state.inquiryQuestion.trim().length > 0 && state.inquiryClass.length > 0;
      case 1:
        return state.template.length > 0;
      case 2:
        return state.domainFilters.length > 0;
      case 3:
        return true;
      case 4:
        return !submitted;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    try {
      const investigation = await createMutation.mutateAsync({
        theatre_id: state.theatreId || undefined,
        construct_id: state.constructId || undefined,
        inquiry_class: state.inquiryClass,
        template_id: state.template || undefined,
        domain_filters: state.domainFilters,
        stop_condition: state.stopCondition,
        stop_config: Object.keys(state.stopConfig).length > 0 ? state.stopConfig : undefined,
      });
      onComplete?.(investigation.id);
    } catch {
      setSubmitted(false);
    }
  };

  const CurrentStepIcon = STEP_ICONS[step];

  return (
    <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="space-y-5">
        <section className="rounded-2xl border border-terminal-border bg-terminal-panel px-5 py-5 shadow-sm">
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-purple-700">
            <SearchCheck className="h-3.5 w-3.5" />
            Bounded Inquiry Tools
          </div>
          <h2 className="mt-4 text-2xl font-semibold tracking-tight text-terminal-text">
            Create investigation
          </h2>
          <p className="mt-2 text-sm leading-6 text-terminal-text-secondary">
            Define the question, lock the domain filters, and commit the stop condition that will govern readiness and certificate issuance.
          </p>
        </section>

        <section className="rounded-2xl border border-terminal-border bg-terminal-panel px-5 py-5 shadow-sm">
          <div className="space-y-3">
            {STEPS.map((label, index) => {
              const StepIcon = STEP_ICONS[index];
              const isActive = index === step;
              const isComplete = index < step;
              return (
                <button
                  key={label}
                  type="button"
                  onClick={() => {
                    if (index <= step) setStep(index);
                  }}
                  className={`flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition ${
                    isActive
                      ? 'border-purple-200 bg-purple-100/70'
                      : isComplete
                        ? 'border-green-200 bg-green-50/70 hover:border-green-300'
                        : 'border-terminal-border bg-terminal-sunken'
                  } ${index > step ? 'cursor-default' : 'hover:bg-terminal-hover'}`}
                >
                  <div
                    className={`mt-0.5 flex h-9 w-9 items-center justify-center rounded-xl border ${
                      isActive
                        ? 'border-purple-200 bg-purple-500 text-white'
                        : isComplete
                          ? 'border-green-200 bg-green-500 text-white'
                          : 'border-terminal-border bg-terminal-panel text-terminal-text-muted'
                    }`}
                  >
                    {isComplete ? <Check className="h-4 w-4" /> : <StepIcon className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                      Step {index + 1}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-terminal-text">
                      {label}
                    </div>
                    <div className="mt-1 text-sm leading-5 text-terminal-text-secondary">
                      {stepSummaryLabel(state, index)}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-orange-200 bg-orange-50 px-5 py-5 shadow-sm">
          <div className="flex items-start gap-3">
            <LockKeyhole className="mt-0.5 h-4 w-4 text-orange-700" />
            <div>
              <div className="text-sm font-semibold text-orange-700">
                Immutable at commit
              </div>
              <p className="mt-1 text-sm leading-6 text-orange-700/90">
                Inquiry class, committed domain filters, and stop condition become the bounded receipt for this investigation once you commit.
              </p>
            </div>
          </div>
        </section>
      </aside>

      <section className="space-y-5">
        <header className="rounded-2xl border border-terminal-border bg-terminal-panel px-6 py-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-terminal-border bg-terminal-sunken px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                <CurrentStepIcon className="h-3.5 w-3.5" />
                Step {step + 1}: {STEPS[step]}
              </div>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-terminal-text">
                {STEPS[step]}
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-terminal-text-secondary">
                {step === 0 &&
                  'Frame the question and decide whether this inquiry should behave like a full investigation, a monitoring loop, or a verification task.'}
                {step === 1 &&
                  'Choose the bounded starting posture and optionally bind the investigation to a known theatre or construct.'}
                {step === 2 &&
                  'Commit the domain filters that will govern ingestion. These filters are part of the investigation receipt, not a cosmetic preference.'}
                {step === 3 &&
                  'Set the stop condition that determines how readiness is evaluated and when this inquiry can progress toward certificate issuance.'}
                {step === 4 &&
                  'Review the exact bounded inquiry contract before you commit it to the investigation ledger.'}
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 lg:w-[360px]">
              <MiniStat
                label="Inquiry Class"
                value={state.inquiryClass}
              />
              <MiniStat
                label="Domain Filters"
                value={state.domainFilters.length.toString()}
              />
              <MiniStat
                label="Stop Condition"
                value={formatStopConditionLabel(state.stopCondition)}
              />
            </div>
          </div>
        </header>

        {originContext ? (
          <section className="rounded-2xl border border-purple-200 bg-purple-100/60 px-5 py-4 shadow-sm">
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-purple-700">
              Launch context
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {originContext.sourceSurface ? (
                <MiniStat label="Source Surface" value={originContext.sourceSurface.replaceAll('_', ' ')} />
              ) : null}
              {originContext.signalClass ? (
                <MiniStat label="Signal Class" value={originContext.signalClass} />
              ) : null}
              {originContext.signalRegion ? (
                <MiniStat label="Region" value={originContext.signalRegion} />
              ) : null}
              {originContext.theatreId || originContext.constructId ? (
                <MiniStat
                  label="Linked Theatre"
                  value={originContext.constructId ?? originContext.theatreId ?? 'Bound'}
                />
              ) : null}
            </div>
            <div className="mt-3 text-sm leading-6 text-terminal-text-secondary">
              {originContext.signalTitle ? (
                <div>
                  Prefilled from signal <span className="font-medium text-terminal-text">{originContext.signalTitle}</span>.
                </div>
              ) : null}
              {state.domainFilters.length > 0 ? (
                <div>
                  Suggested domain filters were preselected from the launch context where the mapping is deterministic.
                </div>
              ) : null}
              {originContext.sourceInvestigation ? (
                <div>
                  Source investigation:{' '}
                  <Link
                    to={`/investigation?investigation=${encodeURIComponent(originContext.sourceInvestigation)}`}
                    className="font-mono text-purple-700 underline decoration-purple-300 underline-offset-2"
                  >
                    {originContext.sourceInvestigation}
                  </Link>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {state.theatreId ? (
          <section className="rounded-2xl border border-terminal-border bg-terminal-panel px-5 py-4 shadow-sm">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                  Theatre context
                </div>
                <h4 className="mt-2 text-lg font-semibold text-terminal-text">
                  {linkedTheatre ? linkedTheatre.construct_id : state.constructId || state.theatreId}
                </h4>
                <p className="mt-1 text-sm leading-6 text-terminal-text-secondary">
                  Bound investigations inherit the operational context of the theatre without changing the investigation receipt.
                </p>
              </div>
              <Link
                to={`/theatre/${encodeURIComponent(state.theatreId)}`}
                className="inline-flex h-9 items-center justify-center rounded-xl border border-terminal-border bg-terminal-sunken px-3 text-sm font-medium text-terminal-text-secondary transition hover:bg-terminal-hover hover:text-terminal-text"
              >
                Open theatre
              </Link>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MiniStat label="Theatre ID" value={state.theatreId} />
              <MiniStat label="State" value={linkedTheatre?.state ?? 'Bound'} />
              <MiniStat label="Inquiry Class" value={linkedTheatre?.inquiry_class ?? state.inquiryClass} />
              <MiniStat label="Paradox Risk" value={linkedTheatre?.paradox_risk_level ?? '—'} />
            </div>
          </section>
        ) : null}

        <div className="rounded-2xl border border-terminal-border bg-terminal-panel px-6 py-6 shadow-sm">
          {step === 0 && (
            <div className="space-y-6">
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                  Inquiry Question
                </span>
                <textarea
                  value={state.inquiryQuestion}
                  onChange={(e) =>
                    setState((current) => ({ ...current, inquiryQuestion: e.target.value }))
                  }
                  placeholder="What are you investigating? e.g., 'Will Company X complete its merger by Q3 2026?'"
                  rows={4}
                  className="mt-2 w-full rounded-2xl border border-terminal-border bg-terminal-elevated px-4 py-3 text-sm text-terminal-text outline-none transition placeholder:text-terminal-text-muted focus:border-purple-300 focus:ring-2 focus:ring-purple-200"
                />
              </label>

              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                  Inquiry Class
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-3 lg:grid-cols-5">
                  {INQUIRY_CLASSES.map((inquiryClass) => {
                    const selected = state.inquiryClass === inquiryClass.id;
                    return (
                      <button
                        key={inquiryClass.id}
                        type="button"
                        onClick={() =>
                          setState((current) => ({
                            ...current,
                            inquiryClass: inquiryClass.id,
                          }))
                        }
                        className={`rounded-2xl border px-4 py-4 text-left transition ${
                          selected
                            ? 'border-purple-200 bg-purple-100/70'
                            : 'border-terminal-border bg-terminal-sunken hover:bg-terminal-hover'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold text-terminal-text">
                              {inquiryClass.label}
                            </div>
                            <p className="mt-2 text-sm leading-6 text-terminal-text-secondary">
                              {inquiryClass.description}
                            </p>
                          </div>
                          <div
                            className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full border ${
                              selected
                                ? 'border-purple-300 bg-purple-500 text-white'
                                : 'border-terminal-border bg-terminal-panel text-terminal-text-muted'
                            }`}
                          >
                            {selected && <Check className="h-3.5 w-3.5" />}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-6">
              {templatesLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-sm text-terminal-text-secondary">Loading templates...</div>
                </div>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {templates.map((template) => {
                    const selected = state.template === template.template_id;
                    return (
                      <button
                        key={template.template_id}
                        type="button"
                        onClick={() => handleTemplateSelect(template.template_id)}
                        className={`rounded-2xl border px-4 py-4 text-left transition ${
                          selected
                            ? 'border-purple-200 bg-purple-100/70'
                            : 'border-terminal-border bg-terminal-sunken hover:bg-terminal-hover'
                        }`}
                      >
                        <div className="text-sm font-semibold text-terminal-text">
                          {template.name}
                        </div>
                        <p className="mt-2 text-sm leading-6 text-terminal-text-secondary">
                          {template.description}
                        </p>
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="rounded-2xl border border-terminal-border bg-terminal-sunken px-4 py-4">
                <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                  Optional scope binding
                </div>
                <p className="mt-2 text-sm leading-6 text-terminal-text-secondary">
                  Bind this investigation to a known theatre or construct if the inquiry already belongs to a live operational context.
                </p>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <label className="block">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                      Theatre ID (optional)
                    </span>
                    <input
                      type="text"
                      value={state.theatreId}
                      onChange={(e) =>
                        setState((current) => ({ ...current, theatreId: e.target.value }))
                      }
                      placeholder="TH_..."
                      className="mt-2 w-full rounded-xl border border-terminal-border bg-terminal-elevated px-3 py-2 text-sm font-mono text-terminal-text outline-none transition placeholder:text-terminal-text-muted focus:border-purple-300 focus:ring-2 focus:ring-purple-200"
                    />
                  </label>

                  <label className="block">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
                      Construct ID (optional)
                    </span>
                    <input
                      type="text"
                      value={state.constructId}
                      onChange={(e) =>
                        setState((current) => ({ ...current, constructId: e.target.value }))
                      }
                      placeholder="CON_..."
                      className="mt-2 w-full rounded-xl border border-terminal-border bg-terminal-elevated px-3 py-2 text-sm font-mono text-terminal-text outline-none transition placeholder:text-terminal-text-muted focus:border-purple-300 focus:ring-2 focus:ring-purple-200"
                    />
                  </label>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <DomainFilterSelector
              selected={state.domainFilters}
              onChange={(domainFilters) => setState((current) => ({ ...current, domainFilters }))}
            />
          )}

          {step === 3 && (
            <StopConditionConfigurator
              condition={state.stopCondition}
              config={state.stopConfig}
              onConditionChange={(stopCondition) =>
                setState((current) => ({ ...current, stopCondition }))
              }
              onConfigChange={(stopConfig) =>
                setState((current) => ({ ...current, stopConfig }))
              }
            />
          )}

          {step === 4 && (
            <div className="space-y-5">
              <div className="rounded-2xl border border-orange-200 bg-orange-50 px-4 py-4">
                <div className="text-sm font-semibold text-orange-700">Immutability Warning</div>
                <p className="mt-2 text-sm leading-6 text-orange-700/90">
                  Once committed, the investigation parameters cannot be changed. The inquiry class, domain filters, and stop condition are sealed into the investigation certificate chain.
                </p>
              </div>

              <ReviewCard
                title="Inquiry"
                body={state.inquiryQuestion}
                footer={state.inquiryClass}
              />

              <ReviewCard
                title={`Domain Filters (${state.domainFilters.length})`}
                body={
                  state.domainFilters.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {state.domainFilters.map((filter) => (
                        <span
                          key={filter}
                          className="rounded-full border border-terminal-border bg-terminal-elevated px-2.5 py-1 text-[11px] font-mono text-terminal-text-secondary"
                        >
                          {filter}
                        </span>
                      ))}
                    </div>
                  ) : (
                    'No domain filters selected'
                  )
                }
              />

              <ReviewCard
                title="Stop Condition"
                body={formatStopConditionLabel(state.stopCondition)}
                footer={
                  Object.keys(state.stopConfig).length > 0 ? (
                    <pre className="overflow-x-auto rounded-xl border border-terminal-border bg-terminal-elevated px-3 py-3 text-[11px] text-terminal-text-secondary">
                      {JSON.stringify(state.stopConfig, null, 2)}
                    </pre>
                  ) : undefined
                }
              />

              {(state.theatreId || state.constructId) && (
                <ReviewCard
                  title="Scope"
                  body={
                    <div className="space-y-1 text-sm text-terminal-text">
                      {state.theatreId && <div>Theatre: <span className="font-mono">{state.theatreId}</span></div>}
                      {state.constructId && <div>Construct: <span className="font-mono">{state.constructId}</span></div>}
                    </div>
                  }
                />
              )}

              {createMutation.error && (
                <div className="rounded-2xl border border-status-danger/25 bg-status-danger/5 px-4 py-4 text-sm text-status-danger">
                  Failed to create investigation: {createMutation.error.message}
                </div>
              )}
            </div>
          )}
        </div>

        <footer className="flex items-center justify-between rounded-2xl border border-terminal-border bg-terminal-panel px-5 py-4 shadow-sm">
          <button
            type="button"
            onClick={step === 0 ? onCancel : () => setStep((current) => current - 1)}
            className="inline-flex items-center gap-2 rounded-xl border border-terminal-border bg-terminal-sunken px-4 py-2 text-sm font-medium text-terminal-text-secondary transition hover:bg-terminal-hover hover:text-terminal-text"
          >
            <ArrowLeft className="h-4 w-4" />
            {step === 0 ? 'Cancel' : 'Back'}
          </button>

          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((current) => current + 1)}
              disabled={!canAdvance()}
              className="inline-flex items-center gap-2 rounded-xl border border-purple-200 bg-purple-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-purple-400 disabled:cursor-not-allowed disabled:border-terminal-border disabled:bg-terminal-sunken disabled:text-terminal-text-disabled"
            >
              Next
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canAdvance() || createMutation.isPending}
              className="inline-flex items-center gap-2 rounded-xl border border-purple-200 bg-purple-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-purple-400 disabled:cursor-not-allowed disabled:border-terminal-border disabled:bg-terminal-sunken disabled:text-terminal-text-disabled"
            >
              <ShieldCheck className="h-4 w-4" />
              {createMutation.isPending ? 'Creating...' : 'Commit Investigation'}
            </button>
          )}
        </footer>
      </section>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-terminal-border bg-terminal-elevated px-4 py-3 shadow-sm">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-terminal-text">{value}</div>
    </div>
  );
}

function ReviewCard({
  title,
  body,
  footer,
}: {
  title: string;
  body: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-terminal-border bg-terminal-sunken px-4 py-4">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
        {title}
      </div>
      <div className="mt-3 text-sm leading-6 text-terminal-text">{body}</div>
      {footer ? <div className="mt-3">{footer}</div> : null}
    </section>
  );
}
