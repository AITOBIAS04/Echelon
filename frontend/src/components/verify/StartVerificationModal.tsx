/**
 * StartVerificationModal — Form modal for creating a new verification run.
 *
 * Client-side validation matching backend Pydantic constraints.
 * Escape key + backdrop click to close.
 */

import { useState, useEffect } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { clsx } from 'clsx';
import { demoStore } from '../../demo/demoStore';
import type { VerificationRunCreateRequest } from '../../types/verification';

// ── Validation ───────────────────────────────────────────────────────────

interface FormErrors {
  repo_url?: string;
  construct_id?: string;
  oracle_url?: string;
  oracle_module?: string;
  oracle_callable?: string;
  limit?: string;
  min_replays?: string;
}

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {};

  if (!form.repo_url.trim()) {
    errors.repo_url = 'Required';
  } else if (form.repo_url.length > 500) {
    errors.repo_url = 'Max 500 characters';
  }

  if (!form.construct_id.trim()) {
    errors.construct_id = 'Required';
  } else if (form.construct_id.length > 255) {
    errors.construct_id = 'Max 255 characters';
  }

  if (form.oracle_type === 'http') {
    if (!form.oracle_url.trim()) {
      errors.oracle_url = 'Required for HTTP oracle';
    }
  }

  if (form.oracle_type === 'python') {
    if (!form.oracle_module.trim()) {
      errors.oracle_module = 'Required for Python oracle';
    }
    if (!form.oracle_callable.trim()) {
      errors.oracle_callable = 'Required for Python oracle';
    }
  }

  const limit = Number(form.limit);
  if (isNaN(limit) || limit < 1 || limit > 1000) {
    errors.limit = 'Must be 1–1000';
  }

  const minReplays = Number(form.min_replays);
  if (isNaN(minReplays) || minReplays < 1 || minReplays > 500) {
    errors.min_replays = 'Must be 1–500';
  }

  return errors;
}

// ── Form state ───────────────────────────────────────────────────────────

interface FormState {
  repo_url: string;
  construct_id: string;
  oracle_type: 'http' | 'python';
  oracle_url: string;
  oracle_module: string;
  oracle_callable: string;
  github_token: string;
  limit: string;
  min_replays: string;
}

const INITIAL_FORM: FormState = {
  repo_url: '',
  construct_id: '',
  oracle_type: 'http',
  oracle_url: '',
  oracle_module: '',
  oracle_callable: '',
  github_token: '',
  limit: '100',
  min_replays: '50',
};

// ── Component ────────────────────────────────────────────────────────────

interface StartVerificationModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (body: VerificationRunCreateRequest) => Promise<void>;
  isSubmitting: boolean;
}

