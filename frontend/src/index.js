import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from 'react-router-dom';
import App from "./App.js";

function ErrorBoundary({ children }) {
  const [error, setError] = React.useState(null);
  if (error) return <div style={{padding:24, color:'#b91c1c'}}>Render error: {String(error)}</div>;
  return (
    <React.Suspense fallback={<div style={{padding:24}}>Loading…</div>}>
      <React.StrictMode>
        {children}
      </React.StrictMode>
    </React.Suspense>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
console.log('[index] App =', App);
root.render(
  <BrowserRouter>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </BrowserRouter>
);

console.log('[index] mounting root');
console.log('[index] App =', App);

// Support both Vite (VITE_API_BASE) and CRA (REACT_APP_API_BASE).
const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE)
  || (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE)
  || '';

function buildUrl(path) {
  if (/^https?:\/\//i.test(path)) return path; // already absolute
  if (!API_BASE) return path; // same-origin (served by Django) or dev proxy configured
  // Ensure exactly one slash between base and path
  return API_BASE.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
}

async function ensureCsrf() {
  await fetch(buildUrl('/api/csrf/'), { credentials: 'include' });
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(buildUrl(path), opts);
  if (res.status === 403) {
    await ensureCsrf();
    const retryRes = await fetch(buildUrl(path), opts);
    return retryRes;
  }
  return res;
}