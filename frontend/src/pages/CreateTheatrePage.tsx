import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronLeft,
  FileText,
  LayoutTemplate,
  Loader2,
  Settings2,
  Sparkles,
} from 'lucide-react';
import { theatreApi } from '../api/theatres';
import { isEnabled } from '../lib/featureFlags';
import { useTheatreTemplate, useTheatreTemplates } from '../hooks/useTheatreTemplates';
import type { TemplateSummaryResponse, TheatreCreateRequest } from '../types/theatre';

type CreationPath = 'blank' | 'template' | 'alpamayo';
type Step = 'choose-path' | 'select-template' | 'select-suggestion' | 'configure' | 'review';
type InquiryClass = 'COUNTERFACTUAL' | 'INVESTIGATIVE' | 'INSPECTION' | 'SURVEY' | 'SCRUTINY';

interface AlpamayoSuggestion {
  id: string;
  title: string;
  templateId: string;
  inquiryLabel: string;
  confidence: number;
  reason: string;
  sourceOfTruth: string;
  resolution: string;
  stopCondition: string;
}

const INQUIRY_CLASSES: InquiryClass[] = [
  'COUNTERFACTUAL',
  'INVESTIGATIVE',
  'INSPECTION',
  'SURVEY',
  'SCRUTINY',
];

const INQUIRY_LABELS: Record<InquiryClass, string> = {
  COUNTERFACTUAL: 'Binary Event',
  INVESTIGATIVE: 'Investigative',
  INSPECTION: 'Inspection',
  SURVEY: 'Survey',
  SCRUTINY: 'Scrutiny',
};

const PATH_COPY: Record<
  CreationPath,
  { title: string; description: string; helper: string; icon: React.ReactNode; tone: string }
> = {
  blank: {
    title: 'Blank Theatre',
    description: 'Start from scratch with full control over the contract.',
    helper: 'Authoring is still staged until full template composition exists.',
    icon: <FileText className="h-5 w-5" />,
    tone: 'border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
  },
  template: {
    title: 'From Theatre Template',
    description: 'Use a pre-structured theatre contract with locked runtime semantics.',
    helper: 'This is the live creation path today.',
    icon: <LayoutTemplate className="h-5 w-5" />,
    tone: 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]',
  },
  alpamayo: {
    title: 'Suggested by Alpamayo',
    description: 'Start from an operator-facing recommendation when the service is available.',
    helper: 'This path remains staged and recommendation data is not yet live.',
    icon: <Sparkles className="h-5 w-5" />,
    tone: 'border-[color:oklch(0.525_0.155_260_/_0.18)] bg-[color:oklch(0.525_0.155_260_/_0.08)] text-[var(--e-purple-700)]',
  },
};

