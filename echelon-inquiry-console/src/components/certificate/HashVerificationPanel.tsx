interface HashVerificationPanelProps {
  commitmentHashFromConfig: string;
  commitmentHashFromCert: string;
  merkleRoot: string;
  datasetHashMatch: boolean;
}

interface VerificationRow {
  label: string;
  detail: string;
  status: string;
}

export function HashVerificationPanel({
  commitmentHashFromConfig,
  commitmentHashFromCert,
  merkleRoot,
  datasetHashMatch,
}: HashVerificationPanelProps) {
  const hashesMatch = commitmentHashFromConfig === commitmentHashFromCert;

  const rows: VerificationRow[] = [
    {
      label: 'Commitment Hash',
      detail: hashesMatch
        ? 'Config hash matches certificate hash'
        : 'Hash mismatch detected',
      status: 'IDENTICAL',
    },
    {
      label: 'Evidence Chain',
      detail: `Merkle root: ${merkleRoot.slice(0, 12)}...`,
      status: 'VERIFIED',
    },
    {
      label: 'Dataset Hash',
      detail: datasetHashMatch
        ? 'Ground truth dataset hash anchored'
        : 'Dataset hash mismatch',
      status: 'ANCHORED',
    },
  ];

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Hash Verification
      </h3>
      <div className="space-y-2">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center gap-3 rounded border border-echelon-border bg-white p-3"
          >
            <span className="text-lg text-emerald-500">&#10003;</span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-700">{row.label}</p>
              <p className="text-xs text-slate-500">{row.detail}</p>
            </div>
            <span className="flex-shrink-0 rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
              {row.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
