import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sun, Moon, Menu, X } from 'lucide-react';

const NAV_LINKS = [
  { to: '/results', label: 'Results' },
  { to: '/verify-public', label: 'Verify' },
  { to: '/results', label: 'Certificates' },
  { to: '/#how-it-works', label: 'How It Works' },
];

export function PublicNav() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>(() =>
    document.documentElement.classList.contains('light') ? 'light' : 'dark'
  );

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    if (next === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }

  function isActive(to: string) {
    if (to.includes('#')) return false;
    return location.pathname === to;
  }

  return (
    <nav className="p-nav" role="navigation" aria-label="Main navigation">
      <div
        className="flex items-center justify-between"
        style={{ height: 56, maxWidth: 1200, margin: '0 auto', padding: '0 var(--space-6)' }}
      >
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 no-underline" style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '1.05rem', letterSpacing: '-0.01em' }}>
          <svg width="26" height="26" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect x="2" y="2" width="28" height="28" rx="6" stroke="currentColor" strokeWidth="2" />
            <path d="M8 10h16M8 16h12M8 22h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <circle cx="24" cy="22" r="3" fill="currentColor" opacity="0.4" />
          </svg>
          Echelon
        </Link>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-1 list-none m-0 p-0">
          {NAV_LINKS.map((link) => (
            <li key={link.to}>
              <Link
                to={link.to}
                className="block px-3 py-1.5 text-sm font-medium no-underline"
                style={{
                  color: isActive(link.to) ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: isActive(link.to) ? 'var(--bg-hover)' : 'transparent',
                  borderRadius: 'var(--radius-sm)',
                  transition: 'color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out)',
                }}
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="flex items-center justify-center"
            style={{
              width: 36, height: 36, borderRadius: 'var(--radius)',
              border: '1px solid var(--border-primary)', background: 'transparent',
              color: 'var(--text-secondary)', cursor: 'pointer',
              transition: 'all var(--duration-fast) var(--ease-out)',
            }}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link
            to="/results"
            className="p-btn p-btn-primary p-btn-sm hidden md:inline-flex"
          >
            View Results
          </Link>
          <button
            className="flex md:hidden items-center justify-center"
            style={{ width: 36, height: 36, border: 'none', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer' }}
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          className="flex flex-col gap-1 md:hidden"
          style={{
            padding: 'var(--space-4) var(--space-6) var(--space-6)',
            borderBottom: '1px solid var(--border-secondary)',
            background: 'var(--bg-app)',
          }}
        >
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setMobileOpen(false)}
              className="block no-underline"
              style={{
                padding: '10px 12px',
                fontSize: '0.95rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              {link.label}
            </Link>
          ))}
          <Link
            to="/results"
            onClick={() => setMobileOpen(false)}
            className="block no-underline"
            style={{ padding: '10px 12px', color: 'var(--purple-400)', fontWeight: 600 }}
          >
            View Results →
          </Link>
        </div>
      )}
    </nav>
  );
}
