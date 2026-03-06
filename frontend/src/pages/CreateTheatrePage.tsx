/**
 * CreateTheatrePage — Theatre creation flow.
 *
 * Three entry paths (locked product model):
 *   1. Blank Theatre — staged shell until template authoring is available
 *   2. From Theatre Template — pick from catalog, template pre-fills
 *   3. Suggested by Alpamayo — recommendation cards with confidence,
 *      reasoning, context chips. Feature-flagged; shows design-contract
 *      shell with empty state when backend support unavailable.
 *
 * All paths submit to POST /api/v1/theatres.
 *
 * DESIGN REF: output/design_reference/echelon_create_theatre_v1.html
 * PRODUCT DISTINCTION: Theatre Templates = market contracts (here).
 *   Scenario Packs = RLMF/RL constructs (separate surface).
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  LayoutTemplate,
  Sparkles,
  ChevronLeft,
  ArrowLeft,
  Check,
  Settings,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useTheatreTemplate, useTheatreTemplates } from '../hooks/useTheatreTemplates';
import { theatreApi } from '../api/theatres';
import { EmptyState } from '../components/empty-states/EmptyState';
import { isEnabled } from '../lib/featureFlags';
import type { TemplateSummaryResponse, TheatreCreateRequest } from '../types/theatre';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type CreationPath = 'blank' | 'template' | 'alpamayo';
type Step = 'choose-path' | 'select-template' | 'select-suggestion' | 'configure' | 'review';

const INQUIRY_CLASSES = [
  'COUNTERFACTUAL',
  'INVESTIGATIVE',
  'INSPECTION',
  'SURVEY',
  'SCRUTINY',
] as const;

type InquiryClass = (typeof INQUIRY_CLASSES)[number];

/** User-facing labels for inquiry classes (design ref: "Market type" not "Inquiry class") */
const INQUIRY_LABELS: Record<InquiryClass, string> = {
  COUNTERFACTUAL: 'Binary Event',
  INVESTIGATIVE: 'Investigative',
  INSPECTION: 'Inspection',
  SURVEY: 'Survey',
  SCRUTINY: 'Scrutiny',
};

