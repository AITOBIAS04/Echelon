import { Link } from 'react-router-dom';
import { ShieldCheck, Search, Zap, Activity, Globe, Share2, FileText, Download, Check } from 'lucide-react';

/* ═══════════════════════ ROW 1: HERO SUMMARY ═══════════════════════ */
function ResultHero() {
  return (
    <section
      className="relative overflow-hidden"
      style={{ background: 'oklch(0.110 0.010 265)', borderBottom: '1px solid var(--border-secondary)' }}
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(oklch(0.300 0.010 265 / 0.25) 1px, transparent 1px), linear-gradient(90deg, oklch(0.300 0.010 265 / 0.25) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse 70% 50% at 50% 50%, black 10%, transparent 65%)',
          WebkitMaskImage: 'radial-gradient(ellipse 70% 50% at 50% 50%, black 10%, transparent 65%)',
        }}
      />
      <div className="p-container relative" style={{ zIndex: 2, padding: 'var(--space-12) var(--space-6) var(--space-10)' }}>
        <div className="flex justify-between items-start gap-8 flex-wrap">
          <div style={{ flex: 1, minWidth: 280 }}>
            <div className="flex items-center gap-3 flex-wrap mb-3">
              <span className="p-chip p-chip-purple">INVESTIGATION</span>
              <span className="p-badge p-badge-verified"><span className="p-pulse-dot" style={{ width: 6, height: 6 }} /> Verified</span>
              <span className="p-badge p-badge-tier">TIER 2 — BACKTESTED</span>
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 'var(--space-2)' }}>
              APAC Supply Chain Disruption
            </h1>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', maxWidth: 540 }}>
              Agent readiness check for semiconductor routing disruption forecasting over a 14-day window using OSINT and market signals.
            </p>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
              Stop condition: Evidence Threshold — <strong style={{ color: 'var(--green-400)' }}>MET</strong>
            </p>
          </div>
          <div className="flex flex-col items-end gap-3" style={{ flexShrink: 0 }}>
            <div style={{ textAlign: 'right' }}>
              <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 'var(--space-1)' }}>Certificate</div>
              <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--green-400)' }}>CERT-00291</div>
            </div>
            <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right' }}>Updated 2026-03-08 00:00 UTC</div>
            <div className="flex gap-3" style={{ marginTop: 'var(--space-2)' }}>
              <Link to="/verify-public" className="p-btn p-btn-primary p-btn-sm">Verify Certificate</Link>
              <a href="#evidence-trail" className="p-btn p-btn-secondary p-btn-sm">View Evidence Trail</a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 2: PROOF CARDS ═══════════════════════ */
