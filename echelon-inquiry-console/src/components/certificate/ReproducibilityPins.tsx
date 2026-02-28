import { truncateHash } from '../../utils/hash';

interface ReproducibilityPinsProps {
  constructVersion: string;
  scorerVersion: string;
  methodology: string;
  datasetHashes: Record<string, string>;
  evidenceBundleHash: string;
  commitmentHash: string;
}

export function ReproducibilityPins({
  constructVersion,
  scorerVersion,
  methodology,
  datasetHashes,
  evidenceBundleHash,
  commitmentHash,
}: ReproducibilityPinsProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
          Version Pins
        </h3>
        <div className="rounded-md bg-echelon-data-bg p-4 font-mono text-sm text-echelon-data-text">
          <div>construct: {constructVersion}</div>
          <div>scorer: {scorerVersion}</div>
          <div>methodology: {methodology}</div>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
          Cryptographic Chain
        </h3>
        <div className="rounded-md bg-echelon-data-bg p-4 font-mono text-sm text-echelon-data-text">
          <div>commitment: {truncateHash(commitmentHash, 16)}...</div>
          <div>evidence_bundle: {truncateHash(evidenceBundleHash, 16)}...</div>
          {Object.entries(datasetHashes).map(([key, hash]) => (
            <div key={key}>
              dataset.{key}: {truncateHash(hash, 16)}...
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
