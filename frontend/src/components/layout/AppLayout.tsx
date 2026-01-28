import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopActionBar } from './TopActionBar';
import { TopActionBarActionsProvider } from '../../contexts/TopActionBarActionsContext';

export function AppLayout() {
  return (
    <TopActionBarActionsProvider>
      <div className="h-[100dvh] w-screen flex overflow-hidden bg-[#0B0C0E]">
        {/* Persistent left sidebar */}
        <Sidebar />

        {/* Main area: top action bar + viewport */}
        <section className="flex-1 flex flex-col min-w-0 h-[100dvh]">
          <TopActionBar />

          {/* Viewport — each page fills this area and manages its own scroll */}
          <div className="flex-1 min-h-0 relative bg-[#0B0C0E] overflow-auto">
            <Outlet />
          </div>
        </section>
      </div>
    </TopActionBarActionsProvider>
  );
}
