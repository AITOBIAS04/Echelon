import { Link } from 'react-router-dom';
import { Globe, Zap, ShieldCheck, Activity, Search } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

/* ── Scroll-in observer ── */
function useScrollIn() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || !('IntersectionObserver' in window)) {
      el?.classList.add('visible');
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } }),
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

function ScrollIn({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useScrollIn();
  return <div ref={ref} className={`p-scroll-in ${className}`}>{children}</div>;
}

/* ═══════════════════════ HERO ═══════════════════════ */
function HeroSection() {
  return (
    <section
      className="relative overflow-hidden"
      style={{ background: 'var(--bg-sunken)', borderBottom: '1px solid var(--border-secondary)' }}
    >
      {/* Grid background */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(var(--border-secondary) 1px, transparent 1px), linear-gradient(90deg, var(--border-secondary) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse 60% 60% at 50% 40%, black 20%, transparent 70%)',
          WebkitMaskImage: 'radial-gradient(ellipse 60% 60% at 50% 40%, black 20%, transparent 70%)',
        }}
      />
      {/* Radial glow */}
      <div
        aria-hidden="true"
        className="absolute pointer-events-none"
        style={{
          top: '-30%', left: '50%', transform: 'translateX(-50%)',
          width: 700, height: 500,
          background: 'radial-gradient(ellipse, oklch(0.530 0.230 295 / 0.08) 0%, transparent 70%)',
        }}
      />

      <div className="p-container relative" style={{ zIndex: 2, padding: 'var(--space-10) var(--space-6) var(--space-16)' }}>
        <div className="text-center">
          <p className="eyebrow" style={{ marginBottom: 'var(--space-4)' }}>Verification infrastructure for AI agents</p>
          <h1 style={{ maxWidth: 700, margin: '0 auto var(--space-5)' }}>Verify agents against reality.</h1>
          <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto var(--space-8)', lineHeight: 1.6 }}>
            Bounded inquiries. Real evidence. Tamper-proof certificates.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap" style={{ marginBottom: 'var(--space-12)' }}>
            <Link to="/results" className="p-btn p-btn-primary">View Verified Results</Link>
            <Link to="/results#certificate" className="p-btn p-btn-secondary">See a Certificate</Link>
          </div>

          {/* Live inquiry panel */}
          <div
            style={{
              maxWidth: 680, margin: '0 auto',
              background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)', overflow: 'hidden',
              boxShadow: '0 0 60px -12px oklch(0.530 0.230 295 / 0.12)',
            }}
          >
            <div className="flex items-center justify-between flex-wrap gap-3" style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-secondary)', background: 'var(--bg-sunken)', fontSize: '0.78rem' }}>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="p-chip p-chip-purple">INVESTIGATION</span>
                <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>INQ-2026-0847</span>
              </div>
              <span className="p-badge p-badge-verified"><span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> Verified</span>
            </div>
            <div className="grid grid-cols-2 gap-4" style={{ padding: 'var(--space-5)' }}>
              <Cell label="Inquiry" value="APAC Supply Chain Disruption" />
              <Cell label="Agent" value="LogiSense v3.1" />
              <Cell label="Composite Score" value="87.4" valueStyle={{ fontFamily: 'var(--font-mono)', color: 'var(--green-400)', fontWeight: 700 }} />
              <Cell label="Trust Tier" value={<span className="p-badge p-badge-tier" style={{ fontSize: '0.65rem' }}>TIER 2 — BACKTESTED</span>} />
            </div>
            <div className="flex items-center justify-between flex-wrap gap-2" style={{ padding: 'var(--space-3) var(--space-4)', borderTop: '1px solid var(--border-secondary)', background: 'var(--bg-sunken)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span className="mono">CERT-00291 · sha256:7a3f9b2c…e4d1</span>
              <span>Routing: <strong style={{ color: 'var(--green-400)' }}>ALLOWED</strong></span>
            </div>
          </div>

          {/* Stat strip */}
          <div className="grid grid-cols-4 gap-4" style={{ marginTop: 'var(--space-10)' }}>
            <StatItem value="127" label="Live inquiries" />
            <StatItem value="84" label="Verified certificates" />
            <StatItem value="2,341" label="Evidence-linked outcomes" />
            <StatItem value={<>96.2<span style={{ fontSize: '0.65em', opacity: 0.7 }}>%</span></>} label="Routing-ready results" />
          </div>
        </div>
      </div>
    </section>
  );
}

function Cell({ label, value, valueStyle }: { label: string; value: React.ReactNode; valueStyle?: React.CSSProperties }) {
  return (
    <div className="flex flex-col gap-1">
      <span style={{ fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: '0.87rem', fontWeight: 500, ...valueStyle }}>{value}</span>
    </div>
  );
}

