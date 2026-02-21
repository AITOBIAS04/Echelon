import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopActionBar } from './TopActionBar';
import { TopActionBarActionsProvider } from '../../contexts/TopActionBarActionsContext';
import { AgentsUiProvider } from '../../contexts/AgentsUiContext';
import { RlmfUiProvider } from '../../contexts/RlmfUiContext';
import { VerifyUiProvider } from '../../contexts/VerifyUiContext';
import { DemoEngine } from '../../demo/DemoEngine';
import { DemoToastHost } from '../../demo/DemoToastHost';

export function AppLayout() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
            <div className="h-[100dvh] w-screen flex overflow-hidden bg-terminal-bg canary-active">
              {/* Persistent left sidebar (desktop) + mobile drawer */}
              <Sidebar
                mobileOpen={mobileMenuOpen}
                onMobileClose={() => setMobileMenuOpen(false)}
              />

              {/* Main area: top action bar + viewport */}
              <section className="flex-1 flex flex-col min-w-0 h-[100dvh]">
                <TopActionBar onHamburgerClick={() => setMobileMenuOpen(true)} />

                {/* Viewport — each page fills this area and manages its own scroll */}
                <div className="flex-1 min-h-0 relative bg-terminal-bg overflow-auto">
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