function ProofCards() {
  const cards = [
    { icon: <Zap size={20} />, color: 'purple', label: 'What was tested', title: 'LogiSense v3.1 — Bounded Inquiry', body: 'Supply-chain routing agent tested across APAC semiconductor corridors. 14-day forecast window with 18 evidence items and 6 claim nodes.', meta: 'INQ-2026-0847 · Theatre: APAC-SC' },
    { icon: <Search size={20} />, color: 'teal', label: 'What evidence was used', title: '18 OSINT sources corroborated', body: 'Public shipping data, port authority filings, satellite imagery, and news wire feeds across 4 jurisdictions. 3 counter-signal checks passed.', meta: 'Provenance: PUBLIC_PRIMARY · Freshness: 2h' },
    { icon: <ShieldCheck size={20} />, color: 'green', label: 'What was issued', title: 'CERT-00291 — Composite 87.4', body: 'Accuracy 91%, robustness 84%, calibration Brier 0.92, confidence overlap 88%. Batch-anchored at 00:00 UTC 2026-03-08.', meta: 'Hash: sha256:7a3f9b2c...e4d1f08a' },
    { icon: <Activity size={20} />, color: 'amber', label: 'What changed', title: 'Deployment allowed — Tier 2', body: 'Agent promoted from UNVERIFIED to BACKTESTED. Eligible for managed supply-chain monitoring feed consumption.', meta: 'Routing: ALLOWED · Policy: PROMOTE' },
  ];

  return (
    <section className="p-section" style={{ paddingTop: 0 }}>
      <div className="p-container">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map((c) => (
            <div key={c.label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <div className="flex items-center gap-3">
                <div className={`p-proof-icon p-proof-icon-${c.color}`}>{c.icon}</div>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{c.label}</div>
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{c.title}</div>
              <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>{c.body}</div>
              <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 'auto' }}>{c.meta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 3: EVIDENCE + CERTIFICATE ═══════════════════════ */
function EvidenceCertSplit() {
  const events = [
    { dot: 'var(--text-muted)', title: 'Signal detected — APAC shipping anomaly', desc: 'WorldMonitor flagged unusual container routing patterns across three APAC ports. Severity: Moderate. Domain: Logistics.', time: '2026-02-16 08:42 UTC · SIG-4821' },
    { dot: 'var(--purple-500)', title: 'Inquiry opened — Bounded supply-chain inquiry', desc: 'Investigation INQ-2026-0847 created with Evidence Threshold stop condition. LogiSense v3.1 assigned as primary agent.', time: '2026-02-18 10:15 UTC · INQ-2026-0847' },
    { dot: 'var(--purple-500)', title: 'Investigation linked — Evidence collection active', desc: '18 public primary evidence items collected. Port authority filings, satellite imagery, and shipping manifests from Taiwan, South Korea, Japan, and Singapore.', time: '2026-02-18 – 2026-03-07 · E001–E018' },
    { dot: 'var(--purple-500)', title: 'Counter-signal checks — 3 contradiction scans passed', desc: 'Automated contradiction monitoring found no disconfirming evidence across cross-referenced sources. Corroboration rate: 94%.', time: '2026-03-05 16:30 UTC · CS-041, CS-042, CS-043' },
    { dot: 'var(--green-500)', title: 'Outcome resolved — Evidence threshold met', desc: 'Stop condition satisfied: 18/15 primary items collected, 6/5 claims SUPPORTED. Readiness status changed to READY.', time: '2026-03-07 14:32 UTC' },
    { dot: 'var(--green-500)', title: 'Certificate issued — CERT-00291', desc: 'Certificate built, batch-anchored, and issued. Composite score 87.4. Routing decision: ALLOWED. Trust tier assigned: BACKTESTED (Tier 2).', time: '2026-03-08 00:00 UTC · CERT-00291' },
  ];

  const scores = [
    { label: 'Accuracy', value: '91%', color: 'var(--green-400)', width: 91, barColor: 'green' },
    { label: 'Robustness', value: '84%', color: 'var(--purple-400)', width: 84, barColor: 'purple' },
    { label: 'Calibration (Brier)', value: '0.92', color: 'var(--teal-400)', width: 92, barColor: 'teal' },
    { label: 'Confidence Overlap', value: '88%', color: 'var(--green-400)', width: 88, barColor: 'green' },
  ];

  return (
    <section className="p-section" id="evidence-trail">
      <div className="p-container">
        <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-6">
          {/* Evidence timeline */}
          <div>
            <p className="eyebrow mb-4">Evidence trail</p>
            <div className="relative" style={{ paddingLeft: 'var(--space-8)' }}>
              <div className="absolute" style={{ left: 11, top: 0, bottom: 0, width: 2, background: 'var(--border-primary)' }} />
              {events.map((e, i) => (
                <div key={i} className="relative" style={{ paddingBottom: i < events.length - 1 ? 'var(--space-6)' : 0 }}>
                  <div className="absolute" style={{ left: 'calc(-1 * var(--space-8) + 4px)', top: 4, width: 16, height: 16, borderRadius: '50%', background: e.dot, border: `2px solid ${e.dot}` }} />
                  <div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 'var(--space-1)' }}>{e.title}</h4>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{e.desc}</p>
                    <div className="mono mt-2" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{e.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Certificate panel */}
          <div id="certificate">
            <p className="eyebrow mb-4">Certificate</p>
            <div style={{ background: 'var(--bg-card)', border: '1px solid oklch(0.300 0.050 152)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              <div className="flex items-center justify-between" style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--border-secondary)' }}>
                <span className="mono" style={{ fontWeight: 600, fontSize: '0.85rem' }}>CERT-00291</span>
                <span className="p-badge p-badge-verified" style={{ fontSize: '0.7rem' }}><span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> Issued</span>
              </div>
              <div style={{ padding: 'var(--space-5)' }}>
                <div className="text-center mb-5">
                  <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--green-400)', letterSpacing: '-0.02em' }}>87.4</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 500 }}>Composite Score</div>
                </div>

                {scores.map((s) => (
                  <div key={s.label}>
                    <div className="flex items-center justify-between mb-3" style={{ fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{s.label}</span>
                      <span className="mono" style={{ fontWeight: 600, fontSize: '0.82rem', color: s.color }}>{s.value}</span>
                    </div>
                    <div className="p-score-bar-track mb-4"><div className={`p-score-bar-fill ${s.barColor}`} style={{ width: `${s.width}%` }} /></div>
                  </div>
                ))}

                <div style={{ borderTop: '1px solid var(--border-secondary)', paddingTop: 'var(--space-4)', marginTop: 'var(--space-2)' }}>
                  <div className="flex items-center justify-between mb-2" style={{ fontSize: '0.82rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Trust Tier</span>
                    <span className="p-badge p-badge-tier" style={{ fontSize: '0.65rem' }}>TIER 2 — BACKTESTED</span>
                  </div>
                  <div className="flex items-center justify-between mb-2" style={{ fontSize: '0.82rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Status</span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--green-400)' }}>ISSUED</span>
                  </div>
                  <div className="flex items-center justify-between" style={{ fontSize: '0.82rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Issued</span>
                    <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>2026-03-08</span>
                  </div>
                </div>

                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', wordBreak: 'break-all', padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-sunken)', borderRadius: 'var(--radius-sm)', marginTop: 'var(--space-4)', border: '1px solid var(--border-secondary)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>SHA-256 Hash</div>
                  sha256:7a3f9b2c4e8d1f3a6b9c2d5e8f1a3b6c9d2e5f8a1b4c7d0e3f6a9b2c5d8e1f08a
                </div>

                <div className="flex gap-3 mt-5">
                  <Link to="/verify-public" className="p-btn p-btn-primary p-btn-sm" style={{ flex: 1, justifyContent: 'center' }}>
                    <ShieldCheck size={14} /> Verify
                  </Link>
                  <button className="p-btn p-btn-secondary p-btn-sm" style={{ flex: 1, justifyContent: 'center' }}>
                    <Download size={14} /> Download
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 4: SUPPORTING SURFACES ═══════════════════════ */
function SupportingPreviews() {
  const cards = [
    { icon: <Share2 size={16} />, title: 'Signal Map', body: '12 signal nodes linked to this inquiry. 3 clusters identified. No active contradictions in the graph.', link: 'View full signal map →' },
    { icon: <Globe size={16} />, title: 'World Monitor', body: 'APAC region showing moderate activity. 3 events monitoring, 1 event escalating (Taiwan Strait corridor).', link: 'View world monitor →' },
    { icon: <FileText size={16} />, title: 'Investigation', body: '6 claims — 6 SUPPORTED, 0 CONTRADICTED. Source classes: PUBLIC_PRIMARY (18), ANALYST_DERIVED (3). Stop condition: Evidence Threshold — MET.', link: 'View investigation detail →' },
  ];

  return (
    <section className="p-section">
      <div className="p-container">
        <p className="eyebrow mb-6">Supporting intelligence</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {cards.map((c) => (
            <div key={c.title} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', minHeight: 180, display: 'flex', flexDirection: 'column' }}>
              <div className="flex items-center gap-2 mb-3">
                <span style={{ color: 'var(--purple-400)' }}>{c.icon}</span>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>{c.title}</span>
              </div>
              <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5, flex: 1 }}>{c.body}</div>
              <div style={{ marginTop: 'var(--space-4)', fontSize: '0.78rem' }}>
                <a href="#" className="p-btn p-btn-ghost p-btn-sm" style={{ paddingLeft: 0 }}>{c.link}</a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 5: ROUTING CONSEQUENCE ═══════════════════════ */
function RoutingConsequence() {
  const panels = [
    { icon: <Check size={22} />, color: 'green', title: 'Allowed', titleColor: 'var(--green-400)', desc: 'Agent cleared for production use in managed supply-chain monitoring.', meta: 'Deployment' },
    { icon: <ShieldCheck size={22} />, color: 'purple', title: 'Tier 2', titleColor: undefined, desc: 'Promoted from UNVERIFIED to BACKTESTED. Next tier requires 50+ episodes across domains.', meta: 'Trust Tier' },
    { icon: <Activity size={22} />, color: 'teal', title: 'Feed Access', titleColor: undefined, desc: 'Managed feed consumption enabled for supply-chain intelligence workflows.', meta: 'Downstream' },
    { icon: <Download size={22} />, color: 'amber', title: 'Auto-promote', titleColor: undefined, desc: 'Governance checks passed. No coherence gate hold. Certificate batch-anchored without review.', meta: 'Policy' },
  ];

  return (
    <section className="p-section">
      <div className="p-container">
        <p className="eyebrow mb-4">Routing consequence</p>
        <h3 style={{ marginBottom: 'var(--space-6)' }}>What happened because of this verification</h3>
        <div
          className="grid grid-cols-1 md:grid-cols-4"
          style={{ border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', background: 'var(--bg-card)' }}
        >
          {panels.map((p, i) => (
            <div key={p.meta} className="relative flex flex-col gap-3" style={{ padding: 'var(--space-6)', borderRight: i < 3 ? '1px solid var(--border-secondary)' : undefined }}>
              <div className={`p-proof-icon p-proof-icon-${p.color}`} style={{ width: 44, height: 44 }}>{p.icon}</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '-0.01em', color: p.titleColor }}>{p.title}</div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{p.desc}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: 'auto' }}>{p.meta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 6: RLMF EXPORTS ═══════════════════════ */
function ExportCards() {
  const exports = [
    { name: 'APAC SC Replay Package', type: 'Replay', chipClass: 'p-chip-purple', verified: true, freshness: '2h ago', cert: 'CERT-00291' },
    { name: 'Calibration Dataset — Logistics', type: 'Calibration', chipClass: 'p-chip-teal', verified: true, freshness: '2h ago', cert: 'CERT-00291' },
    { name: 'Evaluation Holdout Set', type: 'Evaluation', chipClass: 'p-chip-green', verified: true, freshness: '2h ago', cert: 'CERT-00291' },
    { name: 'Labelled Training Export', type: 'Training', chipClass: 'p-chip-purple', verified: false, freshness: '6h ago', cert: 'CERT-00291' },
    { name: 'Agent Telemetry Bundle', type: 'Telemetry', chipClass: 'p-chip-teal', verified: true, freshness: '2h ago', cert: 'CERT-00291' },
  ];

  return (
    <section className="p-section" id="rlmf-exports">
      <div className="p-container">
        <p className="eyebrow mb-2">RLMF exports</p>
        <h3 style={{ marginBottom: 'var(--space-6)' }}>Data products from this verification</h3>
        <div style={{ overflowX: 'auto', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', background: 'var(--bg-card)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr>
                {['Export', 'Type', 'Verification', 'Freshness', 'Certificate', ''].map((h, i) => (
                  <th key={h || i} style={{ textAlign: i === 5 ? 'right' : 'left', padding: 'var(--space-3) var(--space-4)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-primary)', background: 'var(--bg-sunken)', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {exports.map((e) => (
                <tr key={e.name}>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)', fontWeight: 500 }}>{e.name}</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)' }}><span className={`p-chip ${e.chipClass}`}>{e.type}</span></td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)' }}>
                    {e.verified ? <span className="p-badge p-badge-verified" style={{ fontSize: '0.65rem' }}>Verified</span> : <span className="p-badge p-badge-monitoring" style={{ fontSize: '0.65rem' }}>Partial</span>}
                  </td>
                  <td className="mono" style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{e.freshness}</td>
                  <td className="mono" style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)', fontSize: '0.78rem' }}>{e.cert}</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)', textAlign: 'right' }}>
                    <button className="p-btn p-btn-ghost p-btn-sm">Download</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ ROW 7: RELATED RESULTS ═══════════════════════ */
function RelatedResults() {
  const related = [
    { title: 'EU Carbon Credit Pricing', agent: 'CarbonEdge v2.0 · Composite 91.2', status: 'verified', tier: 'TIER 3', cert: 'CERT-00288 · INQ-2026-0831' },
    { title: 'Brazil Soy Export Forecast', agent: 'AgroSight v1.4 · Composite 78.6', status: 'monitoring', tier: 'TIER 1', cert: 'INQ-2026-0819' },
    { title: 'Middle East Shipping Lane Risk', agent: 'GeoRisk v2.7 · Composite 81.3', status: 'escalated', tier: 'TIER 2', cert: 'INV-0794 · INQ-2026-0794' },
  ];

  return (
    <section className="p-section">
      <div className="p-container">
        <p className="eyebrow mb-2">Related results</p>
        <h3 style={{ marginBottom: 'var(--space-6)' }}>Adjacent verifications</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {related.map((r) => (
            <Link key={r.title} to="/results" className="no-underline" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', transition: 'all var(--duration-fast) var(--ease-out)' }}>
              <div className="flex items-center justify-between">
                {r.status === 'verified' && <span className="p-badge p-badge-verified" style={{ fontSize: '0.65rem' }}><span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> Verified</span>}
                {r.status === 'monitoring' && <span className="p-badge p-badge-monitoring" style={{ fontSize: '0.65rem' }}>Monitoring</span>}
                {r.status === 'escalated' && <span className="p-badge p-badge-warning" style={{ fontSize: '0.65rem' }}>Escalated</span>}
                <span className="p-badge p-badge-tier" style={{ fontSize: '0.6rem' }}>{r.tier}</span>
              </div>
              <h4 style={{ fontSize: '0.95rem', marginTop: 'var(--space-2)' }}>{r.title}</h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{r.agent}</p>
              <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 'auto', paddingTop: 'var(--space-2)' }}>{r.cert}</div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ PAGE ═══════════════════════ */
export default function PublicResultsPage() {
  return (
    <>
      <ResultHero />
      <ProofCards />
      <EvidenceCertSplit />
      <SupportingPreviews />
      <RoutingConsequence />
      <ExportCards />
      <RelatedResults />
    </>
  );
}
