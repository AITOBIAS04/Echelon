import { useEffect, useRef, useCallback, useState } from 'react';
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
    surface: '#bfc3cd',          // silver ocean
    emissive: '#b8bcc6',
    emissiveIntensity: 0.04,
    shininess: 0.12,
    polygonCap: 'rgba(243,243,246,0.90)',    // white land — matches page background
    polygonSide: 'rgba(243,243,246,0.70)',
    polygonStroke: 'rgba(180,184,195,0.35)', // subtle silver border
    polygonAltitude: 0,          // flush with surface — don't occlude signal points
    atmosphere: '#c8c0e8',
    atmosphereAltitude: 0.10,
  },
  dark: {
    surface: '#1a1b22',          // matches --e-bg-app dark (oklch 0.145 0.008 265)
    emissive: '#1e2030',
    emissiveIntensity: 0.30,
    shininess: 0.25,
    polygonCap: 'rgba(140,148,168,0.45)',    // soft grey land — same sleek language
    polygonSide: 'rgba(140,148,168,0.28)',
    polygonStroke: 'rgba(120,128,148,0.22)',
    polygonAltitude: 0,          // flush with surface — don't occlude signal points
    atmosphere: '#5848a0',
    atmosphereAltitude: 0.20,
  },
} as const;

const WORLD_ATLAS_URL = 'https://unpkg.com/world-atlas@2/countries-110m.json';

// 1x1 white pixel PNG — fed to globeImageUrl at construction ONLY to prevent
// three-globe from loading its built-in default satellite texture.
// After onGlobeReady, we take over material colours directly via Three.js.
const BLANK_GLOBE_TEXTURE =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12P4////DwAJBgMBBYtFSQAAAABJRU5ErkJggg==';

// three-globe uses GLOBE_RADIUS = 100 internally
const GLOBE_RADIUS = 100;

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

/**
 * Apply solid surface colour + emissive glow directly to the Three.js material.
 *
 * We do NOT use globe.globeImageUrl() for theme switching because three-globe's
 * async TextureLoader callback (three-globe.mjs:699-714) sets:
 *   globeMaterial.map = texture;
 *   globeMaterial.color = null;
 * which wipes any color we set. Instead, we bypass globe.gl entirely:
 * dispose the texture map and set material.color as a solid fill.
 */
function applyMaterialTheme(globe: GlobeInstance, theme: (typeof GLOBE_THEMES)[keyof typeof GLOBE_THEMES]) {
  try {
    const material = globe.globeMaterial();

    // Strip the blank texture — we want solid-colour rendering
    if (material.map) {
      material.map.dispose();
      material.map = null;
    }

    // three-globe's texture load sets material.color = null.
    // Recreate it from emissive's constructor (which IS a THREE.Color).
    if (!material.color) {
      const ColorCtor = material.emissive.constructor;
      material.color = new ColorCtor(theme.surface);
    } else {
      material.color.set(theme.surface);
    }

    material.emissive.set(theme.emissive);
    material.emissiveIntensity = theme.emissiveIntensity;
    material.shininess = theme.shininess;

    // Push the globe SURFACE back in the depth buffer so polygon meshes
    // (land masses) always win the z-test. Without this, islands z-fight
    // against the sphere and flash between surface colour and polygon colour.
    material.polygonOffset = true;
    material.polygonOffsetFactor = 4;
    material.polygonOffsetUnits = 4;

    material.needsUpdate = true;
  } catch (_) {
    // material not ready
  }
}

/**
 * Full theme application: polygon accessors + data reset + material colours.
 *
 * For polygons, a two-phase clear → repopulate forces Kapsule to re-evaluate
 * all accessor functions with the new theme values.
 */
function applyGlobeTheme(globe: GlobeInstance) {
  const theme = getTheme();

  // 1. Update polygon accessor functions
  globe
    .polygonCapColor(() => theme.polygonCap)
    .polygonSideColor(() => theme.polygonSide)
    .polygonStrokeColor(() => theme.polygonStroke)
    .polygonAltitude(() => theme.polygonAltitude)
    .atmosphereColor(theme.atmosphere)
    .atmosphereAltitude(theme.atmosphereAltitude);

  // 2. Force Kapsule to re-evaluate accessor functions by passing a new
  //    array reference. Previous two-phase clear→repopulate caused a visible
  //    one-frame flash (all land disappeared then reappeared).
  const data = globe.polygonsData();
  if (data?.length) {
    globe.polygonsData([...data]);
  }

  // 3. Direct Three.js material manipulation — applied NOW and next frame
  //    (next-frame re-apply guards against Kapsule overwriting our changes)
  applyMaterialTheme(globe, theme);
  requestAnimationFrame(() => applyMaterialTheme(globe, theme));
}