function Stepper({
  steps,
  current,
}: {
  steps: Array<{ key: Step; label: string }>;
  current: Step;
}) {
  const currentIndex = steps.findIndex((item) => item.key === current);

  return (
    <div className="rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="flex flex-wrap items-center gap-3">
        {steps.map((step, index) => {
          const done = index < currentIndex;
          const active = step.key === current;
          return (
            <div key={step.key} className="flex min-w-0 flex-1 items-center gap-3">
              <div
                className={clsx(
                  'flex h-8 w-8 items-center justify-center rounded-full border text-[12px] font-semibold',
                  done
                    ? 'border-[var(--e-green-600)] bg-[var(--e-green-600)] text-white'
                    : active
                      ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-500)] text-white'
                      : 'border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
                )}
              >
                {done ? <Check className="h-4 w-4" /> : index + 1}
              </div>
              <div className={clsx('text-[13px]', active ? 'font-semibold text-[var(--e-text-primary)]' : 'text-[var(--e-text-muted)]')}>
                {step.label}
              </div>
              {index < steps.length - 1 ? (
                <div className={clsx('ml-auto hidden h-px flex-1 md:block', done ? 'bg-[var(--e-green-600)]' : 'bg-[var(--e-border-secondary)]')} />
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SectionCard({
  title,
  eyebrow,
  children,
  aside,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="flex items-center justify-between gap-4 border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-3">
        <div>
          {eyebrow ? (
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
              {eyebrow}
            </div>
          ) : null}
          <h2 className="text-[13px] font-semibold text-[var(--e-text-primary)]">{title}</h2>
        </div>
        {aside}
      </div>
      <div className="px-5 py-5">{children}</div>
    </section>
  );
}

function PathCard({
  path,
  selected,
  onClick,
  recommended,
  disabled,
}: {
  path: CreationPath;
  selected: boolean;
  onClick: () => void;
  recommended?: boolean;
  disabled?: boolean;
}) {
  const copy = PATH_COPY[path];

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'relative rounded-xl border-2 bg-[var(--e-bg-card)] p-5 text-left shadow-[var(--e-shadow-xs)] transition',
        disabled
          ? 'cursor-not-allowed border-[var(--e-border-primary)] opacity-65'
          : 'hover:-translate-y-0.5 hover:shadow-[var(--e-shadow-md)]',
        selected
          ? 'border-[var(--e-purple-500)] shadow-[var(--e-shadow-md)]'
          : 'border-[var(--e-border-primary)]',
        !selected && !disabled && 'hover:border-[var(--e-purple-200)]',
      )}
    >
      {recommended ? (
        <span className="absolute right-4 top-4 rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
          Recommended
        </span>
      ) : null}
      {disabled ? (
        <span className="absolute right-4 top-4 rounded-full border border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-text-muted)]">
          Coming soon
        </span>
      ) : null}
      <div className={clsx('mb-4 flex h-12 w-12 items-center justify-center rounded-lg border', copy.tone)}>{copy.icon}</div>
      <div className="mb-1 text-[17px] font-semibold text-[var(--e-text-primary)]">{copy.title}</div>
      <div className="mb-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">{copy.description}</div>
      <div className="text-[12px] leading-5 text-[var(--e-text-muted)]">{copy.helper}</div>
    </button>
  );
}

function TemplateCard({
  template,
  selected,
  onClick,
}: {
  template: TemplateSummaryResponse;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex h-full flex-col rounded-xl border-2 bg-[var(--e-bg-card)] p-5 text-left shadow-[var(--e-shadow-xs)] transition hover:-translate-y-0.5 hover:shadow-[var(--e-shadow-md)]',
        selected ? 'border-[var(--e-purple-500)]' : 'border-[var(--e-border-primary)] hover:border-[var(--e-purple-200)]',
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[var(--e-purple-700)]">
          {template.inquiry_class ? INQUIRY_LABELS[template.inquiry_class as InquiryClass] ?? template.inquiry_class : 'Template'}
        </span>
        <div
          className={clsx(
            'flex h-5 w-5 items-center justify-center rounded-full border-2',
            selected ? 'border-[var(--e-purple-500)] bg-[var(--e-purple-500)] text-white' : 'border-[var(--e-border-primary)] text-transparent',
          )}
        >
          <Check className="h-3 w-3" />
        </div>
      </div>
      <div className="mb-1 text-[15px] font-semibold text-[var(--e-text-primary)]">{template.display_name}</div>
      <div className="mb-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">
        {template.description ?? 'Structured theatre contract with pre-configured resolution rules.'}
      </div>
      <div className="mt-auto border-t border-[var(--e-border-secondary)] pt-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">Template Family</div>
        <div className="mt-1 font-mono text-[12px] text-[var(--e-text-primary)]">{template.template_family}</div>
      </div>
    </button>
  );
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-t border-[var(--e-border-secondary)] py-3 first:border-t-0 first:pt-0 last:pb-0">
      <span className="text-[13px] text-[var(--e-text-secondary)]">{label}</span>
      <span className={clsx('text-[13px] font-medium text-[var(--e-text-primary)]', mono && 'font-mono tabular-nums')}>
        {value}
      </span>
    </div>
  );
}

export function CreateTheatrePage() {
  const navigate = useNavigate();
  const {
    templates,
    isLoading: templatesLoading,
    error: templatesError,
    isEmpty: templatesEmpty,
    refetch: refetchTemplates,
  } = useTheatreTemplates();

  const [path, setPath] = useState<CreationPath | null>(null);
  const [step, setStep] = useState<Step>('choose-path');
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateSummaryResponse | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<AlpamayoSuggestion | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [marketTitle, setMarketTitle] = useState('');
  const [marketContext, setMarketContext] = useState('');
  const [primarySource, setPrimarySource] = useState('');
  const [endCondition, setEndCondition] = useState('');
  const [resolutionCriteria, setResolutionCriteria] = useState('');
  const [constructId, setConstructId] = useState('');
  const [inquiryClass, setInquiryClass] = useState<InquiryClass>('COUNTERFACTUAL');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    template: selectedTemplateDetail,
    isLoading: selectedTemplateDetailLoading,
    error: selectedTemplateDetailError,
  } = useTheatreTemplate(selectedTemplate?.id ?? null);

  const alpamayoEnabled = isEnabled('CYCLE_017_TAO_FLOW');
  const alpamayoSuggestions: AlpamayoSuggestion[] = [];

  const steps = useMemo(() => {
    const base = [{ key: 'choose-path' as Step, label: 'Choose Path' }];
    if (path === 'template') base.push({ key: 'select-template' as Step, label: 'Template' });
    if (path === 'alpamayo') base.push({ key: 'select-suggestion' as Step, label: 'Alpamayo' });
    base.push({ key: 'configure' as Step, label: 'Configure' });
    base.push({ key: 'review' as Step, label: 'Review' });
    return base;
  }, [path]);

  const blankPathDeferred = path === 'blank';
  const canReviewTemplatePath =
    path === 'template' && constructId.trim().length > 0 && !!selectedTemplateDetail && !selectedTemplateDetailLoading;
  const canSubmit = canReviewTemplatePath;

  const choosePath = (nextPath: CreationPath) => {
    setSubmitError(null);
    if (nextPath !== 'template') {
      return;
    }
    setPath(nextPath);
    setSelectedTemplate(null);
    setSelectedSuggestion(null);
    if (nextPath === 'template') {
      setStep('select-template');
      return;
    }
  };

  const selectTemplate = (template: TemplateSummaryResponse) => {
    setSelectedTemplate(template);
    setSelectedSuggestion(null);
    setMarketTitle((current) => current || template.display_name);
    setConstructId('');
    if (template.inquiry_class && INQUIRY_CLASSES.includes(template.inquiry_class as InquiryClass)) {
      setInquiryClass(template.inquiry_class as InquiryClass);
    }
    setStep('configure');
  };

  const goBack = () => {
    setSubmitError(null);
    if (step === 'review') {
      setStep('configure');
      return;
    }
    if (step === 'configure') {
      if (path === 'template') {
        setStep('select-template');
        return;
      }
      if (path === 'alpamayo') {
        setStep('select-suggestion');
        return;
      }
      setPath(null);
      setStep('choose-path');
      return;
    }
    setPath(null);
    setStep('choose-path');
  };

  const handleCreate = async () => {
    if (path !== 'template' || !selectedTemplateDetail || !canSubmit) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const req: TheatreCreateRequest = {
        template_id: selectedTemplateDetail.id,
        construct_id: constructId.trim(),
        template_json: selectedTemplateDetail.template_json,
        inquiry_class: inquiryClass,
      };
      const theatre = await theatreApi.createTheatre(req);
      navigate(`/theatre/${theatre.id}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to create theatre');
    } finally {
      setIsSubmitting(false);
    }
  };

  const reviewDisabledReason =
    blankPathDeferred
      ? 'Blank authoring remains staged until full template composition support exists.'
      : path === 'alpamayo'
        ? 'Alpamayo recommendations are not yet live.'
        : !constructId.trim()
          ? 'Add a construct ID to continue.'
          : selectedTemplateDetailLoading
            ? 'Loading full template definition…'
            : selectedTemplateDetailError
              ? 'Template detail failed to load.'
              : null;

  return (
    <div className="p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <Link
            to="/theatres"
            className="mb-3 inline-flex items-center gap-1.5 text-[13px] text-[var(--e-text-muted)] no-underline transition hover:text-[var(--e-purple-700)]"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Theatres
          </Link>

          <p className="max-w-3xl text-[14px] leading-6 text-[var(--e-text-secondary)]">
            Theatre Templates are live market and certificate contracts. Scenario Packs stay separate. This flow keeps
            template creation honest: template-backed launch works today, blank authoring is deferred, and Alpamayo
            remains staged until recommendation data exists.
          </p>
        </div>

        <Stepper steps={steps} current={step} />

        {step === 'choose-path' ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-4 py-4 text-[13px] leading-6 text-[var(--e-purple-700)]">
              Template-backed theatre creation is the only live path today. Blank authoring and Alpamayo recommendations
              remain staged until their backend contracts are ready.
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <PathCard path="blank" selected={path === 'blank'} onClick={() => choosePath('blank')} disabled />
              <PathCard path="template" selected={path === 'template'} onClick={() => choosePath('template')} recommended />
              <PathCard path="alpamayo" selected={path === 'alpamayo'} onClick={() => choosePath('alpamayo')} disabled />
            </div>
          </div>
        ) : null}

        {step === 'select-template' ? (
          <SectionCard title="Select a Template" eyebrow="Template Library">
            {templatesError ? (
              <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-4 text-[13px] text-[var(--e-red-600)]">
                <div className="font-semibold">Failed to load templates</div>
                <div className="mt-1">{templatesError.message}</div>
                <button
                  type="button"
                  onClick={() => {
                    void refetchTemplates();
                  }}
                  className="mt-3 inline-flex h-9 items-center rounded-md border border-[var(--e-red-200)] bg-white px-3 text-[12px] font-semibold text-[var(--e-red-600)] transition hover:bg-[var(--e-red-50)]"
                >
                  Retry
                </button>
              </div>
            ) : null}

            {templatesLoading ? (
              <div className="flex items-center gap-2 text-[13px] text-[var(--e-text-muted)]">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading theatre templates…
              </div>
            ) : null}

            {templatesEmpty && !templatesLoading && !templatesError ? (
              <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-5 py-5 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                No theatre templates are currently available. Template-backed creation is the live path today, so this
                flow remains blocked until operators publish templates.
              </div>
            ) : null}

            {!templatesLoading && templates.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {templates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    selected={selectedTemplate?.id === template.id}
                    onClick={() => selectTemplate(template)}
                  />
                ))}
              </div>
            ) : null}

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={goBack}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </button>
            </div>
          </SectionCard>
        ) : null}

        {step === 'select-suggestion' ? (
          <SectionCard title="Alpamayo Suggestions" eyebrow="Recommendation Engine">
            <div className="mb-5 rounded-lg border border-[color:oklch(0.525_0.155_260_/_0.15)] bg-[color:oklch(0.525_0.155_260_/_0.08)] px-4 py-4 text-[13px] leading-6 text-[var(--e-text-secondary)]">
              {alpamayoEnabled
                ? 'Alpamayo is enabled at the feature-flag layer, but no recommendation payload is available yet.'
                : 'Alpamayo remains staged. Recommendation cards will populate once the backend recommendation engine is live.'}
            </div>

            {alpamayoSuggestions.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[var(--e-border-primary)] bg-[var(--e-bg-sunken)] px-5 py-5">
                <div className="mb-2 text-[15px] font-semibold text-[var(--e-text-primary)]">No suggestions available</div>
                <div className="text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  Use the live template path to create a theatre today. Alpamayo recommendations are preserved as a
                  design contract here, not a live backend flow.
                </div>
              </div>
            ) : null}

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={goBack}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </button>
            </div>
          </SectionCard>
        ) : null}

        {step === 'configure' ? (
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
            <SectionCard title="Configure Theatre" eyebrow="Summary First">
              {path ? (
                <div className={clsx('mb-5 rounded-lg border px-4 py-4', PATH_COPY[path].tone)}>
                  <div className="mb-1 text-[12px] font-semibold">{PATH_COPY[path].title}</div>
                  <div className="text-[13px] leading-6">
                    {path === 'template'
                      ? 'Template-backed creation persists the selected template definition, construct ID, and market type. Editorial fields below are planning inputs for now.'
                      : path === 'blank'
                        ? 'Blank theatre authoring is intentionally deferred. Use this surface to understand the eventual flow, then switch to the live template path.'
                        : 'Alpamayo recommendations are not yet live. This section reflects the planned guided configuration shape only.'}
                  </div>
                </div>
              ) : null}

              <div className="space-y-4">
                <label className="block">
                  <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">Market title</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">
                    What traders will see on the theatre surface.
                  </div>
                  <input
                    type="text"
                    value={marketTitle}
                    onChange={(event) => setMarketTitle(event.target.value)}
                    disabled={blankPathDeferred || path === 'alpamayo'}
                    placeholder="Will the Fed cut rates before July 2026?"
                    className="mt-2 h-11 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                  />
                </label>

                <label className="block">
                  <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">Additional context</div>
                  <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">
                    Optional descriptive context for operators and traders.
                  </div>
                  <textarea
                    value={marketContext}
                    onChange={(event) => setMarketContext(event.target.value)}
                    disabled={blankPathDeferred || path === 'alpamayo'}
                    rows={3}
                    placeholder="Why this theatre matters, what should be watched, and what the market is evaluating."
                    className="mt-2 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                  />
                </label>

                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block">
                    <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">Primary source</div>
                    <input
                      type="text"
                      value={primarySource}
                      onChange={(event) => setPrimarySource(event.target.value)}
                      disabled={blankPathDeferred || path === 'alpamayo'}
                      placeholder="Federal Reserve statement"
                      className="mt-2 h-11 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                    />
                  </label>
                  <label className="block">
                    <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">When this market ends</div>
                    <input
                      type="text"
                      value={endCondition}
                      onChange={(event) => setEndCondition(event.target.value)}
                      disabled={blankPathDeferred || path === 'alpamayo'}
                      placeholder="July 1, 2026 or on event resolution"
                      className="mt-2 h-11 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                    />
                  </label>
                </div>

                <label className="block">
                  <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">How this resolves</div>
                  <textarea
                    value={resolutionCriteria}
                    onChange={(event) => setResolutionCriteria(event.target.value)}
                    disabled={blankPathDeferred || path === 'alpamayo'}
                    rows={3}
                    placeholder="Resolving criteria in plain language."
                    className="mt-2 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[14px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                  />
                </label>
              </div>

              <div className="mt-5 overflow-hidden rounded-lg border border-[var(--e-border-primary)]">
                <button
                  type="button"
                  onClick={() => setShowAdvanced((current) => !current)}
                  className="flex w-full items-center gap-2 bg-[var(--e-bg-sunken)] px-4 py-3 text-left text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:text-[var(--e-text-primary)]"
                >
                  <Settings2 className={clsx('h-4 w-4 transition-transform', showAdvanced && 'rotate-90')} />
                  Advanced settings
                  <span className="ml-auto text-[11px] font-medium text-[var(--e-text-muted)]">Market type, construct ID</span>
                </button>

                {showAdvanced ? (
                  <div className="space-y-4 border-t border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-4">
                    <label className="block">
                      <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">Construct ID</div>
                      <input
                        type="text"
                        value={constructId}
                        onChange={(event) => setConstructId(event.target.value)}
                        disabled={blankPathDeferred || path === 'alpamayo'}
                        placeholder="fed_rate_cut_2026_q3"
                        className="mt-2 h-11 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 font-mono text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-disabled)] focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                      />
                    </label>

                    <label className="block">
                      <div className="text-[13px] font-semibold text-[var(--e-text-primary)]">Market type</div>
                      <select
                        value={inquiryClass}
                        onChange={(event) => setInquiryClass(event.target.value as InquiryClass)}
                        disabled={blankPathDeferred || path === 'alpamayo'}
                        className="mt-2 h-11 w-full rounded-lg border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[14px] text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] disabled:cursor-not-allowed disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                      >
                        {INQUIRY_CLASSES.map((item) => (
                          <option key={item} value={item}>
                            {INQUIRY_LABELS[item]}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                ) : null}
              </div>

              {!constructId && marketTitle && path === 'template' ? (
                <button
                  type="button"
                  onClick={() => {
                    const slug = marketTitle
                      .toLowerCase()
                      .replace(/[^a-z0-9\s]/g, '')
                      .trim()
                      .replace(/\s+/g, '_')
                      .slice(0, 40);
                    setConstructId(slug);
                    setShowAdvanced(true);
                  }}
                  className="mt-3 text-[12px] font-medium text-[var(--e-purple-700)] transition hover:underline"
                >
                  Auto-generate construct ID from title
                </button>
              ) : null}

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={goBack}
                  className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </button>
                <button
                  type="button"
                  onClick={() => setStep('review')}
                  disabled={!canReviewTemplatePath}
                  className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)] disabled:cursor-not-allowed disabled:border-[var(--e-border-secondary)] disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                >
                  Review
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>

              {reviewDisabledReason ? (
                <div className="mt-3 text-[12px] text-[var(--e-text-muted)]">{reviewDisabledReason}</div>
              ) : null}
            </SectionCard>

            <div className="space-y-5">
              <SectionCard title="Creation Path" eyebrow="Selected Mode">
                {path ? (
                  <div className="space-y-3">
                    <DetailRow label="Path" value={PATH_COPY[path].title} />
                    <DetailRow label="Live today" value={path === 'template' ? 'Yes' : 'No'} />
                    <DetailRow
                      label="Template"
                      value={selectedTemplate?.display_name ?? selectedSuggestion?.title ?? 'None selected'}
                    />
                  </div>
                ) : (
                  <div className="text-[13px] text-[var(--e-text-muted)]">No creation path selected.</div>
                )}
              </SectionCard>

              <SectionCard title="Launch Contract" eyebrow="Backend Truth">
                <div className="space-y-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  <p>
                    Launch currently persists only the selected template definition, construct ID, and inquiry class
                    to <span className="font-mono text-[var(--e-text-primary)]">POST /api/v1/theatres</span>.
                  </p>
                  <p>
                    The descriptive planning fields on this page are surfaced to match the locked design reference, but
                    they are not yet part of the live theatre creation payload.
                  </p>
                </div>
              </SectionCard>
            </div>
          </div>
        ) : null}

        {step === 'review' ? (
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
            <SectionCard title="Review Theatre" eyebrow="Final Check">
              <div className="space-y-4">
                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Market Title
                  </div>
                  <div className="text-[17px] font-semibold text-[var(--e-text-primary)]">{marketTitle || 'Untitled theatre'}</div>
                  {marketContext ? <div className="mt-2 text-[13px] leading-6 text-[var(--e-text-secondary)]">{marketContext}</div> : null}
                </div>

                <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-4 py-2">
                  <DetailRow label="Path" value={PATH_COPY[path ?? 'template'].title} />
                  <DetailRow label="Template" value={selectedTemplate?.display_name ?? '—'} />
                  <DetailRow label="Construct ID" value={constructId} mono />
                  <DetailRow label="Market type" value={INQUIRY_LABELS[inquiryClass]} />
                  <DetailRow label="Primary source" value={primarySource || '—'} />
                  <DetailRow label="End condition" value={endCondition || '—'} />
                </div>

                {resolutionCriteria ? (
                  <div className="rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-4">
                    <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                      Resolution Criteria
                    </div>
                    <div className="text-[13px] leading-6 text-[var(--e-text-secondary)]">{resolutionCriteria}</div>
                  </div>
                ) : null}

                {submitError ? (
                  <div className="rounded-lg border border-[color:oklch(0.545_0.185_25_/_0.18)] bg-[var(--e-red-50)] px-4 py-3 text-[13px] text-[var(--e-red-600)]">
                    {submitError}
                  </div>
                ) : null}

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={goBack}
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] font-semibold text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={isSubmitting || !canSubmit}
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)] disabled:cursor-not-allowed disabled:border-[var(--e-border-secondary)] disabled:bg-[var(--e-bg-sunken)] disabled:text-[var(--e-text-disabled)]"
                  >
                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <LayoutTemplate className="h-4 w-4" />}
                    {isSubmitting ? 'Creating…' : 'Create Theatre'}
                  </button>
                </div>
              </div>
            </SectionCard>

            <div className="space-y-5">
              <SectionCard title="Post-Launch" eyebrow="What Happens Next">
                <div className="space-y-3 text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  <p>The theatre is created in <span className="font-semibold text-[var(--e-text-primary)]">DRAFT</span> state.</p>
                  <p>From the theatre detail page you can commit it, start the run, settle it, and deploy agents in theatre context.</p>
                </div>
              </SectionCard>

              <SectionCard title="Operator Note" eyebrow="Current Scope">
                <div className="text-[13px] leading-6 text-[var(--e-text-secondary)]">
                  This pass keeps create-theatre honest to the live backend. No blank template authoring, no Alpamayo
                  recommendations, and no hidden runtime configuration are implied here.
                </div>
              </SectionCard>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
