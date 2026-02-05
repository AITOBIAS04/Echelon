import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopActionBar } from './TopActionBar';
import { TopActionBarActionsProvider } from '../../contexts/TopActionBarActionsContext';
import { AgentsUiProvider } from '../../contexts/AgentsUiContext';
import { DemoEngine } from '../../demo/DemoEngine';
import { DemoToastHost } from '../../demo/DemoToastHost';

export function AppLayout() {
  return (
    <TopActionBarActionsProvider>
      <AgentsUiProvider>
        <DemoEngine>
          <DemoToastHost />
          <div className="h-[100dvh] w-screen flex overflow-hidden bg-slate-950">
            {/* Persistent left sidebar */}
            <Sidebar />

            {/* Main area: top action bar + viewport */}
            <section className="flex-1 flex flex-col min-w-0 h-[100dvh]">
              <TopActionBar />

              {/* Viewport — each page fills this area and manages its own scroll */}
              <div className="flex-1 min-h-0 relative bg-slate-950 overflow-auto">
                <Outlet />
              </div>
            </section>
          </div>
        </DemoEngine>
      </AgentsUiProvider>
    </TopActionBarActionsProvider>
  );
}
