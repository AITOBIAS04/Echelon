import type { InquiryClass } from '../../types/signal';
import type { TheatreTemplate } from '../../types/inquiry';
import { TEMPLATES } from '../../data/templates';
import { formatScore } from '../../utils/format';

interface TemplatePanelProps {
  selectedClass: InquiryClass;
  selectedTemplate: TheatreTemplate | null;
  onSelect: (template: TheatreTemplate) => void;
}

export function TemplatePanel({
  selectedClass,
  selectedTemplate,
  onSelect,
}: TemplatePanelProps) {
  const filtered = TEMPLATES.filter(
    (t) => t.inquiry_class === selectedClass
  );

  if (filtered.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-echelon-border p-6 text-center text-sm text-slate-400">
        No templates available for {selectedClass}
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Theatre Templates
      </h3>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {filtered.map((template) => {
          const isSelected =
            selectedTemplate?.template_id === template.template_id;

          return (
            <button
              key={template.template_id}
              onClick={() => onSelect(template)}
              className={`rounded-lg border p-4 text-left transition-colors ${
                isSelected
                  ? 'border-echelon-blue bg-echelon-blue/5 ring-2 ring-echelon-blue'
                  : 'border-echelon-border bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-echelon-navy">
                  {template.template_id}
                </span>
                <span className="shrink-0 rounded border border-echelon-border px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                  {template.execution_path === 'PRODUCT'
                    ? 'PRODUCT / Replay'
                    : 'MARKET / LMSR'}
                </span>
              </div>

              <p className="mt-1 text-sm text-slate-700">{template.name}</p>

              <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                <span>
                  {template.criteria_ids.length} criteria
                </span>
                <span>
                  {template.fixture_count} fixtures
                  <span className="ml-1 text-echelon-success">
                    {template.pass_count}P
                  </span>
                  {' / '}
                  <span className="text-echelon-error">
                    {template.fail_count}F
                  </span>
                </span>
                <span className="font-mono">
                  {formatScore(template.existing_composite)}
                </span>
              </div>

              {template.template_tags && template.template_tags.length > 0 && (
                <div className="mt-2 flex gap-1.5">
                  {template.template_tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-echelon-data-bg px-2 py-0.5 text-[10px] font-medium text-echelon-data-text"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
