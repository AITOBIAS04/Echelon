import { useEffect, useRef, useCallback } from 'react';
import type { CanvasMode, ViewState } from '../../hooks/useWorkspaceState';
import {
  GLOBE_DEFAULT_VIEW,
  GLOBE_SCOPE_VIEW,
  GLOBE_TO_SCOPED_ALTITUDE,
} from '../../hooks/useWorkspaceState';
import { useWorldMonitorLive } from '../../hooks/useWorldMonitorLive';

interface GlobeCanvasProps {
  mode: CanvasMode;
  onScopeTransition: (viewState: ViewState) => void;
}

// Signal points for globe markers (synthetic Path 2 data)
const FALLBACK_SIGNAL_POINTS = [
  { lat: 29.9, lng: 32.55, size: 0.06, color: 'rgba(168,85,247,0.92)', label: 'Suez corridor', meta: 'Maritime evidence' },
  { lat: 12.78, lng: 43.15, size: 0.055, color: 'rgba(168,85,247,0.88)', label: 'Bab-el-Mandeb', meta: 'Conflict chatter' },
  { lat: 21.49, lng: 39.17, size: 0.045, color: 'rgba(74,222,128,0.9)', label: 'Jeddah certified', meta: 'Certificate candidate' },
  { lat: 12.8, lng: 45.03, size: 0.04, color: 'rgba(74,222,128,0.85)', label: 'Gulf of Aden', meta: 'Routing confirmation' },
  { lat: 25.28, lng: 55.3, size: 0.035, color: 'rgba(251,191,36,0.88)', label: 'Dubai SIGINT', meta: 'Behavioural cluster' },
  { lat: 1.35, lng: 103.82, size: 0.04, color: 'rgba(251,191,36,0.85)', label: 'Singapore hub', meta: 'AIS corridor' },
  { lat: 35.69, lng: 139.69, size: 0.03, color: 'rgba(174,180,191,0.7)', label: 'Tokyo inferred', meta: 'Market data' },
  { lat: 51.51, lng: -0.13, size: 0.035, color: 'rgba(174,180,191,0.72)', label: 'London inferred', meta: 'GDELT context' },
  { lat: 40.71, lng: -74.01, size: 0.033, color: 'rgba(174,180,191,0.68)', label: 'New York inferred', meta: 'Market signal' },
];

