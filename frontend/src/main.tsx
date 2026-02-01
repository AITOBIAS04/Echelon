import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { applyDemoModeQueryParam } from './demo/demoMode';

// Apply demo mode query param before rendering
applyDemoModeQueryParam();

// RouterProvider is already used in App.tsx, so we don't need BrowserRouter here
const root = ReactDOM.createRoot(document.getElementById('root')!);
if (import.meta.env.DEV) {
  // Development: Render without StrictMode to avoid double renders
  root.render(<App />);
} else {
  // Production: Use StrictMode
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
