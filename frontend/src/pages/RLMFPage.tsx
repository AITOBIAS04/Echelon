import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Boxes,
  CheckCircle2,
  Database,
  FileCode2,
  FlaskConical,
  PackageSearch,
  ShieldCheck,
} from 'lucide-react';

type PackageState = 'available' | 'staged';

interface PackageDefinition {
  id: string;
  name: string;
  kind: string;
  summary: string;
  state: PackageState;
  integrity: string;
  cadence: string;
  delivery: string;
  verification: string;
  fields?: Array<{ name: string; type: string; description: string }>;
}

const PACKAGE_DEFINITIONS: PackageDefinition[] = [
  {
    id: 'rlmf-training',
    name: 'RLMF Training Export',
    kind: 'training',
    summary:
      'Settled theatre training artefact generated from market epochs, agent traces, calibration, and evidence hashes.',
    state: 'available',
    integrity: 'Receipted at settlement',
    cadence: 'Produced per settled theatre',
    delivery: 'Generator service present; package route pending',
    verification: 'Linked to theatre resolution outputs',
    fields: [
      { name: 'schema_version', type: 'string', description: 'RLMF export schema version.' },
      { name: 'oracle_output_id', type: 'string', description: 'Resolution oracle output identifier.' },
      { name: 'theatre_id', type: 'string', description: 'Source theatre for the export.' },
      { name: 'question', type: 'string', description: 'Resolved theatre question.' },
      { name: 'outcome_labels', type: 'array', description: 'Outcome labels available in the market.' },
      { name: 'winning_outcome_label', type: 'string', description: 'Resolved winning outcome label.' },
      { name: 'epochs', type: 'array', description: 'Per-tick market state sequence.' },
      { name: 'agent_traces', type: 'array', description: 'Serialized agent decision traces.' },
      { name: 'calibration', type: 'object', description: 'Brier/ECE calibration metrics.' },
      { name: 'agent_pnl', type: 'object', description: 'Per-agent realized P&L snapshot.' },
      { name: 'evidence_bundle_hash', type: 'string', description: 'Evidence bundle integrity hash.' },
      { name: 'settlement_hash', type: 'string', description: 'Settlement integrity hash.' },
    ],
  },
  {
    id: 'sponsor-delivery',
    name: 'Sponsor Delivery Package',
    kind: 'delivery',
    summary:
      'Final sponsor bundle that assembles calibration certificate, evidence bundle, RLMF export, and commitment hash.',
    state: 'available',
    integrity: 'Certificate and evidence hash bound',
    cadence: 'Produced at sponsor delivery',
    delivery: 'Assembler service present; delivery route pending',
    verification: 'Auditable through certificate + evidence bundle',
    fields: [
      { name: 'theatre_id', type: 'string', description: 'Resolved theatre identifier.' },
      { name: 'certificate', type: 'object', description: 'Serialized calibration certificate payload.' },
      { name: 'evidence_bundle', type: 'object', description: 'Evidence artefact with receipts and coverage.' },
      { name: 'rlmf_export', type: 'object', description: 'Serialized RLMF export bundle.' },
      { name: 'commitment_hash', type: 'string', description: 'Commitment receipt hash for the sponsor bundle.' },
      { name: 'echelon_status_url', type: 'string', description: 'Status/deep-link URL for the sponsor package.' },
    ],
  },
  {
    id: 'calibration-dataset',
    name: 'Calibration Dataset',
    kind: 'calibration',
    summary:
      'Cross-theatre calibration export for probability quality analysis once package APIs are introduced.',
    state: 'staged',
    integrity: 'Will require certificate-linked label coverage',
    cadence: 'Not yet routable',
    delivery: 'Contract defined, routes pending',
    verification: 'Reference-only until export package API exists',
  },
  {
    id: 'evaluation-holdout',
    name: 'Evaluation Holdout Set',
    kind: 'evaluation',
    summary:
      'Holdout package for offline evaluation and benchmark runs. Design reference exists, delivery route does not.',
    state: 'staged',
    integrity: 'Will depend on receipted outcome labels',
    cadence: 'Not yet routable',
    delivery: 'Contract defined, routes pending',
    verification: 'Reference-only until export package API exists',
  },
  {
    id: 'outcome-ledger',
    name: 'Outcome Ledger',
    kind: 'outcome',
    summary:
      'Historical resolution package for downstream reporting and sponsor reconciliation workflows.',
    state: 'staged',
    integrity: 'Will require settlement and certificate lineage',
    cadence: 'Not yet routable',
    delivery: 'Contract defined, routes pending',
    verification: 'Reference-only until export package API exists',
  },
  {
    id: 'telemetry-bundle',
    name: 'Telemetry Bundle',
    kind: 'telemetry',
    summary:
      'Agent behavior and decision-log package intended for audit and operational replay analysis.',
    state: 'staged',
    integrity: 'Will require route and schema confirmation',
    cadence: 'Not yet routable',
    delivery: 'Contract defined, routes pending',
    verification: 'Reference-only until export package API exists',
  },
];

