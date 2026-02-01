/**
 * Demo Mode Detection
 * 
 * Handles demo mode enablement via environment variable,
 * localStorage persistence, and URL query parameters.
 */

const LS_KEY = "echelon_demo_mode"; // "1" | "0"

export function isDemoModeEnabled(): boolean {
  const envOn = String((import.meta as any).env?.VITE_DEMO_MODE ?? "") === "true";
  if (typeof window === "undefined") return envOn;

  const ls = window.localStorage.getItem(LS_KEY);
  if (ls === "1") return true;
  if (ls === "0") return false;
  return envOn;
}

export function applyDemoModeQueryParam(): void {
  if (typeof window === "undefined") return;

  const url = new URL(window.location.href);
  const demo = url.searchParams.get("demo");
  if (demo !== "1" && demo !== "0") return;

  window.localStorage.setItem(LS_KEY, demo);
  url.searchParams.delete("demo");
  window.history.replaceState({}, "", url.toString());
}
