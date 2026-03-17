import { useEffect, useRef, useCallback } from 'react';
import { feature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
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

// Globe theme colours — high-opacity polygon fills since there's no
// raster texture underneath. Land needs to read as solid geography.
const GLOBE_THEMES = {
  light: {
    surface: '#f5f5f5',
    emissive: '#f0f0f0',
    emissiveIntensity: 0.02,
    shininess: 0.02,
    polygonCap: 'rgba(26,28,33,0.82)',
    polygonSide: 'rgba(26,28,33,0.60)',
    polygonStroke: 'rgba(50,54,62,0.45)',
    polygonAltitude: 0,
    atmosphere: '#d8d4ee',
    atmosphereAltitude: 0.03,
  },
  dark: {
    surface: '#0a0a0f',
    emissive: '#10131b',
    emissiveIntensity: 0.25,
    shininess: 0.30,
    polygonCap: 'rgba(220,225,235,0.65)',
    polygonSide: 'rgba(220,225,235,0.40)',
    polygonStroke: 'rgba(180,185,200,0.40)',
    polygonAltitude: 0,
    atmosphere: '#4a4080',
    atmosphereAltitude: 0.12,
  },
} as const;

const WORLD_ATLAS_URL = 'https://unpkg.com/world-atlas@2/countries-110m.json';

// Generate a 1x1 pixel data URL of a given colour.
// Used as globe surface texture — globe.gl's own API manages the texture lifecycle,
// so we swap data URLs instead of fighting material.map directly.
function createColorDataUrl(hex: string): string {
  const c = document.createElement('canvas');
  c.width = 1;
  c.height = 1;
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = hex;
  ctx.fillRect(0, 0, 1, 1);
  return c.toDataURL();
}

// Pre-generate themed globe surface textures
const GLOBE_TEXTURE_LIGHT = createColorDataUrl(GLOBE_THEMES.light.surface);
const GLOBE_TEXTURE_DARK = createColorDataUrl(GLOBE_THEMES.dark.surface);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GlobeInstance = any;

// Cache country features across builds
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let countriesCache: any[] | null = null;

async function loadCountries() {
  if (countriesCache) return countriesCache;
  const res = await fetch(WORLD_ATLAS_URL);
  const topo = (await res.json()) as Topology<{ countries: GeometryCollection }>;
  const geo = feature(topo, topo.objects.countries);
  countriesCache = geo.features;
  return countriesCache;
}

function getTheme() {
  const isLight = document.documentElement.classList.contains('light');
  return isLight ? GLOBE_THEMES.light : GLOBE_THEMES.dark;
}

function getThemedTextureUrl() {
  const isLight = document.documentElement.classList.contains('light');
  return isLight ? GLOBE_TEXTURE_LIGHT : GLOBE_TEXTURE_DARK;
}

/**
 * Re-apply all theme-dependent globe properties. Called on init + theme toggle.
 *
 * Uses globe.gl's own `globeImageUrl` API for surface colour — this lets
 * globe.gl manage the Three.js texture lifecycle internally, avoiding the race
 * where our `material.map = null` gets overwritten by globe.gl's internal update.
 *
 * For polygons, a two-phase clear → repopulate forces Kapsule to re-evaluate
 * all accessor functions with the new theme values.
 */
function applyGlobeTheme(globe: GlobeInstance) {
  const theme = getTheme();

  // 1. Swap globe surface via official API — globe.gl handles texture internally
  globe.globeImageUrl(getThemedTextureUrl());

  // 2. Update polygon accessor functions with new theme values
  globe
    .polygonCapColor(() => theme.polygonCap)
    .polygonSideColor(() => theme.polygonSide)
    .polygonStrokeColor(() => theme.polygonStroke)
    .polygonAltitude(() => theme.polygonAltitude)
    .atmosphereColor(theme.atmosphere)
    .atmosphereAltitude(theme.atmosphereAltitude);

  // 3. Two-phase polygon reset: clear then repopulate on next frame.
  //    This guarantees Kapsule sees a genuine remove-all + add-all cycle,
  //    forcing every accessor function to be re-evaluated per data item.
  //    The single-spread `[...data]` approach was insufficient because
  //    Kapsule may short-circuit when element references are identical.
  const data = globe.polygonsData();
  if (data?.length) {
    globe.polygonsData([]);
    requestAnimationFrame(() => {
      globe.polygonsData(data);
      // Re-apply polygon offset after data is repopulated
      applyPolygonOffset(globe);
    });
  }

  // 4. Fine-tune Three.js material (emissive glow, shininess).
  //    Don't touch material.map or material.color — globeImageUrl owns those.
  try {
    const material = globe.globeMaterial();
    material.emissive.set(theme.emissive);
    material.emissiveIntensity = theme.emissiveIntensity;
    material.shininess = theme.shininess;
    material.needsUpdate = true;
  } catch (_) {
    // Material not ready yet — next theme toggle will catch it
  }
}

/**
 * Traverse the Three.js scene and enable polygonOffset on polygon meshes.
 * This pushes polygon surfaces slightly back in the depth buffer, so arcs
 * and signal points always render in front — even at arc endpoints where
 * both polygon and arc geometry are at the same altitude (surface level).
 *
 * Identifies polygon meshes by geometry type: three-globe creates country
 * polygons using ConicPolygonGeometry or similar extruded shapes, while
 * arcs use TubeGeometry and points use CylinderGeometry.
 */
function applyPolygonOffset(globe: GlobeInstance) {
  try {
    const scene = globe.scene();
    scene.traverse((obj: any) => {
      if (!obj.isMesh || !obj.material) return;
      const geoType = obj.geometry?.type ?? '';
      // Polygon/Conic/GeoJson geometries = country polygon meshes
      // BufferGeometry with many vertices near the globe surface = also polygons
      const isPolygonMesh =
        geoType.includes('Conic') ||
        geoType.includes('Polygon') ||
        geoType.includes('GeoJson') ||
        geoType.includes('Shape') ||
        geoType.includes('Extrude');
      if (isPolygonMesh) {
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        mats.forEach((m: any) => {
          m.polygonOffset = true;
          m.polygonOffsetFactor = 1;
          m.polygonOffsetUnits = 1;
          m.needsUpdate = true;
        });
      }
    });
  } catch (_) {
    // Scene not ready — safe to skip
  }
}

export function GlobeCanvas({ mode, onScopeTransition }: GlobeCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeInstance>(null);
  const modeRef = useRef(mode);
  const onScopeRef = useRef(onScopeTransition);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const buildAttempt = useRef(0);
  const themeObserverRef = useRef<MutationObserver | null>(null);
  // Transition lock prevents rapid-fire globe→scoped triggers
  const transitionLockRef = useRef(false);

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
    let zoomRafId: number;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let wheelHandler: any = null;

    async function build() {
      const [GlobeModule, countries] = await Promise.all([
        import('globe.gl'),
        loadCountries(),
      ]);
      const Globe = GlobeModule.default ?? GlobeModule;
      if (cancelled || !container) return;

      await new Promise<void>((resolve) => {
        rafId = requestAnimationFrame(() => resolve());
      });
      if (cancelled) return;

      const width = container.clientWidth;
      const height = container.clientHeight;

      if (!width || !height) {
        console.warn('[GlobeCanvas] container has zero dimensions:', width, height);
        buildAttempt.current += 1;
        if (buildAttempt.current < 5) {
          setTimeout(build, 200);
        }
        return;
      }

      const theme = getTheme();

      try {
        // Phase 1: construct with layout + themed texture.
        // showAtmosphere(false) prevents null material.opacity tween crash.
        // globeImageUrl(themed) prevents default satellite texture from loading.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const globe: any = new Globe(container)
          .showAtmosphere(false)
          .backgroundColor('rgba(0,0,0,0)')
          .globeImageUrl(getThemedTextureUrl())
          .width(width)
          .height(height)
          .onGlobeReady(() => {
            if (cancelled) return;

            // Phase 2: Three.js scene ready — safe to configure everything.
            globe
              .showAtmosphere(true)
              .atmosphereColor(theme.atmosphere)
              .atmosphereAltitude(theme.atmosphereAltitude)
              // Country polygons — altitude 0 = flat (no extrusion side walls)
              .polygonsData(countries)
              .polygonAltitude(() => theme.polygonAltitude)
              .polygonCapColor(() => theme.polygonCap)
              .polygonSideColor(() => theme.polygonSide)
              .polygonStrokeColor(() => theme.polygonStroke)
              // Signal points — raised well above polygon surface
              .pointsData(signalPoints)
              .pointLat('lat')
              .pointLng('lng')
              .pointAltitude((d: any) => 0.12 + d.size)
              .pointRadius((d: any) => d.size * 0.9)
              .pointColor('color')
              .pointResolution(18)
              // Arcs — peak altitude raised to clear polygon depth
              .arcsData(arcSignals)
              .arcStartLat('startLat')
              .arcStartLng('startLng')
              .arcEndLat('endLat')
              .arcEndLng('endLng')
              .arcColor('color')
              .arcAltitude(0.35)
              .arcStroke(0.6)
              .arcDashLength(0.45)
              .arcDashGap(0.8)
              .arcDashAnimateTime(2200)
              // Rings
              .ringsData(signalPoints.slice(0, 6))
              .ringColor((d: any) => (t: number) =>
                d.color.replace(')', `,${1 - t})`).replace('rgb', 'rgba')
              )
              .ringMaxRadius((d: any) => 4 + d.size * 16)
              .ringPropagationSpeed(1.6)
              .ringRepeatPeriod(1100);

            // Apply theme to material (emissive glow, shininess)
            applyGlobeTheme(globe);

            // Apply polygon offset for z-order after meshes are built
            requestAnimationFrame(() => {
              applyPolygonOffset(globe);
            });

            // Orbit controls
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

            // ── Zoom-in detection ────────────────────────────────────
            // Two complementary mechanisms:
            // 1. rAF loop — checks altitude every frame (covers all interactions)
            // 2. wheel listener — explicit check after mouse wheel zoom

            function triggerScopeTransition(pov: { lat: number; lng: number }) {
              transitionLockRef.current = true;
              onScopeRef.current({ center: [pov.lng, pov.lat], zoom: 4.8 });
              setTimeout(() => {
                transitionLockRef.current = false;
              }, 1200);
            }

            function checkAltitudeThreshold(): boolean {
              if (modeRef.current !== 'global' || transitionLockRef.current) return false;
              try {
                const pov = globe.pointOfView();
                if (pov && pov.altitude <= GLOBE_TO_SCOPED_ALTITUDE) {
                  triggerScopeTransition(pov);
                  return true;
                }
              } catch (_) {
                // globe not ready
              }
              return false;
            }

            // Mechanism 1: rAF poll
            function checkZoomLoop() {
              if (cancelled) return;
              checkAltitudeThreshold();
              zoomRafId = requestAnimationFrame(checkZoomLoop);
            }
            zoomRafId = requestAnimationFrame(checkZoomLoop);

            // Mechanism 2: wheel event with delayed check
            wheelHandler = () => {
              // Delay lets OrbitControls finish processing the zoom
              setTimeout(() => checkAltitudeThreshold(), 80);
            };
            container.addEventListener('wheel', wheelHandler, { passive: true });

            container.addEventListener('pointerdown', () => {
              if (controls) controls.autoRotate = false;
            });
            container.addEventListener('pointerup', scheduleAutoRotate);

            globeRef.current = globe;

            // Watch for theme toggle (MutationObserver on <html> class)
            themeObserverRef.current = new MutationObserver(() => {
              if (globeRef.current) {
                applyGlobeTheme(globeRef.current);
              }
            });
            themeObserverRef.current.observe(document.documentElement, {
              attributes: true,
              attributeFilter: ['class'],
            });
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
      cancelAnimationFrame(zoomRafId);
      if (wheelHandler && containerRef.current) {
        containerRef.current.removeEventListener('wheel', wheelHandler);
      }
      if (themeObserverRef.current) themeObserverRef.current.disconnect();
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
      // Lock transitions while animating back to default view
      transitionLockRef.current = true;
      globe.pointOfView(GLOBE_DEFAULT_VIEW, 720);
      setTimeout(() => {
        if (controls) controls.autoRotate = true;
        transitionLockRef.current = false;
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
