/**
 * DomainFilterSelector — 9 domain categories with source group preview.
 * Used in the Investigation Creation Wizard step 3.
 */

const DOMAIN_CATEGORIES = [
  {
    id: 'financial_filings',
    label: 'Financial Filings',
    description: 'SEC, EDGAR, annual reports, quarterly earnings',
    sources: ['SEC EDGAR', 'Annual Reports', '10-K/10-Q'],
  },
  {
    id: 'regulatory',
    label: 'Regulatory',
    description: 'Government agencies, compliance databases, enforcement actions',
    sources: ['FDA', 'FTC', 'DOJ', 'EU Commission'],
  },
  {
    id: 'corporate_registry',
    label: 'Corporate Registry',
    description: 'Business registrations, beneficial ownership, corporate structure',
    sources: ['OpenCorporates', 'Companies House', 'State SOS'],
  },
  {
    id: 'litigation',
    label: 'Litigation',
    description: 'Court records, legal proceedings, patent disputes',
    sources: ['PACER', 'CourtListener', 'Patent Office'],
  },
  {
    id: 'media_news',
    label: 'Media & News',
    description: 'News outlets, press releases, investigative journalism',
    sources: ['Reuters', 'AP', 'Bloomberg', 'Local Media'],
  },
  {
    id: 'social_sentiment',
    label: 'Social Sentiment',
    description: 'Social media analysis, community forums, public opinion',
    sources: ['Twitter/X', 'Reddit', 'Forums'],
  },
  {
    id: 'supply_chain',
    label: 'Supply Chain',
    description: 'Trade data, shipping records, supplier networks',
    sources: ['ImportGenius', 'Panjiva', 'Trade DBs'],
  },
  {
    id: 'geopolitical',
    label: 'Geopolitical',
    description: 'Sanctions lists, political risk, country assessments',
    sources: ['OFAC', 'EU Sanctions', 'UN Lists'],
  },
  {
    id: 'technical',
    label: 'Technical',
    description: 'Patents, academic papers, technical standards',
    sources: ['USPTO', 'ArXiv', 'IEEE'],
  },
] as const;

export type DomainFilterId = (typeof DOMAIN_CATEGORIES)[number]['id'];

interface DomainFilterSelectorProps {
  selected: DomainFilterId[];
  onChange: (selected: DomainFilterId[]) => void;
}

export function DomainFilterSelector({ selected, onChange }: DomainFilterSelectorProps) {
  const toggle = (id: DomainFilterId) => {
    onChange(
      selected.includes(id)
        ? selected.filter((s) => s !== id)
        : [...selected, id],
    );
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-terminal-text-muted">
        Select domain categories to scope the investigation. Each category maps to specific OSINT source groups.
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {DOMAIN_CATEGORIES.map((cat) => {
          const isSelected = selected.includes(cat.id);
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => toggle(cat.id)}
              className={`text-left p-3 rounded-lg border transition-colors ${
                isSelected
                  ? 'border-echelon-cyan/50 bg-echelon-cyan/5'
                  : 'border-terminal-border hover:border-terminal-border/80 bg-terminal-surface'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-terminal-text">
                  {cat.label}
                </span>
                <div
                  className={`w-4 h-4 rounded border flex items-center justify-center ${
                    isSelected
                      ? 'border-echelon-cyan bg-echelon-cyan/20'
                      : 'border-terminal-border'
                  }`}
                >
                  {isSelected && (
                    <span className="text-echelon-cyan text-[10px]">✓</span>
                  )}
                </div>
              </div>
              <p className="text-[10px] text-terminal-text-muted leading-relaxed mb-2">
                {cat.description}
              </p>
              <div className="flex flex-wrap gap-1">
                {cat.sources.map((src) => (
                  <span
                    key={src}
                    className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-terminal-bg text-terminal-text-muted"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
      <div className="text-[10px] text-terminal-text-muted">
        {selected.length} of {DOMAIN_CATEGORIES.length} categories selected
      </div>
    </div>
  );
}
