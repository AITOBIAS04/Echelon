import { useState, useEffect } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { clsx } from 'clsx';
import { demoStore } from '../../demo/demoStore';
import type { VerificationRunCreateRequest } from '../../types/verification';

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

  if (form.oracle_type === 'http' && !form.oracle_url.trim()) {
    errors.oracle_url = 'Required for HTTP oracle';
  }

  if (form.oracle_type === 'python') {
    if (!form.oracle_module.trim()) errors.oracle_module = 'Required for Python oracle';
    if (!form.oracle_callable.trim()) errors.oracle_callable = 'Required for Python oracle';
  }

  const limit = Number(form.limit);
  if (isNaN(limit) || limit < 1 || limit > 1000) errors.limit = 'Must be 1–1000';

  const minReplays = Number(form.min_replays);
  if (isNaN(minReplays) || minReplays < 1 || minReplays > 500) errors.min_replays = 'Must be 1–500';

  return errors;
}

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

  useEffect(() => {
    if (open) {
      setForm(INITIAL_FORM);
      setErrors({});
      setShowToken(false);
    }
  }, [open]);

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

    if (form.oracle_type === 'http' && form.oracle_url.trim()) body.oracle_url = form.oracle_url.trim();
    if (form.oracle_type === 'python') {
      if (form.oracle_module.trim()) body.oracle_module = form.oracle_module.trim();
      if (form.oracle_callable.trim()) body.oracle_callable = form.oracle_callable.trim();
    }
    if (form.github_token.trim()) body.github_token = form.github_token.trim();

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
      <div
        className="fixed inset-0 z-[300] bg-[color:oklch(0.205_0.015_265_/_0.14)] backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="fixed inset-0 z-[310] flex items-start justify-center pt-[10vh]">
        <div
          className="flex max-h-[80vh] w-full max-w-lg flex-col rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-lg)]"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div className="flex flex-shrink-0 items-center justify-between border-b border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-5 py-4">
            <div>
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                Verification Run
              </div>
              <span id="modal-title" className="text-[15px] font-semibold text-[var(--e-text-primary)]">
                Start Verification
              </span>
            </div>
            <button
              onClick={onClose}
              className="rounded p-1 text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
            >
              &#x2715;
            </button>
          </div>

          <div className="space-y-4 overflow-y-auto p-4">
            <Field label="Repository URL" required error={errors.repo_url}>
              <input
                type="text"
                className={fieldClass(errors.repo_url)}
                placeholder="https://github.com/org/repo"
                value={form.repo_url}
                onChange={(e) => updateField('repo_url', e.target.value)}
              />
            </Field>

            <Field label="Construct ID" required error={errors.construct_id}>
              <input
                type="text"
                className={fieldClass(errors.construct_id)}
                placeholder="e.g. osint-oracle-v3"
                value={form.construct_id}
                onChange={(e) => updateField('construct_id', e.target.value)}
              />
            </Field>

            <Field label="Oracle Type">
              <select
                className={fieldClass()}
                value={form.oracle_type}
                onChange={(e) => updateField('oracle_type', e.target.value)}
              >
                <option value="http">HTTP</option>
                <option value="python">Python</option>
              </select>
            </Field>

            {form.oracle_type === 'http' ? (
              <Field label="Oracle URL" required error={errors.oracle_url}>
                <input
                  type="text"
                  className={fieldClass(errors.oracle_url)}
                  placeholder="https://oracle.example.com/verify"
                  value={form.oracle_url}
                  onChange={(e) => updateField('oracle_url', e.target.value)}
                />
              </Field>
            ) : (
              <>
                <Field label="Oracle Module" required error={errors.oracle_module}>
                  <input
                    type="text"
                    className={fieldClass(errors.oracle_module)}
                    placeholder="e.g. oracles.my_oracle"
                    value={form.oracle_module}
                    onChange={(e) => updateField('oracle_module', e.target.value)}
                  />
                </Field>
                <Field label="Oracle Callable" required error={errors.oracle_callable}>
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

            <Field label="GitHub Token">
              <div className="relative">
                <input
                  type={showToken ? 'text' : 'password'}
                  className="h-11 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 pr-10 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)]"
                  placeholder="Optional — for private repos"
                  value={form.github_token}
                  onChange={(e) => updateField('github_token', e.target.value)}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--e-text-muted)] transition hover:text-[var(--e-text-primary)]"
                  onClick={() => setShowToken(!showToken)}
                  aria-label={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </div>
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Limit" error={errors.limit}>
                <input
                  type="number"
                  className={fieldClass(errors.limit)}
                  value={form.limit}
                  onChange={(e) => updateField('limit', e.target.value)}
                  min={1}
                  max={1000}
                />
              </Field>
              <Field label="Min Replays" error={errors.min_replays}>
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

          <div className="flex-shrink-0 border-t border-[var(--e-border-secondary)] px-4 py-4">
            <button
              className="inline-flex h-11 w-full items-center justify-center rounded-md border border-[var(--e-purple-500)] bg-[var(--e-purple-500)] px-4 text-[13px] font-semibold text-white transition hover:bg-[var(--e-purple-400)] disabled:cursor-not-allowed disabled:opacity-60"
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

function fieldClass(error?: string): string {
  return clsx(
    'h-11 w-full rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-4 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-purple-500)]',
    error && 'border-[var(--e-red-600)] focus:border-[var(--e-red-600)]',
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
      <label className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
        {label}
        {required ? <span className="ml-0.5 text-[var(--e-red-600)]">*</span> : null}
      </label>
      {children}
      {error ? <p className="text-[10px] text-[var(--e-red-600)]">{error}</p> : null}
    </div>
  );
}