const stateStyles: Record<PackageState, string> = {
  available:
    'border-status-success/15 bg-status-success/[0.05] text-status-success',
  staged:
    'border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-muted)]',
};

const kindStyles: Record<string, string> = {
  training: 'bg-purple-100 text-purple-700 border border-purple-200',
  delivery: 'bg-green-100 text-green-700 border border-green-200',
  calibration: 'bg-status-info/10 text-status-info border border-status-info/20',
  evaluation: 'bg-orange-100 text-orange-700 border border-orange-200',
  outcome: 'bg-[var(--e-bg-sunken)] text-[var(--e-text-secondary)] border border-[var(--e-border-secondary)]',
  telemetry: 'bg-[var(--e-bg-sunken)] text-[var(--e-text-secondary)] border border-[var(--e-border-secondary)]',
};

function PackageCard({ pkg }: { pkg: PackageDefinition }) {
  const actionDisabled = pkg.state !== 'available';

  return (
    <article className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]">
      <div className="flex flex-col gap-4 border-b border-[var(--e-border-secondary)] px-5 py-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] ${kindStyles[pkg.kind] ?? kindStyles.outcome}`}
            >
              {pkg.kind}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] ${stateStyles[pkg.state]}`}
            >
              {pkg.state === 'available' ? 'Backend service ready' : 'Route pending'}
            </span>
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-[var(--e-text-primary)]">
              {pkg.name}
            </h2>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-[var(--e-text-secondary)]">
              {pkg.summary}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={actionDisabled}
            className={`inline-flex items-center rounded-lg px-3 py-2 text-sm font-semibold transition ${
              actionDisabled
                ? 'cursor-not-allowed border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] text-[var(--e-text-disabled)]'
                : 'border border-purple-200 bg-purple-500 text-white hover:bg-purple-400'
            }`}
          >
            {actionDisabled ? 'API Pending' : 'Package Route Pending'}
          </button>
        </div>
      </div>

      <div className="grid gap-4 px-5 py-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metadata label="Integrity" value={pkg.integrity} />
        <Metadata label="Cadence" value={pkg.cadence} />
        <Metadata label="Delivery" value={pkg.delivery} />
        <Metadata label="Verification" value={pkg.verification} />
      </div>

      <div className="flex flex-wrap items-center gap-3 border-t border-[var(--e-border-secondary)] px-5 py-3">
        <button
          type="button"
          disabled={!pkg.fields}
          className={`text-sm font-semibold ${
            pkg.fields
              ? 'text-purple-700 hover:text-purple-500'
              : 'cursor-not-allowed text-[var(--e-text-disabled)]'
          }`}
          onClick={() => {
            const section = document.getElementById(`schema-${pkg.id}`);
            section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        >
          Schema preview
        </button>
        {pkg.state === 'available' && (
          <span className="text-xs text-[var(--e-text-muted)]">
            Service exists in backend, but no package delivery endpoint is live yet.
          </span>
        )}
      </div>
    </article>
  );
}

function Metadata({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className="text-sm text-[var(--e-text-primary)]">{value}</div>
    </div>
  );
}

function SchemaPanel({ pkg }: { pkg: PackageDefinition }) {
  if (!pkg.fields) {
    return null;
  }

  return (
    <section
      id={`schema-${pkg.id}`}
      className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)]"
    >
      <div className="flex items-center justify-between border-b border-[var(--e-border-secondary)] px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-[var(--e-text-primary)]">
            {pkg.name} schema
          </h3>
          <p className="mt-1 text-sm text-[var(--e-text-secondary)]">
            Derived from the current backend service contract.
          </p>
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
          {pkg.fields.length} fields
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--e-border-secondary)] text-sm">
          <thead className="bg-[var(--e-bg-sunken)]">
            <tr>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                Field
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                Type
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                Description
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--e-border-secondary)]">
            {pkg.fields.map((field) => (
              <tr key={field.name}>
                <td className="px-5 py-3 font-mono text-xs text-purple-700">
                  {field.name}
                </td>
                <td className="px-5 py-3 font-mono text-xs text-[var(--e-text-secondary)]">
                  {field.type}
                </td>
                <td className="px-5 py-3 text-sm text-[var(--e-text-secondary)]">
                  {field.description}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function RLMFPage() {
  const availablePackages = PACKAGE_DEFINITIONS.filter((pkg) => pkg.state === 'available').length;
  const stagedPackages = PACKAGE_DEFINITIONS.length - availablePackages;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
      <section className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 py-6 shadow-[var(--e-shadow-xs)]">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-purple-700">
              <Database className="h-3.5 w-3.5" />
              RLMF Exports
            </div>
            <p className="max-w-2xl text-sm leading-6 text-[var(--e-text-secondary)]">
              Echelon can already generate RLMF training exports and sponsor delivery bundles in the backend. This page exposes that delivery model honestly while the dedicated export package routes are still pending.
            </p>
          </div>

          <div className="grid min-w-[280px] gap-3 sm:grid-cols-2 xl:grid-cols-2">
            <StatCard label="Live services" value="2" detail="RLMF generator + sponsor bundle assembler" />
            <StatCard label="Package API" value="Pending" detail="No /exports package routes live yet" />
            <StatCard label="Schema" value="2.0.1" detail="Current RLMF export version" />
            <StatCard label="Catalog split" value={`${availablePackages}/${stagedPackages}`} detail="Available vs staged package families" />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-orange-200 bg-orange-50 px-5 py-4 text-sm text-orange-700 shadow-sm">
        <div className="flex items-start gap-3">
          <PackageSearch className="mt-0.5 h-5 w-5 flex-shrink-0" />
          <div>
            <div className="font-semibold">Delivery API still pending</div>
            <p className="mt-1 leading-6">
              This surface reflects real backend services, but generation and download remain staged until the export package routes land. No buttons on this page simulate missing delivery endpoints.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-5">
          <section className="space-y-4">
            {PACKAGE_DEFINITIONS.map((pkg) => (
              <PackageCard key={pkg.id} pkg={pkg} />
            ))}
          </section>

          {PACKAGE_DEFINITIONS.filter((pkg) => pkg.fields).map((pkg) => (
            <SchemaPanel key={pkg.id} pkg={pkg} />
          ))}
        </div>

        <aside className="space-y-5">
          <div className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-5 shadow-[var(--e-shadow-xs)]">
            <div className="flex items-center gap-2">
              <Boxes className="h-4 w-4 text-purple-600" />
              <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--e-text-primary)]">
                Delivery chain
              </h2>
            </div>
            <div className="mt-4 space-y-3">
              <ChainStep
                icon={<CheckCircle2 className="h-4 w-4 text-green-600" />}
                title="Theatre settlement"
                body="Resolution finalizes the theatre and produces the evidence + settlement hashes that anchor exports."
              />
              <ChainStep
                icon={<ShieldCheck className="h-4 w-4 text-purple-600" />}
                title="Certificate pipeline"
                body="Calibration certificate and evidence bundle are serialized before sponsor delivery is assembled."
              />
              <ChainStep
                icon={<FileCode2 className="h-4 w-4 text-purple-600" />}
                title="RLMF export"
                body="Market epochs, agent traces, calibration, and P&L are emitted into schema v2.0.1."
              />
              <ChainStep
                icon={<ArrowRight className="h-4 w-4 text-[var(--e-text-muted)]" />}
                title="Package routes"
                body="Download and generation APIs are the missing layer. Until then, the bundle stays a backend capability, not a live delivery console."
              />
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-5 shadow-[var(--e-shadow-xs)]">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-purple-600" />
              <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--e-text-primary)]">
                Operator actions
              </h2>
            </div>
            <div className="mt-4 space-y-3 text-sm text-[var(--e-text-secondary)]">
              <p>
                Use the existing operational surfaces to reach the generation point, then return here once delivery APIs land.
              </p>
              <div className="flex flex-col gap-2">
                <Link
                  to="/theatres"
                  className="inline-flex items-center justify-between rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-sm font-medium text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
                >
                  Review theatres
                  <ArrowRight className="h-4 w-4 text-[var(--e-text-muted)]" />
                </Link>
                <Link
                  to="/certificates"
                  className="inline-flex items-center justify-between rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-sm font-medium text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
                >
                  Review certificates
                  <ArrowRight className="h-4 w-4 text-[var(--e-text-muted)]" />
                </Link>
                <Link
                  to="/verify"
                  className="inline-flex items-center justify-between rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3 text-sm font-medium text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
                >
                  Open verify
                  <ArrowRight className="h-4 w-4 text-[var(--e-text-muted)]" />
                </Link>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-5 py-5 shadow-[var(--e-shadow-xs)]">
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--e-text-primary)]">
              Backend truth
            </h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                  Live service
                </dt>
                <dd className="mt-1 text-[var(--e-text-primary)]">`backend/services/rlmf_export.py`</dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                  Sponsor bundle
                </dt>
                <dd className="mt-1 text-[var(--e-text-primary)]">`backend/services/sponsor_delivery.py`</dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
                  Missing route layer
                </dt>
                <dd className="mt-1 text-[var(--e-text-secondary)]">
                  No live export package endpoints yet for list / generate / download.
                </dd>
              </div>
            </dl>
          </div>
        </aside>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-elevated)] px-4 py-4 shadow-[var(--e-shadow-xs)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--e-text-muted)]">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-[var(--e-text-primary)]">
        {value}
      </div>
      <div className="mt-1 text-sm text-[var(--e-text-secondary)]">{detail}</div>
    </div>
  );
}

function ChainStep({
  icon,
  title,
  body,
}: {
  icon: ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-3">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{icon}</div>
        <div>
          <div className="text-sm font-semibold text-[var(--e-text-primary)]">{title}</div>
          <div className="mt-1 text-sm leading-6 text-[var(--e-text-secondary)]">{body}</div>
        </div>
      </div>
    </div>
  );
}
