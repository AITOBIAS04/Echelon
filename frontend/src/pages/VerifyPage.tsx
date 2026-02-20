/**
 * Verification Dashboard
 *
 * Two tabbed views:
 *   1. My Runs — user's verification runs with status, progress, filters
 *   2. Certificates — public certificate browser with scores and sorting
 *
 * Tab state is shared with TopActionBar via VerifyUiContext.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { ShieldCheck } from 'lucide-react';
import { useVerifyUi } from '../contexts/VerifyUiContext';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import { useVerificationRuns } from '../hooks/useVerificationRuns';
import { useCertificates } from '../hooks/useCertificates';
import { RunsListView } from '../components/verify/RunsListView';
import { RunDetailDrawer } from '../components/verify/RunDetailDrawer';
import { CertificatesListView } from '../components/verify/CertificatesListView';
import { CertDetailDrawer } from '../components/verify/CertDetailDrawer';
import { StartVerificationModal } from '../components/verify/StartVerificationModal';
import type { VerificationRunStatus, CertFilters } from '../types/verification';

export function VerifyPage() {
  const { activeTab, setActiveTab } = useVerifyUi();

  // ── Runs state ───────────────────────────────────────────────────────
  const [runFilters, setRunFilters] = useState<{
    status?: VerificationRunStatus;
    construct_id?: string;
  }>({});
  const [runOffset, setRunOffset] = useState(0);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { runs, total: runsTotal, isLoading: runsLoading, error: runsError, createRun, isCreating } =
    useVerificationRuns({
      ...runFilters,
      limit: 20,
      offset: runOffset,
    });

  const selectedRun = selectedRunId ? runs.find((r) => r.run_id === selectedRunId) ?? null : null;

  // ── Certificates state ───────────────────────────────────────────────
  const [certSort, setCertSort] = useState<CertFilters['sort']>('brier_asc');
  const [certConstructFilter, setCertConstructFilter] = useState('');
  const [certOffset, setCertOffset] = useState(0);
  const [selectedCertId, setSelectedCertId] = useState<string | null>(null);

  const { certificates, total: certsTotal, isLoading: certsLoading, error: certsError } =
    useCertificates({
      sort: certSort,
      construct_id: certConstructFilter || undefined,
      limit: 20,
      offset: certOffset,
    });

  // ── Modal state ──────────────────────────────────────────────────────
  const [showModal, setShowModal] = useState(false);

  // ── Close drawers on tab switch ─────────────────────────────────────
  // TopActionBar sets activeTab via context directly, so we watch it here.
  // skipClearRef prevents the effect from clearing selections when
  // handleViewCertificate intentionally switches tab + sets a cert.
  const skipClearRef = useRef(false);
  useEffect(() => {
    if (skipClearRef.current) {
      skipClearRef.current = false;
      return;
    }
    setSelectedRunId(null);
    setSelectedCertId(null);
  }, [activeTab]);

  // ── Handlers ─────────────────────────────────────────────────────────

  // "View Certificate" from run drawer → switch to certificates tab and open cert
  const handleViewCertificate = useCallback(
    (certificateId: string) => {
      skipClearRef.current = true;
      setSelectedRunId(null);
      setActiveTab('certificates');
      setSelectedCertId(certificateId);
    },
    [setActiveTab],
  );

  const handleModalSubmit = useCallback(
    async (body: Parameters<typeof createRun>[0]) => {
      await createRun(body);
    },
    [createRun],
  );

  // Register TopActionBar actions
  useRegisterTopActionBarActions({
    startVerification: () => setShowModal(true),
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Section header */}
      <div className="flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-echelon-cyan" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          {activeTab === 'runs' ? 'Verification Runs' : 'Calibration Certificates'}
        </h2>
      </div>

      {/* Tab content */}
      {activeTab === 'runs' ? (
        <RunsListView
          runs={runs}
          total={runsTotal}
          isLoading={runsLoading}
          error={runsError}
          filters={runFilters}
          onFiltersChange={setRunFilters}
          offset={runOffset}
          onOffsetChange={setRunOffset}
          onSelectRun={setSelectedRunId}
        />
      ) : (
        <CertificatesListView
          certificates={certificates}
          total={certsTotal}
          isLoading={certsLoading}
          error={certsError}
          sort={certSort}
          onSortChange={setCertSort}
          constructFilter={certConstructFilter}
          onConstructFilterChange={(val) => {
            setCertConstructFilter(val);
            setCertOffset(0);
          }}
          offset={certOffset}
          onOffsetChange={setCertOffset}
          onSelectCert={setSelectedCertId}
        />
      )}

      {/* Run detail drawer */}
      <RunDetailDrawer
        run={selectedRun}
        onClose={() => setSelectedRunId(null)}
        onViewCertificate={handleViewCertificate}
      />

      {/* Certificate detail drawer */}
      <CertDetailDrawer
        certId={selectedCertId}
        onClose={() => setSelectedCertId(null)}
      />

      {/* Start verification modal */}
      <StartVerificationModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSubmit={handleModalSubmit}
        isSubmitting={isCreating}
      />
    </div>
  );
}

export default VerifyPage;
