import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { StepIndicator } from './StepIndicator';

export function Shell() {
  return (
    <div className="mx-auto max-w-container px-8">
      <Header />
      <StepIndicator />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
