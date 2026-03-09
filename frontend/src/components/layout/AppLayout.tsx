import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { ShellHeader } from './ShellHeader';
import { TopActionBar } from './TopActionBar';
import { TopActionBarActionsProvider } from '../../contexts/TopActionBarActionsContext';
import { AgentsUiProvider } from '../../contexts/AgentsUiContext';
import { RlmfUiProvider } from '../../contexts/RlmfUiContext';
import { VerifyUiProvider } from '../../contexts/VerifyUiContext';
import { DemoEngine } from '../../demo/DemoEngine';
import { DemoToastHost } from '../../demo/DemoToastHost';
import { useRealtimeInvalidation } from '../../hooks/useRealtimeInvestigation';

export function AppLayout() {
  // WebSocket → TanStack Query bridge (platform-wide real-time updates)
  useRealtimeInvalidation('platform');
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <TopActionBarActionsProvider>
      <AgentsUiProvider>
        <RlmfUiProvider>
          <VerifyUiProvider>
          <DemoEngine>
            <DemoToastHost />
            <div className="min-h-[100dvh] w-screen bg-[var(--e-bg-app)] text-[var(--e-text-primary)]">
              <ShellHeader
                sidebarCollapsed={sidebarCollapsed}
                onToggleSidebar={() => setSidebarCollapsed((value) => !value)}
                onOpenMobileMenu={() => setMobileMenuOpen(true)}
              />

              <Sidebar
                collapsed={sidebarCollapsed}
                mobileOpen={mobileMenuOpen}
                onMobileClose={() => setMobileMenuOpen(false)}
              />

              <section
                className={`flex min-h-[100dvh] min-w-0 flex-col pt-14 transition-[margin] duration-300 ease-out ${
                  sidebarCollapsed ? 'md:ml-16' : 'md:ml-60'
                }`}
              >
                <TopActionBar onHamburgerClick={() => setMobileMenuOpen(true)} />

                <div className="relative flex-1 overflow-auto bg-[var(--e-bg-app)]">
                  <div key={location.pathname} className="page-enter h-full">
                    <Outlet />
                  </div>
                </div>
              </section>
            </div>
          </DemoEngine>
          </VerifyUiProvider>
        </RlmfUiProvider>
      </AgentsUiProvider>
    </TopActionBarActionsProvider>
  );
}