function StatItem({ value, label }: { value: React.ReactNode; label: string }) {
  return (
    <div className="text-center" style={{ padding: 'var(--space-4)', background: 'var(--bg-card)', border: '1px solid var(--border-secondary)', borderRadius: 'var(--radius)' }}>
      <div style={{ fontSize: '1.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--purple-400)', letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 'var(--space-1)', fontWeight: 500 }}>{label}</div>
    </div>
  );
}

/* ═══════════════════════ WHY ═══════════════════════ */
function WhySection() {
  return (
    <section className="p-section">
      <div className="p-container">
        <h2 style={{ textAlign: 'center', maxWidth: 600, margin: '0 auto var(--space-3)' }}>Most agents are deployed before they are proven.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 560, margin: '0 auto var(--space-10)', fontSize: '0.95rem' }}>
          Benchmarks show lab performance. Echelon shows what happens when agents face reality. We structure bounded inquiries, gather evidence, run live verification flows, and issue proof that downstream systems can actually use.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ScrollIn><div className="p-card"><div className="p-proof-icon p-proof-icon-teal mb-4"><Globe size={20} /></div><h3 style={{ fontSize: '1rem', marginBottom: 'var(--space-2)' }}>Detect and observe</h3><p style={{ fontSize: '0.87rem', color: 'var(--text-secondary)' }}>OSINT and market activity surface the signals worth investigating. Live evidence, not synthetic benchmarks.</p></div></ScrollIn>
          <ScrollIn><div className="p-card"><div className="p-proof-icon p-proof-icon-purple mb-4"><Zap size={20} /></div><h3 style={{ fontSize: '1rem', marginBottom: 'var(--space-2)' }}>Investigate under pressure</h3><p style={{ fontSize: '0.87rem', color: 'var(--text-secondary)' }}>Bounded inquiries and adversarial participation expose failure, drift, and robustness gaps before deployment.</p></div></ScrollIn>
          <ScrollIn><div className="p-card"><div className="p-proof-icon p-proof-icon-green mb-4"><ShieldCheck size={20} /></div><h3 style={{ fontSize: '1rem', marginBottom: 'var(--space-2)' }}>Certify and route</h3><p style={{ fontSize: '0.87rem', color: 'var(--text-secondary)' }}>Certificates, evidence trails, and trust tiers turn verification results into deployment decisions.</p></div></ScrollIn>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ HOW IT WORKS ═══════════════════════ */
function HowItWorksSection() {
  const nodes = [
    { icon: <Globe size={22} />, title: 'Detect', desc: 'Signal Scanner ingests live anomalies from OSINT feeds, market activity, and user-driven inquiry formation.', meta: 'Signal Scanner', color: 'teal' },
    { icon: <Zap size={22} />, title: 'Investigate', desc: 'Bounded inquiries structure evidence collection. Corroboration and counter-signal checks stress-test every claim.', meta: 'Bounded Inquiry', color: 'purple' },
    { icon: <ShieldCheck size={22} />, title: 'Certify', desc: 'Deterministic resolution scores outcomes. Certificates issued with evidence links and hash-anchored audit trails.', meta: 'Certificate Engine', color: 'green' },
    { icon: <Activity size={22} />, title: 'Route', desc: 'Certificates produce routing decisions: allowed, review required, or blocked. Trust tiers gate deployment eligibility.', meta: 'Routing Layer', color: 'amber' },
  ];

  return (
    <section className="p-section" id="how-it-works">
      <div className="p-container">
        <p className="eyebrow mb-2" style={{ textAlign: 'center' }}>How it works</p>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-3)' }}>A verification loop, not a static benchmark.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 520, margin: '0 auto var(--space-10)', fontSize: '0.95rem' }}>
          Four stages take a signal from detection through investigation to certified, routable outcomes.
        </p>
        <ScrollIn>
          <div
            className="grid grid-cols-1 md:grid-cols-4"
            style={{ border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', background: 'var(--bg-card)' }}
          >
            {nodes.map((n, i) => (
              <div key={n.title} className="relative flex flex-col gap-3" style={{ padding: 'var(--space-6)', borderRight: i < 3 ? '1px solid var(--border-secondary)' : undefined }}>
                <div className={`p-proof-icon p-proof-icon-${n.color}`} style={{ width: 44, height: 44, marginBottom: 'var(--space-1)' }}>{n.icon}</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '-0.01em' }}>{n.title}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{n.desc}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: 'auto' }}>{n.meta}</div>
              </div>
            ))}
          </div>
        </ScrollIn>
      </div>
    </section>
  );
}

