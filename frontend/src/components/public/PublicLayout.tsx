import { Outlet } from 'react-router-dom';
import { PublicNav } from './PublicNav';
import { PublicFooter } from './PublicFooter';
import '../../styles/public.css';

/**
 * PublicLayout — Shell for unauthenticated public pages.
 * No sidebar. No operator header. Just nav + content + footer.
 * Wraps content in .public-shell for scoped design tokens.
 */
export function PublicLayout() {
  return (
    <div className="public-shell">
      <PublicNav />
      <main>
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
}