export function StartVerificationModal({
  open,
  onClose,
  onSubmit,
  isSubmitting,
}: StartVerificationModalProps) {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [showToken, setShowToken] = useState(false);

  // Reset form when opening
  useEffect(() => {
    if (open) {
      setForm(INITIAL_FORM);
      setErrors({});
      setShowToken(false);
    }
  }, [open]);

  // Escape key to close
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const updateField = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear error on change
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field as keyof FormErrors];
        return next;
      });
    }
  };

  const handleSubmit = async () => {
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    const body: VerificationRunCreateRequest = {
      repo_url: form.repo_url.trim(),
      construct_id: form.construct_id.trim(),
      oracle_type: form.oracle_type,
      limit: Number(form.limit),
      min_replays: Number(form.min_replays),
    };

    if (form.oracle_type === 'http' && form.oracle_url.trim()) {
      body.oracle_url = form.oracle_url.trim();
    }
    if (form.oracle_type === 'python') {
      if (form.oracle_module.trim()) body.oracle_module = form.oracle_module.trim();
      if (form.oracle_callable.trim()) body.oracle_callable = form.oracle_callable.trim();
    }
    if (form.github_token.trim()) {
      body.github_token = form.github_token.trim();
    }

    try {
      await onSubmit(body);
      demoStore.pushToast('Verification started');
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start verification';
      demoStore.pushToast(message);
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-[300] bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-[310] flex items-start justify-center pt-[10vh] pointer-events-none"
      >
        <div
          className="max-w-lg w-full bg-terminal-overlay border border-terminal-border rounded-xl shadow-elevation-3 pointer-events-auto flex flex-col max-h-[80vh]"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          {/* Header */}
          <div className="section-header flex-shrink-0">
            <span id="modal-title" className="section-header-title">Start Verification</span>
            <button
              onClick={onClose}
              className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text"
            >
              &#x2715;
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4 overflow-y-auto">
            {/* repo_url */}
            <Field
              label="Repository URL"
              required
              error={errors.repo_url}
            >
              <input
                type="text"
                className={fieldClass(errors.repo_url)}
                placeholder="https://github.com/org/repo"
                value={form.repo_url}
                onChange={(e) => updateField('repo_url', e.target.value)}
              />
            </Field>

            {/* construct_id */}
            <Field
              label="Construct ID"
              required
              error={errors.construct_id}
            >
              <input
                type="text"
                className={fieldClass(errors.construct_id)}
                placeholder="e.g. osint-oracle-v3"
                value={form.construct_id}
                onChange={(e) => updateField('construct_id', e.target.value)}
              />
            </Field>

            {/* oracle_type */}
            <Field label="Oracle Type">
              <select
                className="terminal-input w-full"
                value={form.oracle_type}
                onChange={(e) => updateField('oracle_type', e.target.value)}
              >
                <option value="http">HTTP</option>
                <option value="python">Python</option>
              </select>
            </Field>

            {/* Conditional oracle fields */}
            {form.oracle_type === 'http' && (
              <Field
                label="Oracle URL"
                required
                error={errors.oracle_url}
              >
                <input
                  type="text"
                  className={fieldClass(errors.oracle_url)}
                  placeholder="https://oracle.example.com/verify"
                  value={form.oracle_url}
                  onChange={(e) => updateField('oracle_url', e.target.value)}
                />
              </Field>
            )}

            {form.oracle_type === 'python' && (
              <>
                <Field
                  label="Oracle Module"
                  required
                  error={errors.oracle_module}
                >
                  <input
                    type="text"
                    className={fieldClass(errors.oracle_module)}
                    placeholder="e.g. oracles.my_oracle"
                    value={form.oracle_module}
                    onChange={(e) => updateField('oracle_module', e.target.value)}
                  />
                </Field>
                <Field
                  label="Oracle Callable"
                  required
                  error={errors.oracle_callable}
                >
                  <input
                    type="text"
                    className={fieldClass(errors.oracle_callable)}
                    placeholder="e.g. verify_prediction"
                    value={form.oracle_callable}
                    onChange={(e) => updateField('oracle_callable', e.target.value)}
                  />
                </Field>
              </>
            )}

            {/* github_token */}
            <Field label="GitHub Token">
              <div className="relative">
                <input
                  type={showToken ? 'text' : 'password'}
                  className="terminal-input w-full pr-8"
                  placeholder="Optional — for private repos"
                  value={form.github_token}
                  onChange={(e) => updateField('github_token', e.target.value)}
                />
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-terminal-text-muted hover:text-terminal-text transition-colors"
                  onClick={() => setShowToken(!showToken)}
                  aria-label={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </Field>

            {/* limit + min_replays side by side */}
            <div className="grid grid-cols-2 gap-3">
              <Field
                label="Limit"
                error={errors.limit}
              >
                <input
                  type="number"
                  className={fieldClass(errors.limit)}
                  value={form.limit}
                  onChange={(e) => updateField('limit', e.target.value)}
                  min={1}
                  max={1000}
                />
              </Field>
              <Field
                label="Min Replays"
                error={errors.min_replays}
              >
                <input
                  type="number"
                  className={fieldClass(errors.min_replays)}
                  value={form.min_replays}
                  onChange={(e) => updateField('min_replays', e.target.value)}
                  min={1}
                  max={500}
                />
              </Field>
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-terminal-border flex-shrink-0">
            <button
              className="btn-cyan w-full"
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Starting...' : 'Start Verification'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────

function fieldClass(error?: string): string {
  return clsx(
    'terminal-input w-full',
    error && 'border-status-danger focus:border-status-danger focus:ring-status-danger/20'
  );
}

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <label className="data-label">
        {label}
        {required && <span className="text-status-danger ml-0.5">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-[10px] text-status-danger">{error}</p>
      )}
    </div>
  );
}
