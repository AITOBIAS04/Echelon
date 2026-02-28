import type { InquiryClass } from '../../types/signal';
import { TEMPLATES } from '../../data/templates';

interface ClassSelectorProps {
  suggestedClass: InquiryClass;
  selectedClass: InquiryClass | null;
  onSelect: (cls: InquiryClass) => void;
}

const CLASS_DEFINITIONS: {
  class: InquiryClass;
  definition: string;
  executionPath: string;
  icon: string;
}[] = [
  {
    class: 'COUNTERFACTUAL',
    definition: 'What would happen if a scenario materialised?',
    executionPath: 'MARKET / LMSR',
    icon: 'rotate-45',
  },
  {
    class: 'INVESTIGATIVE',
    definition: 'Corroborate claims across multiple sources',
    executionPath: 'PRODUCT / Replay',
    icon: 'circle',
  },
  {
    class: 'INSPECTION',
    definition: 'Verify compliance against deterministic rules',
    executionPath: 'PRODUCT / Replay',
    icon: 'triangle',
  },
  {
    class: 'SURVEY',
    definition: 'Calibrate a construct against known baselines',
    executionPath: 'PRODUCT / Replay',
    icon: 'diamond',
  },
  {
    class: 'SCRUTINY',
    definition: 'Stress-test under adversarial conditions',
    executionPath: 'PRODUCT / Replay',
    icon: 'hexagon',
  },
];

function ClassIcon({ shape }: { shape: string }) {
  const base = 'h-6 w-6 border-2 border-current';
  switch (shape) {
    case 'rotate-45':
      return <div className={`${base} rotate-45`} />;
    case 'circle':
      return <div className={`${base} rounded-full`} />;
    case 'triangle':
      return (
        <div
          className="h-0 w-0"
          style={{
            borderLeft: '12px solid transparent',
            borderRight: '12px solid transparent',
            borderBottom: '20px solid currentColor',
          }}
        />
      );
    case 'diamond':
      return <div className={`${base} h-5 w-5 rotate-45 rounded-sm`} />;
    case 'hexagon':
      return <div className={`${base} rounded-md`} />;
    default:
      return <div className={base} />;
  }
}

export function ClassSelector({
  suggestedClass,
  selectedClass,
  onSelect,
}: ClassSelectorProps) {
  const active = selectedClass ?? suggestedClass;

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Inquiry Class
      </h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {CLASS_DEFINITIONS.map((def) => {
          const isActive = active === def.class;
          const isSuggested = suggestedClass === def.class;
          const templateCount = TEMPLATES.filter(
            (t) => t.inquiry_class === def.class
          ).length;

          return (
            <button
              key={def.class}
              onClick={() => onSelect(def.class)}
              className={`flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition-colors ${
                isActive
                  ? 'border-echelon-navy bg-echelon-navy/5 ring-2 ring-echelon-navy'
                  : 'border-echelon-border bg-white hover:border-slate-300'
              }`}
            >
              <div
                className={`${isActive ? 'text-echelon-navy' : 'text-slate-400'}`}
              >
                <ClassIcon shape={def.icon} />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span
                    className={`text-xs font-semibold uppercase tracking-[0.05em] ${
                      isActive ? 'text-echelon-navy' : 'text-slate-700'
                    }`}
                  >
                    {def.class}
                  </span>
                  {isSuggested && (
                    <span className="rounded bg-echelon-blue/10 px-1 py-0.5 text-[9px] font-medium uppercase text-echelon-blue">
                      suggested
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs leading-snug text-slate-500">
                  {def.definition}
                </p>
              </div>
              <div className="mt-auto flex w-full items-center justify-between pt-2">
                <span className="rounded border border-echelon-border px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                  {def.executionPath}
                </span>
                <span className="text-[10px] text-slate-400">
                  {templateCount} template{templateCount !== 1 ? 's' : ''}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
