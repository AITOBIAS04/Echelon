import { Bell, ChevronDown, Menu, PanelLeftClose, PanelLeftOpen, Search, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ShellHeaderProps {
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onOpenMobileMenu: () => void;
}

export function ShellHeader({
  sidebarCollapsed,
  onToggleSidebar,
  onOpenMobileMenu,
}: ShellHeaderProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-30 flex h-14 items-center justify-between border-b border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-6 shadow-[var(--e-shadow-xs)]">
      <div className="flex min-w-[216px] items-center gap-4">
        <button
          type="button"
          onClick={onOpenMobileMenu}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-secondary)] md:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onToggleSidebar}
          className="hidden h-8 w-8 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-secondary)] md:inline-flex"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
        <Link to="/home" className="flex items-center gap-2 text-[var(--e-text-primary)] no-underline">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--e-purple-500)] font-mono text-sm font-semibold tracking-[-0.02em] text-[var(--e-text-inverse)]">
            E
          </span>
          <span className="text-[17px] font-bold tracking-[-0.02em]">Echelon</span>
          <span className="rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-1.5 py-px font-mono text-[11px] font-medium text-[var(--e-text-muted)]">
            v1
          </span>
        </Link>
      </div>

      <div className="hidden flex-1 items-center justify-center px-8 lg:flex">
        <div className="relative w-full max-w-[480px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--e-text-muted)]" />
          <input
            type="search"
            placeholder="Search theatres, investigations, certificates..."
            className="h-9 w-full rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] pl-9 pr-14 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)] focus:bg-[var(--e-bg-card)] focus:shadow-[0_0_0_2px_oklch(0.53_0.23_295_/_0.12)]"
          />
          <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] px-1.5 py-px font-mono text-[11px] text-[var(--e-text-disabled)]">
            /
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-1 rounded-full border border-[color:oklch(0.545_0.170_152_/_0.2)] bg-[color:oklch(0.545_0.170_152_/_0.1)] px-2.5 py-1 font-mono text-[11px] font-medium text-[var(--e-green-600)] md:flex">
          <span className="h-2 w-2 rounded-full bg-[var(--status-success)] shadow-[0_0_0_2px_oklch(0.545_0.170_152_/_0.20)]" />
          Testnet Live
        </div>
        <button
          type="button"
          className="relative inline-flex h-9 w-9 items-center justify-center rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute -right-1 -top-1 flex min-h-4 min-w-4 items-center justify-center rounded-full border-2 border-[var(--e-bg-card)] bg-[var(--status-danger)] px-1 font-mono text-[10px] font-semibold text-[var(--e-text-inverse)]">
            3
          </span>
        </button>
        <button
          type="button"
          disabled
          title="Wallet connect not yet wired in this shell pass"
          className="hidden items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[13px] font-semibold text-[var(--e-text-primary)] md:inline-flex"
        >
          <Shield className="h-4 w-4 text-[var(--e-purple-500)]" />
          <span>Wallet</span>
          <ChevronDown className="h-4 w-4 text-[var(--e-text-muted)]" />
        </button>
      </div>
    </header>
  );
}

export default ShellHeader;
