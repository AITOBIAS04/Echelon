import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Temporarily disable StrictMode to prevent double rendering in development
// This helps debug if multiple paradox alerts are being rendered
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
