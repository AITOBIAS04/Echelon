import { useState, useCallback } from 'react';
import { Shield, Check, X, BarChart3, FileText, Lock, LayoutGrid } from 'lucide-react';

type VerifyState = 'idle' | 'verifying' | 'pass' | 'fail';

interface PipelineCheck {
  label: string;
  description: string;
  icon: React.ReactNode;
  status: 'idle' | 'pass' | 'fail';
}

const CHECKS_EXPLAIN: { label: string; description: string; icon: React.ReactNode }[] = [
  {
    label: 'Structural integrity',
    description: 'Envelope schema, required fields, type checks',
    icon: <LayoutGrid size={18} />,
  },
  {
    label: 'Template conformance',
    description: 'Schema version match, field coverage',
    icon: <FileText size={18} />,
  },
  {
    label: 'Score mathematics',
    description: 'Composite recalculation, weight-sum audit',
    icon: <BarChart3 size={18} />,
  },
  {
    label: 'Cryptographic chain',
    description: 'Hash anchoring, batch membership proof',
    icon: <Lock size={18} />,
  },
];

export default function PublicVerifyPage() {
  const [input, setInput] = useState('');
  const [state, setState] = useState<VerifyState>('idle');
  const [checks, setChecks] = useState<PipelineCheck[]>([]);

  const runVerify = useCallback(() => {
    const val = input.trim();
    if (!val) return;

    setState('verifying');

    // Simulate pipeline checks
    const newChecks: PipelineCheck[] = CHECKS_EXPLAIN.map((c) => ({
      ...c,
      status: 'pass' as const,
    }));

    setTimeout(() => {
      setChecks(newChecks);
      setState('pass');
    }, 600);
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') runVerify();
  };

  return (
    <>
      {/* ═══ Verify Hero ═══ */}
      <section
        className="p-section"
        style={{ paddingTop: 'var(--space-20)', paddingBottom: 'var(--space-12)', textAlign: 'center' }}
      >
        <div className="p-container">
          {/* Shield icon */}
          <div
            className="p-proof-icon p-proof-icon-green"
            style={{
              width: 56,
              height: 56,
              borderRadius: 'var(--radius-lg)',
              margin: '0 auto var(--space-6)',
            }}
          >
            <Shield size={28} />
          </div>

          <h1 style={{ fontSize: '2rem', maxWidth: 520, margin: '0 auto var(--space-3)' }}>
            Verify a certificate
          </h1>
          <p
            style={{
              fontSize: '0.95rem',
              color: 'var(--text-secondary)',
              maxWidth: 480,
              margin: '0 auto var(--space-8)',
            }}
          >
            Independent verification. No account required. Paste a certificate hash or certificate ID
            to confirm its integrity.
          </p>

          {/* Terminal-style input */}
          <div
            style={{
              maxWidth: 640,
              margin: '0 auto',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
            }}
          >
            {/* Terminal bar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '10px 16px',
                borderBottom: '1px solid var(--border-secondary)',
                background: 'var(--bg-elevated)',
              }}
            >
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--red-400)', opacity: 0.6 }} />
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--amber-400)', opacity: 0.6 }} />
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--green-400)', opacity: 0.6 }} />
              <span
                className="mono"
                style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginLeft: 'var(--space-2)' }}
              >
                echelon verify
              </span>
            </div>
            {/* Input row */}
            <div style={{ padding: 'var(--space-4) var(--space-5)' }}>
              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="CERT-00291 or sha256:7a3f9b2c..."
                  aria-label="Certificate hash or ID"
                  style={{
                    flex: 1,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.87rem',
                    padding: '10px 14px',
                    background: 'var(--bg-sunken)',
                    border: '1px solid var(--border-secondary)',
                    borderRadius: 'var(--radius)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    transition: 'border-color var(--duration-fast) var(--ease-out)',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--border-focus)')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-secondary)')}
                />
                <button className="p-btn p-btn-primary" onClick={runVerify}>
                  Verify
                </button>
              </div>
            </div>
          </div>

          {/* ═══ Result (shown after verify) ═══ */}
          {state !== 'idle' && (
            <div style={{ maxWidth: 640, margin: 'var(--space-8) auto 0' }}>
              {/* Verdict banner */}
              {state === 'pass' && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-4) var(--space-5)',
                    borderRadius: 'var(--radius-lg)',
                    background: 'oklch(0.200 0.050 152)',
                    border: '1px solid oklch(0.300 0.060 152)',
                    color: 'var(--green-400)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    letterSpacing: '0.04em',
                  }}
                >
                  <Shield size={20} />
                  CERTIFICATE VALID
                </div>
              )}

              {state === 'fail' && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-4) var(--space-5)',
                    borderRadius: 'var(--radius-lg)',
                    background: 'oklch(0.200 0.050 25)',
                    border: '1px solid oklch(0.300 0.060 25)',
                    color: 'var(--red-400)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    letterSpacing: '0.04em',
                  }}
                >
                  <X size={20} />
                  CERTIFICATE INVALID
                </div>
              )}

              {state === 'verifying' && (
                <div
                  style={{
                    padding: 'var(--space-4) var(--space-5)',
                    borderRadius: 'var(--radius-lg)',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-primary)',
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    textAlign: 'center',
                  }}
                >
                  Verifying...
                </div>
              )}

              {/* Pipeline checks */}
              {checks.length > 0 && (
                <div
                  style={{
                    marginTop: 'var(--space-6)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                  }}
                >
                  {checks.map((check) => (
                    <div
                      key={check.label}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-3)',
                        padding: 'var(--space-3) var(--space-4)',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-primary)',
                        borderRadius: 'var(--radius)',
                      }}
                    >
                      <div
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: 'var(--radius-sm)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background:
                            check.status === 'pass'
                              ? 'oklch(0.200 0.050 152)'
                              : 'oklch(0.200 0.050 25)',
                          color:
                            check.status === 'pass' ? 'var(--green-400)' : 'var(--red-400)',
                          flexShrink: 0,
                        }}
                      >
                        {check.status === 'pass' ? <Check size={16} strokeWidth={2.5} /> : <X size={16} strokeWidth={2.5} />}
                      </div>
                      <div style={{ flex: 1, fontSize: '0.85rem', fontWeight: 500 }}>{check.label}</div>
                      <span
                        className="mono"
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          letterSpacing: '0.04em',
                          color:
                            check.status === 'pass' ? 'var(--green-400)' : 'var(--red-400)',
                        }}
                      >
                        {check.status === 'pass' ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Certificate detail card */}
              {state === 'pass' && (
                <div
                  style={{
                    marginTop: 'var(--space-6)',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: 'var(--radius-lg)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: 'var(--space-4) var(--space-5)',
                      borderBottom: '1px solid var(--border-secondary)',
                    }}
                  >
                    <div>
                      <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                        CERT-00291
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                        APAC Supply Chain Disruption
                      </div>
                    </div>
                    <span className="p-badge p-badge-tier" style={{ fontSize: '0.65rem' }}>
                      TIER 2 — BACKTESTED
                    </span>
                  </div>
                  <div style={{ padding: 'var(--space-4) var(--space-5)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                      <div>
                        <div
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.06em',
                            color: 'var(--text-muted)',
                            marginBottom: 2,
                          }}
                        >
                          Composite
                        </div>
                        <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--green-400)' }}>
                          87.4
                        </div>
                      </div>
                      <div>
                        <div
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.06em',
                            color: 'var(--text-muted)',
                            marginBottom: 2,
                          }}
                        >
                          Issued
                        </div>
                        <div className="mono" style={{ fontSize: '0.85rem' }}>
                          2026-03-08
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        marginTop: 'var(--space-4)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.78rem',
                        wordBreak: 'break-all',
                        lineHeight: 1.5,
                      }}
                    >
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>
                        SHA-256 Hash
                      </div>
                      sha256:7a3f9b2c4e8d1f3a6b9c2d5e8f1a3b6c9d2e5f8a1b4c7d0e3f6a9b2c5d8e1f08a
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══ Pipeline explanation ═══ */}
          <div style={{ maxWidth: 800, margin: 'var(--space-12) auto 0' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--text-muted)',
                textAlign: 'center',
                marginBottom: 'var(--space-6)',
              }}
            >
              Four independent checks
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)' }}>
              {CHECKS_EXPLAIN.map((check) => (
                <div
                  key={check.label}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-5) var(--space-4)',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: 'var(--radius-lg)',
                  }}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 'var(--radius)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-secondary)',
                      flexShrink: 0,
                    }}
                  >
                    {check.icon}
                  </div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{check.label}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {check.description}
                  </div>
                </div>
              ))}
            </div>

            <p
              style={{
                fontSize: '0.82rem',
                color: 'var(--text-muted)',
                textAlign: 'center',
                lineHeight: 1.6,
                marginTop: 'var(--space-8)',
              }}
            >
              Any single failure marks the certificate as invalid. All four checks must pass
              independently.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
