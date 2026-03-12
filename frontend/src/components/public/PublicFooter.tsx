export function PublicFooter() {
  return (
    <footer className="p-footer">
      <div
        className="flex items-center justify-between flex-wrap gap-4"
        style={{ maxWidth: 1200, margin: '0 auto', padding: '0 var(--space-6)' }}
      >
        <span>&copy; {new Date().getFullYear()} Echelon. Verification infrastructure for AI agents.</span>
        <div className="flex items-center gap-4">
          <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="/public/verify">Verify</a>
          <a href="/public/results">Results</a>
        </div>
      </div>
    </footer>
  );
}
