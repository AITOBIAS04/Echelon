import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bell, ChevronDown, ExternalLink, Link as LinkIcon, Menu, PanelLeftClose, PanelLeftOpen, Search, Shield, Wallet } from 'lucide-react';
import { Link } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { paymentsApi } from '../../api/payments';

interface ShellHeaderProps {
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onOpenMobileMenu: () => void;
}

const WALLET_STORAGE_KEY = 'wallet_address';

function shortenWalletAddress(value: string) {
  if (value.length <= 10) return value;
  return `${value.slice(0, 6)}…${value.slice(-4)}`;
}

function formatUsd(value: number) {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function ShellHeader({
  sidebarCollapsed,
  onToggleSidebar,
  onOpenMobileMenu,
}: ShellHeaderProps) {
  const [walletPanelOpen, setWalletPanelOpen] = useState(false);
  const [walletInput, setWalletInput] = useState(() => localStorage.getItem(WALLET_STORAGE_KEY) ?? '');
  const [depositAmount, setDepositAmount] = useState('25');
  const [manualWalletMode, setManualWalletMode] = useState(false);
  const walletPanelRef = useRef<HTMLDivElement | null>(null);

  const { data: currentUser, isError: userLoadFailed } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getMe,
    retry: false,
    staleTime: 60_000,
  });

  const { data: walletBalance } = useQuery({
    queryKey: ['payments', 'balance', currentUser?.id],
    queryFn: () => paymentsApi.getBalance(currentUser!.id),
    enabled: Boolean(currentUser?.id),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  const depositCharge = useMutation({
    mutationFn: () =>
      paymentsApi.createDepositCharge({
        user_id: currentUser!.id,
        amount: Number(depositAmount),
        redirect_url: window.location.href,
      }),
    onSuccess: (charge) => {
      window.open(charge.hosted_url, '_blank', 'noopener,noreferrer');
    },
  });

  const persistedWalletAddress = useMemo(
    () => localStorage.getItem(WALLET_STORAGE_KEY) ?? '',
    [walletInput],
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!walletPanelRef.current?.contains(event.target as Node)) {
        setWalletPanelOpen(false);
      }
    }

    if (walletPanelOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }

    return undefined;
  }, [walletPanelOpen]);

  function handleWalletSave() {
    const trimmed = walletInput.trim();
    if (!trimmed) {
      localStorage.removeItem(WALLET_STORAGE_KEY);
      setWalletInput('');
      return;
    }

    localStorage.setItem(WALLET_STORAGE_KEY, trimmed);
    setWalletInput(trimmed);
  }

  const canCreateDeposit = Boolean(currentUser?.id) && Number(depositAmount) > 0;
  const walletConnected = Boolean(persistedWalletAddress);

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
        <div className="relative hidden md:block" ref={walletPanelRef}>
          <button
            type="button"
            onClick={() => setWalletPanelOpen((value) => !value)}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 py-2 text-[13px] font-semibold text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
          >
            <Shield className="h-4 w-4 text-[var(--e-purple-500)]" />
            <span>{persistedWalletAddress ? shortenWalletAddress(persistedWalletAddress) : 'Wallet'}</span>
            <ChevronDown className="h-4 w-4 text-[var(--e-text-muted)]" />
          </button>

          {walletPanelOpen ? (
            <div className="absolute right-0 top-[calc(100%+0.75rem)] w-[340px] rounded-xl border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] p-4 shadow-[var(--e-shadow-md)]">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Wallet
                  </div>
                  <div className="mt-1 text-[18px] font-semibold tracking-[-0.02em] text-[var(--e-text-primary)]">
                    Funding & connection
                  </div>
                </div>
                <div className="rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2 py-1 text-[11px] font-medium text-[var(--e-text-muted)]">
                  {walletConnected ? 'Wallet linked' : currentUser?.id ? 'Ready to fund' : 'Identity pending'}
                </div>
              </div>

              <div className="mb-4 rounded-lg border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] p-3">
                <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                  USDC balance
                </div>
                <div className="font-mono text-[24px] font-bold text-[var(--e-text-primary)] tabular-nums">
                  {walletBalance ? formatUsd(walletBalance.balance) : '—'}
                </div>
                <div className="mt-1 text-[12px] text-[var(--e-text-muted)]">
                  {currentUser?.id
                    ? `Loaded for ${currentUser.username}`
                    : 'Sign in is still required for balance-backed funding.'}
                </div>
              </div>

              <div className="mb-4 grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setManualWalletMode((value) => !value)}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
                >
                  <LinkIcon className="h-4 w-4 text-[var(--e-purple-500)]" />
                  {walletConnected ? 'Update wallet' : 'Connect Wallet'}
                </button>
                <button
                  type="button"
                  disabled={!canCreateDeposit || depositCharge.isPending}
                  onClick={() => depositCharge.mutate()}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[var(--e-purple-500)] px-3 text-[12px] font-semibold text-[var(--e-text-inverse)] transition hover:bg-[var(--e-purple-600)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Wallet className="h-4 w-4" />
                  {depositCharge.isPending ? 'Opening…' : 'Add Funds'}
                </button>
              </div>

              {manualWalletMode ? (
                <>
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                    Wallet address
                  </label>
                  <div className="mb-4 flex gap-2">
                    <input
                      type="text"
                      value={walletInput}
                      onChange={(event) => setWalletInput(event.target.value)}
                      placeholder="0x..."
                      className="h-10 flex-1 rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none transition placeholder:text-[var(--e-text-muted)] focus:border-[var(--e-border-focus)] focus:bg-[var(--e-bg-card)]"
                    />
                    <button
                      type="button"
                      onClick={handleWalletSave}
                      className="rounded-md border border-[var(--e-border-primary)] bg-[var(--e-bg-card)] px-3 text-[12px] font-semibold text-[var(--e-text-primary)] transition hover:bg-[var(--e-bg-hover)]"
                    >
                      Save
                    </button>
                  </div>
                </>
              ) : null}

              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]">
                Add funds (USDC)
              </label>
              <div className="mb-3 flex gap-2">
                <input
                  type="number"
                  min="1"
                  max="10000"
                  step="1"
                  value={depositAmount}
                  onChange={(event) => setDepositAmount(event.target.value)}
                  className="h-10 flex-1 rounded-md border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-3 text-[13px] text-[var(--e-text-primary)] outline-none transition focus:border-[var(--e-border-focus)] focus:bg-[var(--e-bg-card)]"
                />
              </div>

              {depositCharge.isError ? (
                <div className="mb-3 rounded-md border border-[var(--e-red-200)] bg-[var(--e-red-50)] px-3 py-2 text-[12px] text-[var(--e-red-600)]">
                  Failed to create deposit charge. Check payments service availability.
                </div>
              ) : null}

              <div className="space-y-2 text-[12px] text-[var(--e-text-muted)]">
                <div className="flex items-start gap-2">
                  <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>
                    Funding uses the live Coinbase Commerce deposit route. Wallet address is optional here and only used
                    as a local identity override until the full connect-wallet flow lands.
                  </span>
                </div>
                {userLoadFailed ? (
                  <div className="rounded-md border border-[var(--e-amber-200)] bg-[var(--e-amber-50)] px-3 py-2 text-[var(--e-amber-700)]">
                    Account sign-in is not available from the shell yet, so balance-backed funding only works for existing signed-in sessions.
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

export default ShellHeader;