/* ═══════════════════════ FEATURED PROOF ═══════════════════════ */
function FeaturedProofSection() {
  const steps = [
    { num: 1, phase: 'Detect', phaseColor: 'var(--teal-400)', numClass: 'teal', title: 'Bounded supply-chain inquiry opened', desc: 'Agent tasked with predicting APAC semiconductor routing disruptions over a 14-day window using OSINT and market signals.', aside: <><span className="p-chip p-chip-purple" style={{ marginBottom: 4 }}>INVESTIGATION</span><br />INQ-2026-0847</> },
    { num: 2, phase: 'Investigate', phaseColor: 'var(--purple-400)', numClass: 'purple', title: '18 primary sources corroborated', desc: 'Public shipping data, port authority filings, satellite imagery feeds, three counter-signal contradiction checks passed.', aside: <>6 claims<br />SUPPORTED</> },
    { num: 3, phase: 'Certify', phaseColor: 'var(--green-400)', numClass: 'green', title: 'CERT-00291 — Composite 87.4', desc: 'Accuracy 91%, robustness 84%, calibration 0.92 Brier, confidence interval overlap 88%. Hash-pinned and batch-anchored.', aside: <>Issued<br />2026-03-08</> },
    { num: 4, phase: 'Route', phaseColor: 'var(--amber-400)', numClass: 'amber', title: 'Deployment allowed — Tier 2', desc: 'Agent promoted from UNVERIFIED to BACKTESTED. Eligible for managed supply-chain monitoring feed consumption.', aside: <>Decision:<br /><strong style={{ color: 'var(--green-400)' }}>ALLOWED</strong></> },
  ];

  const numBg: Record<string, string> = {
    teal: 'oklch(0.200 0.035 185)',
    purple: 'oklch(0.200 0.040 295)',
    green: 'oklch(0.200 0.040 152)',
    amber: 'oklch(0.200 0.035 85)',
  };

  return (
    <section className="p-section">
      <div className="p-container">
        <p className="eyebrow mb-2" style={{ textAlign: 'center' }}>Featured proof</p>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-3)' }}>Follow one result from inquiry to consequence.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 520, margin: '0 auto var(--space-10)', fontSize: '0.95rem' }}>
          Understand the product by tracing a single verified outcome through every layer.
        </p>

        <div style={{ maxWidth: 760, margin: '0 auto' }}>
          {steps.map((s, i) => (
            <ScrollIn key={s.num}>
              <div
                className="grid items-start gap-4"
                style={{
                  gridTemplateColumns: '40px 1fr auto',
                  background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-lg)', padding: 'var(--space-5) var(--space-6)',
                  transition: 'border-color var(--duration-fast) var(--ease-out)',
                }}
              >
                <div className="flex items-center justify-center" style={{ width: 40, height: 40, borderRadius: '50%', background: numBg[s.numClass], color: s.phaseColor, fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                  {s.num}
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: s.phaseColor, marginBottom: 'var(--space-1)' }}>{s.phase}</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 'var(--space-2)' }}>{s.title}</div>
                  <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{s.desc}</div>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right', whiteSpace: 'nowrap', alignSelf: 'center' }}>{s.aside}</div>
              </div>
              {i < steps.length - 1 && (
                <div style={{ width: 2, height: 32, margin: '0 auto', background: 'linear-gradient(to bottom, var(--border-primary), var(--purple-500), var(--border-primary))' }} />
              )}
            </ScrollIn>
          ))}
        </div>

        <p style={{ textAlign: 'center', fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 'var(--space-8)', fontStyle: 'italic' }}>
          This is one verified result. Every inquiry produces the same chain: signal → investigation → evidence → certificate → routing decision.
        </p>
      </div>
    </section>
  );
}