export function GlobeCanvas({ mode, onScopeTransition }: GlobeCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeInstance>(null);
  const modeRef = useRef(mode);
  const onScopeRef = useRef(onScopeTransition);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const buildAttempt = useRef(0);
  const themeObserverRef = useRef<MutationObserver | null>(null);
  const transitionLockRef = useRef(false);
  const [isLight, setIsLight] = useState(
    () => document.documentElement.classList.contains('light'),
  );

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
        // Phase 1: construct with layout + blank texture.
        // showAtmosphere(false) prevents null material.opacity tween crash.
        // globeImageUrl(BLANK) prevents default satellite texture from loading.
        // We take over material colours in onGlobeReady via applyMaterialTheme.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const globe: any = new Globe(container)
          .showAtmosphere(false)
          .backgroundColor('rgba(0,0,0,0)')
          .globeImageUrl(BLANK_GLOBE_TEXTURE)
          .width(width)
          .height(height)
          .onGlobeReady(() => {
            if (cancelled) return;

            // Phase 2: Three.js scene ready — configure data layers.
            globe
              .showAtmosphere(true)
              .atmosphereColor(theme.atmosphere)
              .atmosphereAltitude(theme.atmosphereAltitude)
              // Country polygons — altitude 0.001 keeps land just above surface
              .polygonsData(countries)
              .polygonAltitude(() => theme.polygonAltitude)
              .polygonCapColor(() => theme.polygonCap)
              .polygonSideColor(() => theme.polygonSide)
              .polygonStrokeColor(() => theme.polygonStroke)
              // Signal points — well above polygon surface
              .pointsData(signalPoints)
              .pointLat('lat')
              .pointLng('lng')
              .pointAltitude((d: any) => 0.15 + d.size)
              .pointRadius((d: any) => d.size * 0.9)
              .pointColor('color')
              .pointResolution(18)
              // Arcs — peak altitude well above polygons
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

            // Apply theme colours directly to Three.js material
            applyMaterialTheme(globe, theme);

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
            // globe.pointOfView() may return CACHED values that don't
            // reflect OrbitControls-driven camera movement. Read the
            // Three.js camera position directly for reliable altitude.

            function triggerScopeTransition(lat: number, lng: number) {
              transitionLockRef.current = true;
              onScopeRef.current({ center: [lng, lat], zoom: 4.8 });
              setTimeout(() => {
                transitionLockRef.current = false;
              }, 1200);
            }

            function getCameraAltitude(): number {
              try {
                const camera = globe.camera();
                const distance = camera.position.length();
                return distance / GLOBE_RADIUS - 1;
              } catch (_) {
                return Infinity;
              }
            }

            function checkAndTriggerZoom() {
              if (modeRef.current !== 'global' || transitionLockRef.current) return;
              const altitude = getCameraAltitude();
              if (altitude <= GLOBE_TO_SCOPED_ALTITUDE) {
                // Use pointOfView for lat/lng (those values ARE correct)
                const pov = globe.pointOfView();
                triggerScopeTransition(pov?.lat ?? 0, pov?.lng ?? 0);
              }
            }

            // Mechanism 1: rAF loop — checks every frame
            function checkZoomLoop() {
              if (cancelled) return;
              checkAndTriggerZoom();
              zoomRafId = requestAnimationFrame(checkZoomLoop);
            }
            zoomRafId = requestAnimationFrame(checkZoomLoop);

            // Mechanism 2: OrbitControls change event
            controls.addEventListener('change', checkAndTriggerZoom);

            // Mechanism 3: wheel event with delayed check
            container.addEventListener('wheel', () => {
              setTimeout(checkAndTriggerZoom, 80);
            }, { passive: true });

            container.addEventListener('pointerdown', () => {
              if (controls) controls.autoRotate = false;
            });
            container.addEventListener('pointerup', scheduleAutoRotate);

            globeRef.current = globe;

            // Watch for theme toggle (MutationObserver on <html> class)
            themeObserverRef.current = new MutationObserver(() => {
              setIsLight(document.documentElement.classList.contains('light'));
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
        filter: isLight
          ? 'drop-shadow(0 0 28px rgba(0,0,0,0.12))'
          : 'drop-shadow(0 0 32px rgba(255,255,255,0.08))',
      }}
    />
  );
}