/** Alpamayo suggestion shape — matches design contract */
interface AlpamayoSuggestion {
  id: string;
  title: string;
  templateId: string;
  inquiryLabel: string;
  confidence: number;
  confidenceLevel: 'high' | 'medium' | 'low';
  context: string[];
  reason: string;
  sourceOfTruth: string;
  resolution: string;
  stopCondition: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CreateTheatrePage() {
  const navigate = useNavigate();
  const {
    templates,
    isLoading: templatesLoading,
    error: templatesError,
    isEmpty: templatesEmpty,
  } = useTheatreTemplates();

  const [path, setPath] = useState<CreationPath | null>(null);
  const [step, setStep] = useState<Step>('choose-path');
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateSummaryResponse | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<AlpamayoSuggestion | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Form state
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

  // ---------------------------------------------------------------------------
  // Derived
  // ---------------------------------------------------------------------------

  const alpamayoEnabled = isEnabled('CYCLE_017_TAO_FLOW');

  // Alpamayo suggestions — empty until backend wired (design contract shell)
  const alpamayoSuggestions: AlpamayoSuggestion[] = [];

  const blankPathDeferred = path === 'blank';
  const canReviewTemplatePath =
    path === 'template' &&
    constructId.trim().length > 0 &&
    !!selectedTemplateDetail &&
    !selectedTemplateDetailLoading;
  const canSubmit = canReviewTemplatePath;

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const choosePath = (p: CreationPath) => {
    setPath(p);
    if (p === 'blank') {
      setSelectedTemplate(null);
      setSelectedSuggestion(null);
      setStep('configure');
    } else if (p === 'template') {
      setStep('select-template');
    } else if (p === 'alpamayo') {
      setStep('select-suggestion');
    }
  };

  const selectTemplate = (t: TemplateSummaryResponse) => {
    setSelectedTemplate(t);
    setSelectedSuggestion(null);
    // Pre-fill from template
    setConstructId('');
    setMarketTitle((current) => current || t.display_name);
    if (t.inquiry_class) {
      setInquiryClass(t.inquiry_class as InquiryClass);
    }
    setStep('configure');
  };

  const selectSuggestion = (s: AlpamayoSuggestion) => {
    setSelectedSuggestion(s);
    setSelectedTemplate(null);
    // Pre-fill from suggestion
    setMarketTitle(s.title);
    setPrimarySource(s.sourceOfTruth);
    setEndCondition(s.stopCondition);
    setResolutionCriteria(s.resolution);
    setStep('configure');
  };

  const goBack = () => {
    setSubmitError(null);
    if (step === 'review') {
      setStep('configure');
    } else if (step === 'configure') {
      if (path === 'template') setStep('select-template');
      else if (path === 'alpamayo') setStep('select-suggestion');
      else {
        setStep('choose-path');
        setPath(null);
      }
    } else if (step === 'select-template' || step === 'select-suggestion') {
      setStep('choose-path');
      setPath(null);
    }
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to create theatre:', err);
      setSubmitError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Step indicator
  // ---------------------------------------------------------------------------

  const activeSteps: { key: Step; label: string }[] = (() => {
    const base = [{ key: 'choose-path' as Step, label: 'Choose Path' }];
    if (path === 'template') {
      base.push({ key: 'select-template', label: 'Template' });
    } else if (path === 'alpamayo') {
      base.push({ key: 'select-suggestion', label: 'Alpamayo' });
    }
    base.push({ key: 'configure', label: 'Configure' });
    base.push({ key: 'review', label: 'Review' });
    return base;
  })();

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/theatres"
        className="inline-flex items-center gap-1.5 text-xs text-terminal-text-muted hover:text-terminal-text transition-colors"
      >
        <ArrowLeft className="w-3 h-3" />
        Back to Theatres
      </Link>

      <h1 className="text-lg font-bold text-terminal-text">Create Theatre</h1>

      {/* Flow progress bar */}
      <div className="flex items-center gap-0 p-3 bg-terminal-surface border border-terminal-border rounded-lg">
        {activeSteps.map((s, i) => {
          const stepIdx = activeSteps.findIndex((x) => x.key === step);
          const isDone = i < stepIdx;
          const isActive = s.key === step;
          return (
            <div key={s.key} className="flex items-center flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    'w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-mono font-bold border',
                    isDone && 'bg-status-success border-status-success text-white',
                    isActive && 'bg-status-paradox border-status-paradox text-white',
                    !isDone && !isActive && 'bg-terminal-panel border-terminal-border text-terminal-text-muted',
                  )}
                >
                  {isDone ? <Check className="w-3 h-3" /> : i + 1}
                </span>
                <span
                  className={clsx(
                    'text-xs font-medium whitespace-nowrap',
                    isActive ? 'text-terminal-text font-semibold' : 'text-terminal-text-muted',
                  )}
                >
                  {s.label}
                </span>
              </div>
              {i < activeSteps.length - 1 && (
                <div
                  className={clsx(
                    'flex-1 h-0.5 mx-3 min-w-[20px]',
                    isDone ? 'bg-status-success' : 'bg-terminal-border',
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* ═══════════ STEP: Choose Path ═══════════ */}
      {step === 'choose-path' && (
        <div className="space-y-4">
          <p className="text-xs text-terminal-text-secondary">
            How would you like to create this theatre?
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Blank Theatre */}
            <button
              onClick={() => choosePath('blank')}
              className={clsx(
                'text-left bg-terminal-surface border-2 rounded-lg p-5 transition-all',
                'hover:border-status-paradox/30 hover:shadow-md',
                'border-terminal-border',
              )}
            >
              <div className="w-12 h-12 rounded-lg bg-terminal-panel border border-terminal-border flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-terminal-text-muted" />
              </div>
              <div className="text-sm font-semibold text-terminal-text mb-1">Blank Theatre</div>
              <div className="text-xs text-terminal-text-muted mb-4">
                Start from scratch with full control over your market design.
              </div>
              <div className="space-y-1.5">
                <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                  <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  Define every aspect manually
                </div>
                <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                  <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  Best for novel market structures
                </div>
              </div>
            </button>

            {/* From Template */}
            <button
              onClick={() => choosePath('template')}
              className={clsx(
                'text-left bg-terminal-surface border-2 rounded-lg p-5 transition-all',
                'hover:border-status-paradox/30 hover:shadow-md',
                'border-terminal-border',
              )}
            >
              <div className="w-12 h-12 rounded-lg bg-status-paradox/10 border border-status-paradox/20 flex items-center justify-center mb-4">
                <LayoutTemplate className="w-6 h-6 text-status-paradox" />
              </div>
              <div className="text-sm font-semibold text-terminal-text mb-1">From Theatre Template</div>
              <div className="text-xs text-terminal-text-muted mb-4">
                Choose a structured market contract with pre-configured resolution rules and evidence
                requirements.
              </div>
              <div className="space-y-1.5">
                <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                  <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  Resolution rules built in
                </div>
                <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                  <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  6 market types available
                </div>
              </div>
            </button>

            {/* Suggested by Alpamayo */}
            <div className="relative">
              <button
                onClick={() => choosePath('alpamayo')}
                className={clsx(
                  'w-full text-left bg-terminal-surface border-2 rounded-lg p-5 transition-all',
                  'hover:border-status-info/30 hover:shadow-md',
                  'border-terminal-border',
                )}
              >
                <div className="w-12 h-12 rounded-lg bg-status-info/10 border border-status-info/20 flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-status-info" />
                </div>
                <div className="text-sm font-semibold text-terminal-text mb-1">
                  Suggested by Alpamayo
                </div>
                <div className="text-xs text-terminal-text-muted mb-4">
                  Alpamayo recommends a market structure based on events and signals. Most fields are
                  pre-filled for you.
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                    <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    Ready to launch with minimal edits
                  </div>
                  <div className="flex items-start gap-2 text-[11px] text-terminal-text-muted">
                    <Check className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    Explains why each choice fits
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════ STEP: Select Template (2A) ═══════════ */}
      {step === 'select-template' && (
        <div className="space-y-4">
          <h2 className="text-base font-bold text-terminal-text">Select a Template</h2>

          {templatesError && (
            <div className="p-3 text-status-danger text-xs rounded-lg bg-status-danger/5 border border-status-danger/20">
              Failed to load templates: {templatesError.message}
            </div>
          )}

          {templatesLoading && (
            <div className="text-xs text-terminal-text-muted">Loading templates…</div>
          )}

          {templatesEmpty && !templatesLoading && !templatesError && (
            <EmptyState
              type="NOT_YET_GENERATED"
              icon={<LayoutTemplate className="w-6 h-6" />}
              title="No templates available"
              description="Theatre templates define the contract structure for prediction markets. Templates are configured by platform operators."
              triggerText="Contact your administrator to add templates."
            />
          )}

          {!templatesLoading && !templatesEmpty && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => selectTemplate(t)}
                  className={clsx(
                    'text-left bg-terminal-surface border-2 rounded-lg p-5 transition-all flex flex-col',
                    'hover:border-status-paradox/30 hover:shadow-sm',
                    'border-terminal-border',
                  )}
                >
                  <div className="flex items-start justify-between mb-3">
                    {t.inquiry_class && (
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-status-info/10 text-status-info border border-status-info/20">
                        {t.inquiry_class}
                      </span>
                    )}
                    <div className="w-5 h-5 rounded-full border-2 border-terminal-border flex items-center justify-center flex-shrink-0" />
                  </div>
                  <div className="text-sm font-semibold text-terminal-text mb-1">
                    {t.display_name}
                  </div>
                  {t.description && (
                    <div className="text-xs text-terminal-text-secondary line-clamp-2 mb-3">
                      {t.description}
                    </div>
                  )}
                  <div className="mt-auto pt-3 border-t border-terminal-border/50 text-[10px] font-mono text-terminal-text-muted">
                    {t.template_family}
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={goBack}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-terminal-border text-terminal-text-secondary hover:bg-terminal-hover"
            >
              <ChevronLeft className="w-3 h-3 inline mr-1" />
              Back
            </button>
          </div>
        </div>
      )}

      {/* ═══════════ STEP: Alpamayo Suggestions (2B) ═══════════ */}
      {step === 'select-suggestion' && (
        <div className="space-y-4">
          {/* Alpamayo header */}
          <div className="flex items-start gap-4 p-5 bg-status-info/5 border border-status-info/15 rounded-lg">
            <div className="w-10 h-10 rounded-lg bg-status-info/10 border border-status-info/20 flex items-center justify-center flex-shrink-0 font-mono font-bold text-status-info text-lg">
              A
            </div>
            <div>
              <p className="text-xs text-terminal-text-secondary">
                <strong className="text-terminal-text">Alpamayo</strong> recommends market
                structures based on detected events, signal clusters, and historical performance.
                Pick a suggestion to get started — you can adjust anything before launch.
              </p>
              {!alpamayoEnabled && (
                <p className="text-[11px] text-terminal-text-muted mt-1 italic">
                  Alpamayo backend integration coming in Cycle 017. These suggestions will be
                  populated by the recommendation engine.
                </p>
              )}
            </div>
          </div>

          {/* Suggestion grid or empty state */}
          {alpamayoSuggestions.length === 0 ? (
            <EmptyState
              type="NOT_YET_GENERATED"
              icon={<Sparkles className="w-6 h-6" />}
              title="No suggestions available"
              description={
                alpamayoEnabled
                  ? 'Alpamayo hasn\u2019t generated any suggestions yet. Check back when new events and signal clusters are detected.'
                  : 'Alpamayo\u2019s recommendation engine requires TAO Flow integration (Cycle 017). Once enabled, suggestions with confidence scores and reasoning will appear here.'
              }
              triggerText={
                alpamayoEnabled
                  ? 'Suggestions refresh automatically when new signals arrive.'
                  : 'You can still create a theatre via Blank or Template paths.'
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {alpamayoSuggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSuggestion(s)}
                  className={clsx(
                    'text-left bg-terminal-surface border-2 rounded-lg p-5 transition-all flex flex-col',
                    'hover:border-status-info/30 hover:shadow-sm',
                    selectedSuggestion?.id === s.id
                      ? 'border-status-paradox bg-status-paradox/5'
                      : 'border-terminal-border',
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-sm font-semibold text-terminal-text flex-1">{s.title}</div>
                    <div
                      className={clsx(
                        'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ml-3',
                        selectedSuggestion?.id === s.id
                          ? 'border-status-paradox bg-status-paradox text-white'
                          : 'border-terminal-border',
                      )}
                    >
                      {selectedSuggestion?.id === s.id && <Check className="w-3 h-3" />}
                    </div>
                  </div>

                  {/* Confidence bar */}
                  <div
                    className={clsx(
                      'flex items-center gap-1.5 text-xs font-semibold mb-3',
                      s.confidenceLevel === 'high' && 'text-status-success',
                      s.confidenceLevel === 'medium' && 'text-yellow-500',
                      s.confidenceLevel === 'low' && 'text-terminal-text-muted',
                    )}
                  >
                    <div className="w-12 h-1.5 rounded-full bg-terminal-panel overflow-hidden">
                      <div
                        className={clsx(
                          'h-full rounded-full',
                          s.confidenceLevel === 'high' && 'bg-status-success',
                          s.confidenceLevel === 'medium' && 'bg-yellow-500',
                          s.confidenceLevel === 'low' && 'bg-terminal-text-muted',
                        )}
                        style={{ width: `${s.confidence}%` }}
                      />
                    </div>
                    {s.confidence}% fit
                  </div>

                  {/* Context chips */}
                  <div className="flex flex-wrap gap-1 mb-3">
                    {s.context.map((c) => (
                      <span
                        key={c}
                        className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-terminal-panel border border-terminal-border text-terminal-text-muted"
                      >
                        {c}
                      </span>
                    ))}
                  </div>

                  {/* Reasoning */}
                  <p className="text-xs text-terminal-text-secondary leading-relaxed mb-3 flex-1">
                    {s.reason}
                  </p>

                  {/* Meta grid */}
                  <div className="grid grid-cols-2 gap-2 pt-3 border-t border-terminal-border/50 mt-auto">
                    <div>
                      <div className="text-[9px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                        Market type
                      </div>
                      <div className="text-[11px] font-medium text-terminal-text">
                        {s.inquiryLabel}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                        Source
                      </div>
                      <div className="text-[11px] font-medium text-terminal-text">
                        {s.sourceOfTruth}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                        Resolves by
                      </div>
                      <div className="text-[11px] font-medium text-terminal-text">
                        {s.resolution}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                        Ends
                      </div>
                      <div className="text-[11px] font-medium text-terminal-text">
                        {s.stopCondition}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={goBack}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-terminal-border text-terminal-text-secondary hover:bg-terminal-hover"
            >
              <ChevronLeft className="w-3 h-3 inline mr-1" />
              Back
            </button>
          </div>
        </div>
      )}

      {/* ═══════════ STEP: Configure ═══════════ */}
      {step === 'configure' && (
        <div className="space-y-5">
          {/* Alpamayo recommendation summary (only when coming from alpamayo path) */}
          {path === 'alpamayo' && selectedSuggestion && (
            <div className="p-5 bg-status-info/5 border border-status-info/15 rounded-lg">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-status-info bg-status-info/10 px-2 py-0.5 rounded">
                  Alpamayo Recommendation
                </span>
                <span className="ml-auto text-xs font-semibold text-status-success flex items-center gap-1.5">
                  <span className="w-10 h-1.5 rounded-full bg-terminal-panel overflow-hidden inline-block">
                    <span
                      className="block h-full rounded-full bg-status-success"
                      style={{ width: `${selectedSuggestion.confidence}%` }}
                    />
                  </span>
                  {selectedSuggestion.confidence}% fit
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-terminal-text-muted">Recommended structure</span>
                  <div className="font-semibold text-terminal-text">{selectedSuggestion.inquiryLabel}</div>
                </div>
                <div>
                  <span className="text-terminal-text-muted">How it resolves</span>
                  <div className="font-semibold text-terminal-text">{selectedSuggestion.resolution}</div>
                </div>
                <div>
                  <span className="text-terminal-text-muted">Primary source</span>
                  <div className="font-semibold text-terminal-text">{selectedSuggestion.sourceOfTruth}</div>
                </div>
                <div>
                  <span className="text-terminal-text-muted">Suggested end</span>
                  <div className="font-semibold text-terminal-text">{selectedSuggestion.stopCondition}</div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-status-info/10 text-xs text-terminal-text-secondary">
                {selectedSuggestion.reason}
              </div>
            </div>
          )}

          {/* Core fields — "Your Market" section */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg p-5">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted mb-5 pb-2 border-b border-terminal-border/50">
              Your Market
            </div>

            {(path === 'template' || blankPathDeferred) && (
              <div className="mb-5 rounded-lg border border-status-info/20 bg-status-info/5 p-3 text-[11px] leading-relaxed text-terminal-text-secondary">
                {blankPathDeferred
                  ? 'Blank theatre authoring is staged until the backend can build a full schema-valid template from this form. Use From Theatre Template to create a theatre today.'
                  : 'Today, creation persists the selected template, construct ID, and market type. The editorial fields below are design-shell inputs until deeper theatre configuration support lands.'}
              </div>
            )}

            <div className="space-y-4">
              <label className="block">
                <span className="text-xs font-semibold text-terminal-text">Market title</span>
                <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                  The question traders will see. Make it clear and specific.
                </span>
                <input
                  type="text"
                  value={marketTitle}
                  onChange={(e) => setMarketTitle(e.target.value)}
                  placeholder="e.g. Will the Fed cut rates before July 2026?"
                  className={clsx(
                    'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm',
                    'bg-terminal-panel border border-terminal-border text-terminal-text',
                    'placeholder:text-terminal-text-muted',
                    'focus:outline-none focus:border-status-paradox/50',
                    path === 'alpamayo' && selectedSuggestion && 'bg-status-paradox/5 border-status-paradox/20',
                  )}
                  disabled={blankPathDeferred}
                />
              </label>

              <label className="block">
                <span className="text-xs font-semibold text-terminal-text">Additional context</span>
                <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                  Optional. Helps traders understand what this market is asking.
                </span>
                <textarea
                  value={marketContext}
                  onChange={(e) => setMarketContext(e.target.value)}
                  placeholder="Provide additional context for market participants..."
                  rows={2}
                  className={clsx(
                    'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm resize-y',
                    'bg-terminal-panel border border-terminal-border text-terminal-text',
                    'placeholder:text-terminal-text-muted',
                    'focus:outline-none focus:border-status-paradox/50',
                  )}
                  disabled={blankPathDeferred}
                />
              </label>

              <div className="grid grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-xs font-semibold text-terminal-text">Primary source</span>
                  <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                    Where resolution comes from.
                  </span>
                  <input
                    type="text"
                    value={primarySource}
                    onChange={(e) => setPrimarySource(e.target.value)}
                    placeholder="e.g. Federal Reserve FOMC Statement"
                    className={clsx(
                      'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm',
                      'bg-terminal-panel border border-terminal-border text-terminal-text',
                      'placeholder:text-terminal-text-muted',
                      'focus:outline-none focus:border-status-paradox/50',
                    )}
                    disabled={blankPathDeferred}
                  />
                </label>

                <label className="block">
                  <span className="text-xs font-semibold text-terminal-text">When this market ends</span>
                  <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                    A date, an event, or both.
                  </span>
                  <input
                    type="text"
                    value={endCondition}
                    onChange={(e) => setEndCondition(e.target.value)}
                    placeholder="e.g. July 1, 2026"
                    className={clsx(
                      'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm',
                      'bg-terminal-panel border border-terminal-border text-terminal-text',
                      'placeholder:text-terminal-text-muted',
                      'focus:outline-none focus:border-status-paradox/50',
                    )}
                    disabled={blankPathDeferred}
                  />
                </label>
              </div>

              <label className="block">
                <span className="text-xs font-semibold text-terminal-text">How this resolves</span>
                <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                  In plain language, what needs to happen for the market to settle.
                </span>
                <textarea
                  value={resolutionCriteria}
                  onChange={(e) => setResolutionCriteria(e.target.value)}
                  placeholder="e.g. Resolves YES if the Federal Reserve announces a rate cut of 25bps or more..."
                  rows={2}
                  className={clsx(
                    'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm resize-y',
                    'bg-terminal-panel border border-terminal-border text-terminal-text',
                    'placeholder:text-terminal-text-muted',
                    'focus:outline-none focus:border-status-paradox/50',
                  )}
                  disabled={blankPathDeferred}
                />
              </label>
            </div>
          </div>

          {/* Advanced settings (collapsed) */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center gap-2 px-5 py-3 text-xs font-medium text-terminal-text-muted hover:text-terminal-text-secondary"
            >
              <Settings className={clsx('w-3.5 h-3.5 transition-transform', showAdvanced && 'rotate-90')} />
              Advanced settings
              <span className="flex-1" />
              <span className="text-[11px] text-terminal-text-muted">
                Market type, evidence, verification
              </span>
            </button>
            {showAdvanced && (
              <div className="px-5 pb-5 pt-3 border-t border-terminal-border/50 space-y-4">
                <label className="block">
                  <span className="text-xs font-semibold text-terminal-text">Construct ID</span>
                  <span className="block text-[11px] text-terminal-text-muted mt-0.5">
                    A unique slug identifying this market construct.
                  </span>
                  <input
                    type="text"
                    value={constructId}
                    onChange={(e) => setConstructId(e.target.value)}
                    placeholder="e.g. fed_rate_cut_2026_q3"
                    className={clsx(
                      'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm font-mono',
                      'bg-terminal-panel border border-terminal-border text-terminal-text',
                      'placeholder:text-terminal-text-muted',
                      'focus:outline-none focus:border-status-paradox/50',
                    )}
                    disabled={blankPathDeferred}
                  />
                </label>

                <div className="grid grid-cols-2 gap-4">
                  <label className="block">
                    <span className="text-xs font-semibold text-terminal-text">Market type</span>
                    <select
                      value={inquiryClass}
                      onChange={(e) => setInquiryClass(e.target.value as InquiryClass)}
                      className={clsx(
                        'mt-1.5 block w-full px-3 py-2 rounded-lg text-sm',
                        'bg-terminal-panel border border-terminal-border text-terminal-text',
                        'focus:outline-none focus:border-status-paradox/50',
                      )}
                      disabled={blankPathDeferred}
                    >
                      {INQUIRY_CLASSES.map((ic) => (
                        <option key={ic} value={ic}>
                          {INQUIRY_LABELS[ic]}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Auto-generate construct_id hint when not set */}
          {!blankPathDeferred && !constructId && marketTitle && (
            <button
              onClick={() => {
                const slug = marketTitle
                  .toLowerCase()
                  .replace(/[^a-z0-9\s]/g, '')
                  .trim()
                  .replace(/\s+/g, '_')
                  .slice(0, 40);
                setConstructId(slug);
                if (!showAdvanced) setShowAdvanced(true);
              }}
              className="text-[11px] text-status-info hover:underline"
            >
              Auto-generate construct ID from title
            </button>
          )}

          <div className="flex gap-3">
            <button
              onClick={goBack}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-terminal-border text-terminal-text-secondary hover:bg-terminal-hover"
            >
              <ChevronLeft className="w-3 h-3 inline mr-1" />
              Back
            </button>
            <button
              onClick={() => setStep('review')}
              disabled={!canReviewTemplatePath}
              className={clsx(
                'px-4 py-2 text-xs font-semibold rounded-lg',
                canReviewTemplatePath
                  ? 'bg-status-paradox text-white hover:bg-purple-400'
                  : 'bg-terminal-panel text-terminal-text-muted cursor-not-allowed',
              )}
            >
              {blankPathDeferred ? 'Template Authoring Pending' : 'Review'}
            </button>
          </div>

          {path === 'template' && selectedTemplateDetailLoading && (
            <div className="text-[11px] text-terminal-text-muted">
              Loading full template definition…
            </div>
          )}

          {path === 'template' && selectedTemplateDetailError && (
            <div className="rounded-lg border border-status-danger/20 bg-status-danger/5 p-3 text-[11px] text-status-danger">
              Failed to load the selected template definition. Creation is blocked until the full
              template JSON is available.
            </div>
          )}
        </div>
      )}

      {/* ═══════════ STEP: Review & Launch ═══════════ */}
      {step === 'review' && (
        <div className="space-y-5">
          {/* Summary card */}
          <div className="bg-terminal-surface border border-terminal-border rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-terminal-border/50">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                Theatre Configuration
              </span>
              <span
                className={clsx(
                  'text-[10px] font-bold uppercase px-2 py-0.5 rounded',
                  path === 'blank' && 'bg-terminal-panel text-terminal-text-muted border border-terminal-border',
                  path === 'template' && 'bg-status-paradox/10 text-status-paradox border border-status-paradox/20',
                  path === 'alpamayo' && 'bg-status-info/10 text-status-info border border-status-info/20',
                )}
              >
                {path === 'blank' ? 'Custom' : path === 'template' ? 'Template' : 'Alpamayo'}
              </span>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                  Market Title
                </div>
                <div className="text-base font-semibold text-terminal-text">{marketTitle}</div>
              </div>
              {marketContext && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                    Context
                  </div>
                  <div className="text-xs text-terminal-text-secondary">{marketContext}</div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                    Construct ID
                  </div>
                  <div className="text-xs font-mono text-terminal-text">{constructId}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                    Market Type
                  </div>
                  <div className="text-xs text-terminal-text">{INQUIRY_LABELS[inquiryClass]}</div>
                </div>
                {primarySource && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                      Primary Source
                    </div>
                    <div className="text-xs text-terminal-text">{primarySource}</div>
                  </div>
                )}
                {endCondition && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                      Ends
                    </div>
                    <div className="text-xs text-terminal-text">{endCondition}</div>
                  </div>
                )}
              </div>
              {resolutionCriteria && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                    Resolution Criteria
                  </div>
                  <div className="text-xs text-terminal-text-secondary">{resolutionCriteria}</div>
                </div>
              )}
              {selectedTemplate && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-terminal-text-muted">
                    Template
                  </div>
                  <div className="text-xs text-terminal-text">{selectedTemplate.display_name}</div>
                </div>
              )}
            </div>
          </div>

          {submitError && (
            <div className="p-3 text-status-danger text-xs rounded-lg bg-status-danger/5 border border-status-danger/20">
              {submitError}
            </div>
          )}

          <div className="rounded-lg border border-status-info/20 bg-status-info/5 p-3 text-[11px] text-terminal-text-secondary">
            Launch currently persists the template definition, construct ID, and inquiry class.
            The descriptive planning fields on this page are staged UI fields until deeper theatre
            configuration support is available.
          </div>

          <div className="flex gap-3">
            <button
              onClick={goBack}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-terminal-border text-terminal-text-secondary hover:bg-terminal-hover"
            >
              <ChevronLeft className="w-3 h-3 inline mr-1" />
              Back
            </button>
            <button
              onClick={handleCreate}
              disabled={isSubmitting}
              className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-status-paradox text-white hover:bg-purple-400 disabled:opacity-50"
            >
              {isSubmitting ? 'Creating…' : 'Create Theatre'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