/* ═══════════════════════ RESULTS PREVIEW ═══════════════════════ */
function ResultsPreviewSection() {
  const [activeTab, setActiveTab] = useState<'results' | 'evidence' | 'certificates' | 'exports'>('results');

  const results = [
    { title: 'APAC Supply Chain Disruption', id: 'INQ-2026-0847', type: 'INVESTIGATION', status: 'verified', agent: 'LogiSense v3.1', score: 87.4, tier: 'TIER 2 — BACKTESTED', cert: 'CERT-00291', date: '8 Mar 2026' },
    { title: 'EU Carbon Credit Pricing', id: 'INQ-2026-0831', type: 'INSPECTION', status: 'verified', agent: 'CarbonEdge v2.0', score: 91.2, tier: 'TIER 3 — PROVEN', cert: 'CERT-00288', date: '5 Mar 2026' },
    { title: 'Brazil Soy Export Forecast', id: 'INQ-2026-0819', type: 'SURVEY', status: 'monitoring', agent: 'AgroSight v1.4', score: 78.6, tier: 'TIER 1 — UNVERIFIED', cert: null, date: '' },
    { title: 'US Treasury Yield Curve Inversion', id: 'INQ-2026-0802', type: 'SCRUTINY', status: 'verified', agent: 'MacroScope v4.2', score: 92.8, tier: 'TIER 3 — PROVEN', cert: 'CERT-00285', date: '1 Mar 2026' },
    { title: 'Middle East Shipping Lane Risk', id: 'INQ-2026-0794', type: 'INVESTIGATION', status: 'escalated', agent: 'GeoRisk v2.7', score: 81.3, tier: 'TIER 2 — BACKTESTED', cert: 'INV-0794', date: '' },
  ];

  return (
    <section className="p-section" id="results-preview">
      <div className="p-container">
        <p className="eyebrow mb-2" style={{ textAlign: 'center' }}>Verification results</p>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-3)' }}>Results you can inspect.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 520, margin: '0 auto var(--space-8)', fontSize: '0.95rem' }}>
          Every result answers four questions: what was tested, what evidence was used, what certificate was issued, and what changed.
        </p>

        {/* Tab bar */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-1)',
          marginBottom: 'var(--space-6)',
          borderBottom: '1px solid var(--border-secondary)',
        }}>
          {(['results', 'evidence', 'certificates', 'exports'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: 'var(--space-3) var(--space-5)',
                fontSize: '0.88rem',
                fontWeight: activeTab === tab ? 600 : 400,
                color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-muted)',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid var(--purple-400)' : '2px solid transparent',
                cursor: 'pointer',
                transition: 'all var(--duration-fast) var(--ease-out)',
                marginBottom: -1,
                textTransform: 'capitalize',
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* ── Results tab (default) ── */}
        {activeTab === 'results' && (
          <>
            <div className="flex flex-col gap-3">
              {results.map((r) => (
                <div
                  key={r.id}
                  className="grid items-start gap-3"
                  style={{
                    gridTemplateColumns: '1fr auto',
                    background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
                    borderRadius: 'var(--radius-lg)', padding: 'var(--space-5) var(--space-6)',
                    transition: 'border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out)',
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div className="flex items-center gap-3 flex-wrap" style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                      {r.title}
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 400 }}>{r.id}</span>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span className={`p-chip ${r.type === 'SURVEY' ? 'p-chip-grey' : 'p-chip-purple'}`} style={{ fontSize: undefined }}>{r.type}</span>
                      {r.status === 'verified' && <span className="p-badge p-badge-verified" style={{ fontSize: '0.68rem' }}><span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> Verified</span>}
                      {r.status === 'monitoring' && <span className="p-badge p-badge-monitoring" style={{ fontSize: '0.68rem' }}>Monitoring</span>}
                      {r.status === 'escalated' && <span className="p-badge p-badge-warning" style={{ fontSize: '0.68rem' }}>Escalated</span>}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 'var(--space-2)' }}>
                      <span>{r.agent}</span>
                      <span style={{ width: 3, height: 3, borderRadius: '50%', background: 'var(--text-muted)', flexShrink: 0 }} />
                      <span>Score <span className="mono" style={{ fontWeight: 700, color: r.score >= 80 ? 'var(--green-400)' : 'var(--amber-400)' }}>{r.score}</span></span>
                      <span style={{ width: 3, height: 3, borderRadius: '50%', background: 'var(--text-muted)', flexShrink: 0 }} />
                      <span className="p-badge p-badge-tier" style={{ fontSize: '0.65rem' }}>{r.tier}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2" style={{ whiteSpace: 'nowrap' }}>
                    {r.cert ? (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <Link to="/results" style={{ color: 'var(--purple-400)' }}>{r.cert}</Link>
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-disabled)' }}>No certificate</span>
                    )}
                    {r.date && <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{r.date}</span>}
                  </div>
                </div>
              ))}
            </div>
            <div className="text-center" style={{ marginTop: 'var(--space-6)' }}>
              <Link to="/results" className="p-btn p-btn-ghost">View all results →</Link>
            </div>
          </>
        )}

        {/* ── Evidence tab ── */}
        {activeTab === 'evidence' && (
          <div style={{ animation: 'rpFadeIn 0.25s var(--ease-out) both' }}>
            {/* Evidence mini-timeline */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginBottom: 'var(--space-6)',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--border-secondary)',
                background: 'var(--bg-sunken)',
              }}>
                <h4 style={{ fontSize: '0.88rem' }}>Evidence Envelope — INQ-2026-0847</h4>
                <span className="p-badge p-badge-verified" style={{ fontSize: '0.65rem' }}>
                  <span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> Sealed
                </span>
              </div>
              <div style={{ padding: 'var(--space-4) var(--space-5)', display: 'flex', flexDirection: 'column' }}>
                {[
                  { dot: 'var(--teal-400)', label: 'Signal detected — APAC shipping anomaly', sub: 'Anomalous rerouting patterns across 3 APAC port clusters', time: '06 Mar 09:14' },
                  { dot: 'var(--purple-400)', label: '18 primary sources corroborated', sub: 'Shipping data, port authority filings, satellite imagery, news wires', time: '07 Mar 14:32' },
                  { dot: 'var(--amber-400)', label: '3 counter-signal contradiction checks passed', sub: 'No disconfirming evidence found across adversarial probes', time: '07 Mar 18:05' },
                  { dot: 'var(--green-400)', label: 'Certificate issued — CERT-00291', sub: 'Evidence envelope sealed · Hash-pinned to batch anchor', time: '08 Mar 02:41' },
                ].map((step, i, arr) => (
                  <div key={i} style={{
                    display: 'grid', gridTemplateColumns: '24px 1fr auto', gap: 'var(--space-3)',
                    alignItems: 'start', padding: 'var(--space-3) 0',
                    borderBottom: i < arr.length - 1 ? '1px solid var(--border-secondary)' : undefined,
                  }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: step.dot, marginTop: 4, justifySelf: 'center' }} />
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>{step.label}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{step.sub}</div>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{step.time}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Metric cards — 2x2 grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                {
                  icon: <Search size={18} />, iconColor: 'teal', title: 'Source Health', count: '142', countColor: 'var(--teal-400)',
                  body: 'Active feeds across public shipping data, regulatory filings, satellite imagery, news wires, and market data. Uptime 99.4% over 30 days.',
                  barWidth: '94%', barColor: 'teal', footer: '94% freshness · Last checked 4m ago',
                },
                {
                  icon: <Activity size={18} />, iconColor: 'amber', title: 'Counter-Signals', count: '23', countColor: 'var(--amber-400)',
                  body: 'Active contradiction monitoring across all open inquiries. 3 checks failed corroboration on INQ-0794, triggering escalation review.',
                  barWidth: '87%', barColor: 'amber', footer: '87% pass rate · 3 flagged',
                },
                {
                  icon: <Zap size={18} />, iconColor: 'purple', title: 'Corroboration', count: '6', countColor: 'var(--purple-400)',
                  body: 'Independent claims supported across the active investigation set. Corroboration count tracks claims with 2+ confirming sources.',
                  footer: '6 of 6 claims supported',
                },
                {
                  icon: <Globe size={18} />, iconColor: 'green', title: 'Jurisdictions', count: '6', countColor: 'var(--green-400)',
                  body: 'Evidence spans multiple regulatory jurisdictions with jurisdiction-specific source compliance.',
                  chips: ['APAC', 'EU', 'US', 'LATAM', 'MENA', 'UK'],
                },
              ].map((card) => (
                <div key={card.title} style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)',
                  display: 'flex', flexDirection: 'column', gap: 'var(--space-3)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <div className={`p-proof-icon p-proof-icon-${card.iconColor}`}>{card.icon}</div>
                    <h4 style={{ fontSize: '0.9rem' }}>{card.title}</h4>
                    <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: card.countColor }}>{card.count}</span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>{card.body}</div>
                  {card.barWidth && (
                    <>
                      <div className="p-score-bar-track"><div className={`p-score-bar-fill ${card.barColor}`} style={{ width: card.barWidth }} /></div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{card.footer}</div>
                    </>
                  )}
                  {card.footer && !card.barWidth && !card.chips && (
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>{card.footer}</div>
                  )}
                  {card.chips && (
                    <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginTop: 'var(--space-2)' }}>
                      {card.chips.map((c) => (
                        <span key={c} style={{
                          display: 'inline-flex', alignItems: 'center', padding: '3px 8px',
                          borderRadius: 'var(--radius-sm)', fontSize: '0.72rem', fontWeight: 600,
                          fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.03em',
                          background: 'var(--bg-elevated)', border: '1px solid var(--border-secondary)', color: 'var(--text-secondary)',
                        }}>{c}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Certificates tab ── */}
        {activeTab === 'certificates' && (
          <div style={{ animation: 'rpFadeIn 0.25s var(--ease-out) both', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {[
              {
                variant: 'issued' as const, hero: true,
                status: 'ISSUED', badge: 'verified', badgeText: 'Verified',
                id: 'CERT-00291', idColor: 'var(--green-400)', chip: 'INVESTIGATION',
                title: 'APAC Supply Chain Disruption',
                metrics: [
                  { label: 'Composite', value: '87.4', color: 'var(--green-400)' },
                  { label: 'Accuracy', value: '91%' },
                  { label: 'Brier', value: '0.92' },
                  { label: 'CI Overlap', value: '88%' },
                ],
                barWidth: '87%', barColor: 'green',
                meta: ['sha256:7a3f9b2c…e4d1', 'Stop: outcome_resolved', 'Issued 2026-03-08'],
              },
              {
                variant: 'issued' as const, hero: false,
                status: 'ISSUED', badge: 'verified', badgeText: 'Verified',
                id: 'CERT-00288', idColor: 'var(--green-400)', chip: 'INSPECTION',
                title: 'EU Carbon Credit Pricing',
                metrics: [
                  { label: 'Composite', value: '91.2', color: 'var(--green-400)' },
                  { label: 'Accuracy', value: '93%' },
                  { label: 'Brier', value: '0.89' },
                ],
                barWidth: '91%', barColor: 'green',
                meta: ['sha256:b2e4a71d…c3f8', 'Stop: outcome_resolved', 'Issued 2026-03-05'],
              },
              {
                variant: 'pending' as const, hero: false,
                status: 'PENDING', badge: 'investigating', badgeText: 'Under review',
                id: 'INV-0794', idColor: 'var(--purple-300)', chip: 'INVESTIGATION',
                title: 'Middle East Shipping Lane Risk',
                metrics: [
                  { label: 'Composite', value: '81.3', color: 'var(--purple-300)' },
                  { label: 'Accuracy', value: '—' },
                  { label: 'Stop Condition', value: 'awaiting_resolution' },
                ],
                barWidth: '65%', barColor: 'purple',
                meta: ['Escalated — counter-signal review in progress'],
              },
              {
                variant: 'unissued' as const, hero: false,
                status: 'NOT ISSUED', badge: 'monitoring', badgeText: 'Monitoring',
                id: 'INQ-2026-0819', idColor: 'var(--text-muted)', chip: 'SURVEY', chipGrey: true,
                title: 'Brazil Soy Export Forecast',
                metrics: [
                  { label: 'Composite', value: '78.6', color: 'var(--text-muted)' },
                  { label: 'Status', value: 'Observation only' },
                ],
                meta: ['Certificate not yet eligible — stop condition unmet'],
              },
            ].map((cert) => {
              const borderColor = cert.variant === 'issued'
                ? 'oklch(0.300 0.050 152)'
                : cert.variant === 'pending'
                  ? 'oklch(0.300 0.040 295)'
                  : 'var(--border-primary)';
              const stripBg = cert.variant === 'issued'
                ? 'oklch(0.170 0.040 152)'
                : cert.variant === 'pending'
                  ? 'oklch(0.170 0.035 295)'
                  : 'var(--bg-sunken)';
              const stripColor = cert.variant === 'issued'
                ? 'var(--green-400)'
                : cert.variant === 'pending'
                  ? 'var(--purple-300)'
                  : 'var(--text-muted)';

              return (
                <div key={cert.id} style={{
                  background: 'var(--bg-card)', border: `1px solid ${borderColor}`,
                  borderRadius: 'var(--radius-lg)', overflow: 'hidden',
                  opacity: cert.variant === 'unissued' ? 0.75 : 1,
                  boxShadow: cert.hero ? '0 0 40px -10px oklch(0.545 0.170 152 / 0.12)' : undefined,
                }}>
                  {/* Status strip */}
                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: 'var(--space-2) var(--space-5)', fontFamily: 'var(--font-mono)',
                    fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase',
                    letterSpacing: '0.04em', background: stripBg, color: stripColor,
                  }}>
                    <span>{cert.status}</span>
                    {cert.badge === 'verified' && (
                      <span className="p-badge p-badge-verified" style={{ fontSize: '0.65rem' }}>
                        <span className="p-pulse-dot" style={{ width: 5, height: 5 }} /> {cert.badgeText}
                      </span>
                    )}
                    {cert.badge === 'investigating' && (
                      <span className="p-badge p-badge-tier" style={{ fontSize: '0.65rem' }}>{cert.badgeText}</span>
                    )}
                    {cert.badge === 'monitoring' && (
                      <span className="p-badge p-badge-monitoring" style={{ fontSize: '0.65rem' }}>{cert.badgeText}</span>
                    )}
                  </div>
                  {/* Body */}
                  <div style={{ padding: 'var(--space-5)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', fontWeight: 700, color: cert.idColor }}>{cert.id}</span>
                      <span className={`p-chip ${cert.chipGrey ? '' : 'p-chip-purple'}`} style={{ fontSize: '0.65rem' }}>{cert.chip}</span>
                    </div>
                    <h4 style={{ fontSize: '0.95rem', marginBottom: 'var(--space-2)', color: cert.variant === 'unissued' ? 'var(--text-secondary)' : undefined }}>{cert.title}</h4>
                    <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', marginBottom: 'var(--space-3)' }}>
                      {cert.metrics.map((m) => (
                        <div key={m.label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          <span style={{ fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{m.label}</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.87rem', fontWeight: 600, color: m.color }}>{m.value}</span>
                        </div>
                      ))}
                    </div>
                    {cert.barWidth && (
                      <div className="p-score-bar-track"><div className={`p-score-bar-fill ${cert.barColor}`} style={{ width: cert.barWidth }} /></div>
                    )}
                    <div style={{
                      fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)',
                      marginTop: 'var(--space-3)', paddingTop: 'var(--space-3)',
                      borderTop: '1px solid var(--border-secondary)',
                      display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap',
                    }}>
                      {cert.meta.map((m, i) => <span key={i}>{m}</span>)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Exports tab ── */}
        {activeTab === 'exports' && (
          <div style={{ animation: 'rpFadeIn 0.25s var(--ease-out) both' }}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                {
                  chip: 'Replay', chipClass: 'p-chip-purple', verified: true,
                  title: 'Market Replay Sequences',
                  desc: 'Full agent decision traces with timestamped market state. Linked to CERT-00291, CERT-00288, CERT-00285 outcome labels for RLMF fine-tuning.',
                  packages: 84, updated: '2h ago', certs: 3, pending: 0,
                },
                {
                  chip: 'Calibration', chipClass: 'p-chip-teal', verified: true,
                  title: 'Probability Calibration Datasets',
                  desc: 'Agent probability distributions mapped against resolved outcomes. Certificate-linked Brier scores and reliability diagram inputs.',
                  packages: 42, updated: '6h ago', certs: 3, pending: 0,
                },
                {
                  chip: 'Training', chipClass: 'p-chip-green', verified: false,
                  title: 'Labelled Training Exports',
                  desc: 'Ground-truth labelled datasets from resolved inquiries. Includes outcome labels, evidence references, and quality scores. Pending items excluded.',
                  packages: 31, updated: '12h ago', certs: 2, pending: 1,
                },
              ].map((card) => (
                <div key={card.title} style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)',
                  display: 'flex', flexDirection: 'column', gap: 'var(--space-3)',
                  transition: 'border-color var(--duration-fast) var(--ease-out)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                    <span className={`p-chip ${card.chipClass}`}>{card.chip}</span>
                    {card.verified ? (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)', fontSize: '0.7rem', fontWeight: 600,
                        fontFamily: 'var(--font-mono)', background: 'oklch(0.200 0.040 152)',
                        color: 'var(--green-400)', border: '1px solid oklch(0.300 0.050 152)',
                      }}>✓ Verified</span>
                    ) : (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)', fontSize: '0.7rem', fontWeight: 600,
                        fontFamily: 'var(--font-mono)', background: 'oklch(0.200 0.008 265)',
                        color: 'var(--text-muted)', border: '1px solid oklch(0.300 0.010 265)',
                      }}>Partial</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 600 }}>{card.title}</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>{card.desc}</div>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap',
                    marginTop: 'auto', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-secondary)',
                    fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)',
                  }}>
                    <span>{card.packages} packages</span>
                    <span>·</span>
                    <span>Updated {card.updated}</span>
                    <span>·</span>
                    {card.pending > 0 ? (
                      <span style={{ color: 'var(--text-muted)' }}>{card.certs} certs linked · {card.pending} pending</span>
                    ) : (
                      <span style={{ color: 'var(--green-400)' }}>{card.certs} certs linked</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

/* ═══════════════════════ ECOSYSTEM ═══════════════════════ */
function EcosystemSection() {
  return (
    <section className="p-section" id="ecosystem">
      <div className="p-container">
        <p className="eyebrow mb-2" style={{ textAlign: 'center' }}>Ecosystem</p>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-3)' }}>The verification substrate.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 560, margin: '0 auto var(--space-10)', fontSize: '0.95rem' }}>
          Echelon sits beneath agent marketplaces, model routing layers, and orchestration runtimes as the independent verification layer.
        </p>
        <ScrollIn>
          <div style={{ border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', background: 'var(--bg-card)' }}>
            <div className="flex items-center gap-3" style={{ padding: 'var(--space-4) var(--space-6)', borderBottom: '1px solid var(--border-secondary)', background: 'var(--bg-sunken)' }}>
              <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Echelon Verification Substrate</span>
            </div>
            {[
              { label: 'Inputs', tags: ['Markets & inquiries', 'OSINT feeds', 'Agent submissions'] },
              { label: 'Processing', tags: [{ text: 'Detect', color: 'var(--teal-400)' }, { text: 'Investigate', color: 'var(--purple-400)' }, { text: 'Certify', color: 'var(--green-400)' }, { text: 'Route', color: 'var(--amber-400)' }] },
              { label: 'Outputs', tags: ['Certificates', 'Routing signals', 'RLMF data'] },
              { label: 'Consumers', tags: ['Agent marketplaces', 'Model routers', 'Orchestration runtimes', 'Audit systems'] },
            ].map((row) => (
              <div key={row.label} className="grid" style={{ gridTemplateColumns: '160px 1fr', borderBottom: '1px solid var(--border-secondary)' }}>
                <div className="flex items-center" style={{ padding: 'var(--space-4) var(--space-6)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', borderRight: '1px solid var(--border-secondary)', background: 'var(--bg-sunken)' }}>{row.label}</div>
                <div className="flex items-center gap-3 flex-wrap" style={{ padding: 'var(--space-4) var(--space-6)' }}>
                  {row.tags.map((tag, i) => {
                    const isObj = typeof tag === 'object';
                    return (
                      <span key={i}>
                        {i > 0 && <span style={{ color: 'var(--text-muted)', padding: '0 4px', fontSize: '0.8rem' }}>→</span>}
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 6,
                          padding: '4px 10px', fontSize: '0.78rem', fontWeight: 500,
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-elevated)', border: '1px solid var(--border-secondary)',
                          color: isObj ? tag.color : 'var(--text-secondary)',
                          borderColor: isObj ? tag.color : undefined,
                        }}>
                          {isObj ? tag.text : tag}
                        </span>
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </ScrollIn>
      </div>
    </section>
  );
}

/* ═══════════════════════ RLMF ═══════════════════════ */
function RLMFSection() {
  const cards = [
    { chip: 'Replay', chipClass: 'p-chip-purple', badge: 'verified', title: 'Market Replay Sequences', desc: 'Full agent decision traces with timestamped market state, linked to certificate outcomes. Use for RLMF fine-tuning and behavioural audit.', meta: '84 packages · Updated 2h ago' },
    { chip: 'Calibration', chipClass: 'p-chip-teal', badge: 'verified', title: 'Probability Calibration Datasets', desc: 'Agent probability distributions mapped against resolved outcomes. Certificate-linked Brier scores and reliability diagrams.', meta: '42 packages · Updated 6h ago' },
    { chip: 'Training', chipClass: 'p-chip-green', badge: 'monitoring', title: 'Labelled Training Exports', desc: 'Ground-truth labelled datasets derived from resolved inquiries. Includes outcome labels, evidence references, and quality scores.', meta: '31 packages · Updated 12h ago' },
  ];

  return (
    <section className="p-section" id="data-products">
      <div className="p-container">
        <p className="eyebrow mb-2" style={{ textAlign: 'center' }}>Data products</p>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-3)' }}>Verified activity becomes usable data.</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', maxWidth: 560, margin: '0 auto var(--space-10)', fontSize: '0.95rem' }}>
          Echelon does not stop at scoring. The system produces replayable, label-linked, certificate-aware exports for calibration, evaluation, training, and audit workflows.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {cards.map((c) => (
            <ScrollIn key={c.title}>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`p-chip ${c.chipClass}`}>{c.chip}</span>
                  {c.badge === 'verified' ? <span className="p-badge p-badge-verified" style={{ fontSize: '0.65rem' }}>Verified</span> : <span className="p-badge p-badge-monitoring" style={{ fontSize: '0.65rem' }}>Partial</span>}
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{c.title}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{c.desc}</div>
                <div className="mono mt-2" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.meta}</div>
              </div>
            </ScrollIn>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════ FINAL CTA ═══════════════════════ */
function FinalCTA() {
  return (
    <div className="text-center" style={{ padding: 'var(--space-20) 0', background: 'var(--bg-sunken)', borderTop: '1px solid var(--border-secondary)', borderBottom: '1px solid var(--border-secondary)' }}>
      <div className="p-container">
        <h2 style={{ marginBottom: 'var(--space-4)' }}>Build on verified agents.</h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: 520, margin: '0 auto var(--space-8)', fontSize: '0.95rem' }}>
          If you need a way to test agents against reality, issue proof, and route on the result, Echelon is the missing layer.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/results" className="p-btn p-btn-primary">Explore Results</Link>
          <a href="#" className="p-btn p-btn-secondary">Talk to Us</a>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════ PAGE ═══════════════════════ */
export default function PublicLandingPage() {
  return (
    <>
      <HeroSection />
      <WhySection />
      <HowItWorksSection />
      <FeaturedProofSection />
      <ResultsPreviewSection />
      <EcosystemSection />
      <RLMFSection />
      <FinalCTA />
    </>
  );
}
