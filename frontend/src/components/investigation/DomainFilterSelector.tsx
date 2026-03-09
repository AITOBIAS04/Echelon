/**
 * DomainFilterSelector — committed investigation ingestion filters.
 *
 * Domain filter IDs align to the backend DomainFilter enum
 * (backend/investigation/signal_scanner.py).
 */

import {
  Anchor,
  Building2,
  Gavel,
  Landmark,
  Plane,
  Satellite,
  Shield,
  Swords,
  Waves,
} from 'lucide-react';

const DOMAIN_CATEGORIES = [
  {
    id: 'corporate_and_entity',
    label: 'Corporate & Entity',
    description: 'Business registrations, beneficial ownership, corporate structure, identity checks',
    sources: ['OpenCorporates', 'Companies House', 'State SOS'],
    icon: Building2,
  },
  {
    id: 'finance_and_markets',
    label: 'Finance & Markets',
    description: 'SEC filings, earnings reports, market data, financial disclosures',
    sources: ['SEC EDGAR', '10-K/10-Q', 'Bloomberg'],
    icon: Landmark,
  },
  {
    id: 'maritime',
    label: 'Maritime',
    description: 'Vessel tracking, shipping records, port activity, maritime intelligence',
    sources: ['MarineTraffic', 'AIS Data', 'Lloyd\'s List'],
    icon: Anchor,
  },
  {
    id: 'airspace',
    label: 'Airspace',
    description: 'Flight tracking, airspace monitoring, aviation intelligence',
    sources: ['FlightRadar24', 'ADS-B Exchange', 'ICAO'],
    icon: Plane,
  },
  {
    id: 'geopolitical_and_conflict',
    label: 'Geopolitical & Conflict',
    description: 'Sanctions lists, political risk, conflict monitoring, country assessments',
    sources: ['OFAC', 'EU Sanctions', 'UN Lists', 'ACLED'],
    icon: Swords,
  },
  {
    id: 'cyber_threat',
    label: 'Cyber Threat',
    description: 'Threat intelligence, vulnerability databases, dark web monitoring',
    sources: ['CVE', 'VirusTotal', 'Shodan', 'MITRE ATT&CK'],
    icon: Shield,
  },
  {
    id: 'property_and_land',
    label: 'Property & Land',
    description: 'Land registry, property records, real estate transactions',
    sources: ['Land Registry', 'County Records', 'Zillow'],
    icon: Waves,
  },
  {
    id: 'court_and_legal',
    label: 'Court & Legal',
    description: 'Court records, legal proceedings, enforcement actions, patent disputes',
    sources: ['PACER', 'CourtListener', 'Patent Office'],
    icon: Gavel,
  },
  {
    id: 'satellite_and_earth_observation',
    label: 'Satellite & Earth Obs',
    description: 'Satellite imagery, earth observation data, geospatial intelligence',
    sources: ['Sentinel', 'Planet Labs', 'Maxar'],
    icon: Satellite,
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
      selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id],
    );
  };

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-terminal-border bg-terminal-sunken px-4 py-4">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-terminal-text-muted">
          Committed ingestion filters
        </div>
        <p className="mt-2 text-sm leading-6 text-terminal-text-secondary">
          These filters govern what evidence and signal classes are considered in scope for the investigation. They are part of the bounded inquiry receipt, not just UI filters.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {DOMAIN_CATEGORIES.map((category) => {
          const selectedState = selected.includes(category.id);
          const Icon = category.icon;

          return (
            <button
              key={category.id}
              type="button"
              onClick={() => toggle(category.id)}
              className={`rounded-2xl border px-4 py-4 text-left transition ${
                selectedState
                  ? 'border-purple-200 bg-purple-100/70'
                  : 'border-terminal-border bg-terminal-sunken hover:bg-terminal-hover'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                      selectedState
                        ? 'border-purple-200 bg-purple-500 text-white'
                        : 'border-terminal-border bg-terminal-panel text-terminal-text-muted'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-terminal-text">
                      {category.label}
                    </div>
                    <p className="mt-1 text-sm leading-6 text-terminal-text-secondary">
                      {category.description}
                    </p>
                  </div>
                </div>
                <div
                  className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full border ${
                    selectedState
                      ? 'border-purple-300 bg-purple-500 text-white'
                      : 'border-terminal-border bg-terminal-panel text-terminal-text-muted'
                  }`}
                >
                  {selectedState ? '✓' : ''}
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {category.sources.map((source) => (
                  <span
                    key={source}
                    className="rounded-full border border-terminal-border bg-terminal-elevated px-2.5 py-1 text-[11px] font-medium text-terminal-text-secondary"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>

      <div className="text-sm text-terminal-text-secondary">
        {selected.length} of {DOMAIN_CATEGORIES.length} categories selected
      </div>
    </div>
  );
}
