/**
 * Entity Profile Panel
 *
 * Displays resolved entity profile with source queries and provenance.
 */

import type { EntityProfile } from '../../types/investigation';

export function EntityProfilePanel({ profile }: { profile: EntityProfile | null }) {
  if (!profile) {
    return (
      <div className="text-terminal-text-muted text-xs p-4">
        No entity profile resolved. Submit an entity query first.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Profile identity */}
      <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
          Entity Profile
        </h3>
        <dl className="grid grid-cols-2 gap-2 text-xs">
          <dt className="text-terminal-text-muted">Entity ID</dt>
          <dd className="font-mono text-terminal-text">{profile.entity_id}</dd>
          <dt className="text-terminal-text-muted">Name</dt>
          <dd className="text-terminal-text">{profile.entity_name}</dd>
          <dt className="text-terminal-text-muted">Jurisdiction</dt>
          <dd className="text-terminal-text">{profile.jurisdiction ?? '—'}</dd>
          <dt className="text-terminal-text-muted">Registration</dt>
          <dd className="font-mono text-terminal-text">{profile.registration_number ?? '—'}</dd>
          <dt className="text-terminal-text-muted">Profile Hash</dt>
          <dd className="font-mono text-terminal-text">
            {profile.profile_hash.substring(0, 16)}...
          </dd>
          <dt className="text-terminal-text-muted">Resolved At</dt>
          <dd className="text-terminal-text">
            {new Date(profile.resolved_at).toLocaleString()}
          </dd>
        </dl>
      </div>

      {/* Data fields */}
      {Object.keys(profile.data).length > 0 && (
        <div className="bg-terminal-surface rounded-lg p-4 border border-terminal-border">
          <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
            Resolved Data
          </h3>
          <dl className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(profile.data).map(([key, value]) => (
              <div key={key} className="contents">
                <dt className="text-terminal-text-muted">{key}</dt>
                <dd className="font-mono text-terminal-text break-all">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