const FALLBACK_ARC_SIGNALS = [
  { startLat: 29.9, startLng: 32.55, endLat: 12.78, endLng: 43.15, color: ['rgba(168,85,247,0.7)', 'rgba(168,85,247,0.1)'] },
  { startLat: 1.35, startLng: 103.82, endLat: 21.49, endLng: 39.17, color: ['rgba(74,222,128,0.6)', 'rgba(74,222,128,0.1)'] },
  { startLat: 25.28, startLng: 55.3, endLat: 29.9, endLng: 32.55, color: ['rgba(251,191,36,0.7)', 'rgba(251,191,36,0.1)'] },
  { startLat: 51.51, startLng: -0.13, endLat: 25.28, endLng: 55.3, color: ['rgba(174,180,191,0.5)', 'rgba(174,180,191,0.1)'] },
  { startLat: 29.9, startLng: 32.55, endLat: -33.86, endLng: 151.2, color: ['rgba(251,191,36,0.8)', 'rgba(251,191,36,0.1)'] },
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GlobeInstance = any;

export function GlobeCanvas({ mode, onScopeTransition }: GlobeCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeInstance>(null);
  const modeRef = useRef(mode);
  const onScopeRef = useRef(onScopeTransition);
  const zoomIntentRef = useRef(false);
  const zoomIntentTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const buildAttempt = useRef(0);

  // Keep refs current so closures see fresh values
  modeRef.current = mode;
  onScopeRef.current = onScopeTransition;

  const { data: liveData } = useWorldMonitorLive();

  const signalPoints = liveData?.signals?.length
    ? liveData.signals.slice(0, 12).map((s) => ({
        lat: s.geo.lat,
        lng: s.geo.lon,
        size: 0.03 + Math.min(s.level * 0.006, 0.04),
        color: s.severity === 'critical'
          ? 'rgba(168,85,247,0.92)'
          : s.severity === 'high'
            ? 'rgba(74,222,128,0.9)'
            : 'rgba(251,191,36,0.88)',
        label: s.title,
        meta: s.source,
      }))
    : FALLBACK_SIGNAL_POINTS;

  const arcSignals = FALLBACK_ARC_SIGNALS;

  const markZoomIntent = useCallback(() => {
    zoomIntentRef.current = true;
    if (zoomIntentTimer.current) clearTimeout(zoomIntentTimer.current);
    zoomIntentTimer.current = setTimeout(() => {
      zoomIntentRef.current = false;
    }, 1100);
  }, []);

  const scheduleAutoRotate = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => {
      if (globeRef.current?.controls()) {
        globeRef.current.controls().autoRotate = modeRef.current === 'global';
      }
    }, 1400);
  }, []);

  // Build globe (once, after layout is stable)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let cancelled = false;
    let rafId: number;

    async function build() {
      // Dynamic import — loads globe.gl chunk
      const GlobeModule = await import('globe.gl');
      const Globe = GlobeModule.default ?? GlobeModule;
      if (cancelled || !container) return;

      // Wait one frame so the browser has finished layout
      await new Promise<void>((resolve) => {
        rafId = requestAnimationFrame(() => resolve());
      });
      if (cancelled) return;

      const width = container.clientWidth;
      const height = container.clientHeight;

      if (!width || !height) {
        console.warn('[GlobeCanvas] container has zero dimensions:', width, height);
        // Retry after a short delay — parent layout may not be ready
        buildAttempt.current += 1;
        if (buildAttempt.current < 5) {
          setTimeout(build, 200);
        }
        return;
      }

      const isLight = document.documentElement.classList.contains('light');
      const textureUrl = isLight
        ? 'https://unpkg.com/three-globe/example/img/earth-day.jpg'
        : 'https://unpkg.com/three-globe/example/img/earth-night.jpg';

      const theme = isLight
        ? { atmosphere: '#a8c8e6', atmosphereAltitude: 0.14, surface: '#c4d0dc', emissive: '#a8b8c6', emissiveIntensity: 0.06 }
        : { atmosphere: '#1a3d5c', atmosphereAltitude: 0.18, surface: '#0c3e5c', emissive: '#1a3d5c', emissiveIntensity: 0.14 };

      try {
        // Phase 1: construct with layout-only props.
        // Animation loop starts immediately — atmosphere/material/data MUST
        // wait for onGlobeReady or the loop reads null material.opacity.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const globe: any = new Globe(container)
          .backgroundColor('rgba(0,0,0,0)')
          .width(width)
          .height(height)
          .globeImageUrl(textureUrl)
          .onGlobeReady(() => {
            if (cancelled) return;

            // Phase 2: Three.js scene is now initialised — safe to configure
            globe
              .showAtmosphere(true)
              .atmosphereColor(theme.atmosphere)
              .atmosphereAltitude(theme.atmosphereAltitude)
              .pointsData(signalPoints)
              .pointLat('lat')
              .pointLng('lng')
              .pointAltitude((d: any) => d.size)
              .pointRadius((d: any) => d.size * 0.9)
              .pointColor('color')
              .pointResolution(18)
              .arcsData(arcSignals)
              .arcStartLat('startLat')
              .arcStartLng('startLng')
              .arcEndLat('endLat')
              .arcEndLng('endLng')
              .arcColor('color')
              .arcAltitude(0.2)
              .arcStroke(0.6)
              .arcDashLength(0.45)
              .arcDashGap(0.8)
              .arcDashAnimateTime(2200)
              .ringsData(signalPoints.slice(0, 6))
              .ringColor((d: any) => (t: number) =>
                d.color.replace(')', `,${1 - t})`).replace('rgb', 'rgba')
              )
              .ringMaxRadius((d: any) => 4 + d.size * 16)
              .ringPropagationSpeed(1.6)
              .ringRepeatPeriod(1100);

            const material = globe.globeMaterial();
            material.color.set(theme.surface);
            material.emissive.set(theme.emissive);
            material.emissiveIntensity = theme.emissiveIntensity;
            material.shininess = isLight ? 0.02 : 0.34;

            const controls = globe.controls();
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.32;
            controls.enablePan = false;
            controls.minDistance = width < 500 ? 155 : 180;
            controls.maxDistance = width < 500 ? 420 : 520;
            controls.enableDamping = true;
            controls.dampingFactor = 0.08;

            globe.pointOfView(
              modeRef.current === 'scoped' ? GLOBE_SCOPE_VIEW : GLOBE_DEFAULT_VIEW,
              0,
            );

            globe.onPointClick((point: any) => {
              if (!point) return;
              onScopeRef.current({ center: [point.lng, point.lat], zoom: 5.4 });
            });

            globe.onPointHover((point: any) => {
              container.style.cursor = point ? 'pointer' : 'grab';
            });

            // Zoom-in detection polling (reads modeRef to avoid stale closure)
            pollRef.current = setInterval(() => {
              if (modeRef.current !== 'global' || !zoomIntentRef.current) return;
              const pov = globe.pointOfView();
              if (pov?.altitude <= GLOBE_TO_SCOPED_ALTITUDE) {
                zoomIntentRef.current = false;
                onScopeRef.current({ center: [pov.lng, pov.lat], zoom: 4.8 });
              }
            }, 180);

            container.addEventListener('wheel', markZoomIntent);
            container.addEventListener('pointerdown', () => {
              if (controls) controls.autoRotate = false;
            });
            container.addEventListener('pointerup', scheduleAutoRotate);

            globeRef.current = globe;
          });
      } catch (err) {
        console.warn('[GlobeCanvas] build attempt failed:', err);
        buildAttempt.current += 1;
        if (buildAttempt.current < 5) {
          setTimeout(build, 300);
        }
      }
    }

    build();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      if (pollRef.current) clearInterval(pollRef.current);
      if (globeRef.current) {
        const renderer = globeRef.current.renderer?.();
        if (renderer) renderer.dispose();
        globeRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update globe camera when mode changes
  useEffect(() => {
    const globe = globeRef.current;
    if (!globe) return;

    const controls = globe.controls();
    if (mode === 'global') {
      globe.pointOfView(GLOBE_DEFAULT_VIEW, 720);
      setTimeout(() => {
        if (controls) controls.autoRotate = true;
      }, 1400);
    } else {
      globe.pointOfView(GLOBE_SCOPE_VIEW, 720);
      if (controls) controls.autoRotate = false;
    }
  }, [mode]);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver(() => {
      const globe = globeRef.current;
      if (globe) {
        globe.width(container.clientWidth);
        globe.height(container.clientHeight);
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-0"
      data-globe-canvas
      style={{
        width: '100%',
        height: '100%',
        opacity: mode === 'global' ? 1 : 0.3,
        transition: 'opacity 0.6s ease-out',
        pointerEvents: mode === 'global' ? 'auto' : 'none',
      }}
    />
  );
}
