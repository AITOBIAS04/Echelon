import { useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { CanvasMode, ViewState } from '../../hooks/useWorkspaceState';
import { SCOPED_TO_GLOBAL_ZOOM } from '../../hooks/useWorkspaceState';
import type { LayerState } from '../../hooks/useLayerState';
import { ALL_LAYERS, LAYER_MAP_IDS } from '../../hooks/useLayerState';

interface ScopedMapProps {
  mode: CanvasMode;
  viewState?: ViewState;
  layers: LayerState;
  onGlobeTransition: () => void;
  onMapReady: (map: maplibregl.Map) => void;
}

// ── Mock GeoJSON data matching design reference shapes ──────────────

const SCOPED_MARKERS: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [32.55, 29.9] }, properties: { provenance: 'evidence', title: 'Suez corridor evidence stack', detail: 'Port authority bulletins and AIS anomalies aligned after reroute detection.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [43.15, 12.78] }, properties: { provenance: 'evidence', title: 'Bab-el-Mandeb conflict chatter', detail: 'Persistent evidence path connects merchant route disruption to open-source reports.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [39.17, 21.49] }, properties: { provenance: 'certified', title: 'Jeddah certificate candidate', detail: 'Candidate chain satisfies issuance pre-check with corroborated vessel movements.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [45.03, 12.8] }, properties: { provenance: 'certified', title: 'Gulf of Aden routing confirmation', detail: 'Certificate path strengthened by insurance chatter and corridor timing alignment.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [56.2, 26.5] }, properties: { provenance: 'inferred', title: 'Hormuz passage inferred', detail: 'Pattern-matched from GDELT activity near Strait of Hormuz.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [48.5, 9.05] }, properties: { provenance: 'inferred', title: 'Mogadishu coastal inference', detail: 'Weak-signal maritime events near Somali coast detected by behavioural model.' } },
  ],
};

const SCOPED_CLUSTERS: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [36.8, 28.2] }, properties: { count: 87, title: 'Gulf of Aqaba cluster', detail: 'GDELT behavioural signals near gulf shipping corridor.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [44.2, 15.3] }, properties: { count: 105, title: 'Yemen coast cluster', detail: 'Elevated GDELT activity — conflict and maritime disruption signals.' } },
  ],
};

const SCOPED_ROUTES: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'LineString', coordinates: [[32.55, 30.0], [34.5, 27.8], [38.5, 22.0], [43.1, 12.8], [45.0, 12.0], [50.0, 13.5], [56.2, 26.5]] }, properties: { title: 'Red Sea — Gulf of Aden route', detail: 'Primary AIS corridor through Bab-el-Mandeb.' } },
  ],
};

const SCOPED_ADSB: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [40.0, 18.5] }, properties: { title: 'ADS-B overflight', detail: 'Surveillance aircraft track near Red Sea.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [55.3, 25.3] }, properties: { title: 'ADS-B Dubai corridor', detail: 'Cargo flight path anomaly detected.' } },
  ],
};

const SCOPED_QUAKES: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [36.1, 29.5] }, properties: { title: 'Gulf of Aqaba seismic', detail: 'M3.2 event detected by USGS near gulf coast.' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [42.0, 11.5] }, properties: { title: 'Djibouti tremor', detail: 'M2.8 shallow event along rift extension.' } },
  ],
};

// ── Component ───────────────────────────────────────────────────────

export function ScopedMap({ mode, viewState, layers, onGlobeTransition, onMapReady }: ScopedMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const initialised = useRef(false);
  const modeRef = useRef(mode);
  const onGlobeRef = useRef(onGlobeTransition);
  const layersRef = useRef(layers);

  // Keep refs current so closures see fresh values
  modeRef.current = mode;
  onGlobeRef.current = onGlobeTransition;
  layersRef.current = layers;

  /** Add all GeoJSON sources, layers, popups — and apply current layer visibility.
   *  Idempotent: removes existing sources/layers first so it survives setStyle() re-entry.
   *  Reads layersRef so it's safe to call from any closure (MutationObserver, style.load). */
  const addLayers = useCallback((map: maplibregl.Map) => {
    // Guard: clean up any existing layers/sources for idempotent re-entry
    const allLayerIds = [
      'scoped-routes', 'scoped-clusters', 'scoped-cluster-counts',
      'scoped-inferred-halo', 'scoped-inferred-points',
      'scoped-evidence-halo', 'scoped-evidence-points',
      'scoped-certified-halo', 'scoped-certified-points',
      'scoped-adsb', 'scoped-quakes',
    ];
    const allSourceIds = [
      'scoped-markers', 'scoped-clusters-src', 'scoped-routes-src',
      'scoped-adsb-src', 'scoped-quakes-src',
    ];
    for (const id of allLayerIds) {
      if (map.getLayer(id)) map.removeLayer(id);
    }
    for (const id of allSourceIds) {
      if (map.getSource(id)) map.removeSource(id);
    }

    // Sources
    map.addSource('scoped-markers', { type: 'geojson', data: SCOPED_MARKERS });
    map.addSource('scoped-clusters-src', { type: 'geojson', data: SCOPED_CLUSTERS });
    map.addSource('scoped-routes-src', { type: 'geojson', data: SCOPED_ROUTES });
    map.addSource('scoped-adsb-src', { type: 'geojson', data: SCOPED_ADSB });
    map.addSource('scoped-quakes-src', { type: 'geojson', data: SCOPED_QUAKES });

    // AIS routes
    map.addLayer({
      id: 'scoped-routes',
      type: 'line',
      source: 'scoped-routes-src',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#49d6ff', 'line-opacity': 0.72, 'line-width': 2.2, 'line-dasharray': [2.2, 2.2] },
    });

    // GDELT clusters
    map.addLayer({
      id: 'scoped-clusters',
      type: 'circle',
      source: 'scoped-clusters-src',
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['get', 'count'], 50, 18, 110, 28],
        'circle-color': '#f3b84a',
        'circle-opacity': 0.92,
        'circle-stroke-width': 10,
        'circle-stroke-color': 'rgba(243,184,74,0.16)',
      },
    });

    map.addLayer({
      id: 'scoped-cluster-counts',
      type: 'symbol',
      source: 'scoped-clusters-src',
      layout: { 'text-field': ['to-string', ['get', 'count']], 'text-size': 12 },
      paint: { 'text-color': '#051018' },
    });

    // Inferred markers (grey)
    map.addLayer({
      id: 'scoped-inferred-halo',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'inferred'],
      paint: { 'circle-radius': 14, 'circle-color': 'rgba(186,189,196,0.18)' },
    });
    map.addLayer({
      id: 'scoped-inferred-points',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'inferred'],
      paint: { 'circle-radius': 6, 'circle-color': '#aeb4bf', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#e5e7eb' },
    });

    // Evidence markers (purple)
    map.addLayer({
      id: 'scoped-evidence-halo',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'evidence'],
      paint: { 'circle-radius': 15, 'circle-color': 'rgba(159,85,255,0.18)' },
    });
    map.addLayer({
      id: 'scoped-evidence-points',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'evidence'],
      paint: { 'circle-radius': 6.5, 'circle-color': '#a855f7', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#f5e9ff' },
    });

    // Certified markers (green)
    map.addLayer({
      id: 'scoped-certified-halo',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'certified'],
      paint: { 'circle-radius': 15, 'circle-color': 'rgba(74,222,128,0.18)' },
    });
    map.addLayer({
      id: 'scoped-certified-points',
      type: 'circle',
      source: 'scoped-markers',
      filter: ['==', ['get', 'provenance'], 'certified'],
      paint: { 'circle-radius': 6.5, 'circle-color': '#4ade80', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#ecfdf3' },
    });

    // ADS-B
    map.addLayer({
      id: 'scoped-adsb',
      type: 'circle',
      source: 'scoped-adsb-src',
      paint: { 'circle-radius': 5, 'circle-color': '#38bdf8', 'circle-stroke-width': 1.4, 'circle-stroke-color': '#e0f2fe', 'circle-opacity': 0.92 },
    });

    // Quakes
    map.addLayer({
      id: 'scoped-quakes',
      type: 'circle',
      source: 'scoped-quakes-src',
      paint: { 'circle-radius': 6, 'circle-color': '#f59e0b', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#fff7ed', 'circle-opacity': 0.94 },
    });

    // Apply current layer visibility (reads ref for fresh state)
    const currentLayers = layersRef.current;
    for (const key of ALL_LAYERS) {
      const visibility = currentLayers[key] ? 'visible' : 'none';
      for (const layerId of LAYER_MAP_IDS[key]) {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', visibility);
        }
      }
    }

    // Popups
    const addPopup = (layerId: string) => {
      map.on('click', layerId, (e) => {
        if (!e.features?.length) return;
        const props = e.features[0].properties;
        new maplibregl.Popup({ closeButton: false, offset: 12 })
          .setLngLat(e.lngLat)
          .setHTML(`<div style="padding:8px 10px;font:12px Inter,sans-serif"><strong>${props?.title ?? 'Signal'}</strong><br/><span style="opacity:0.7">${props?.detail ?? ''}</span></div>`)
          .addTo(map);
      });
      map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
    };

    ['scoped-routes', 'scoped-clusters', 'scoped-cluster-counts',
     'scoped-inferred-points', 'scoped-evidence-points', 'scoped-certified-points',
     'scoped-adsb', 'scoped-quakes'].forEach(addPopup);
  }, []);

  // Initialise map
  useEffect(() => {
    if (initialised.current || !containerRef.current) return;
    initialised.current = true;

    const isLight = document.documentElement.classList.contains('light');
    const tileStyle = isLight
      ? 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
      : 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

    const center = viewState?.center ?? [43.0, 15.0] as [number, number];
    const zoom = viewState?.zoom ?? 5;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: tileStyle,
      center,
      zoom,
      minZoom: 1.5,
      maxZoom: 14,
      attributionControl: false,
      pitchWithRotate: false,
    });

    map.addControl(new maplibregl.AttributionControl({ compact: true }));

    map.on('load', () => {
      addLayers(map);
      onMapReady(map);
    });

    // Zoom-out detection for global transition (uses refs to avoid stale closure)
    map.on('zoomend', () => {
      const currentZoom = map.getZoom();
      if (currentZoom <= SCOPED_TO_GLOBAL_ZOOM && modeRef.current === 'scoped') {
        onGlobeRef.current();
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      initialised.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Swap basemap tiles on theme change (MutationObserver on <html> class)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const LIGHT_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
    const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

    let swapping = false;

    const observer = new MutationObserver(() => {
      if (swapping) return;
      const isLight = document.documentElement.classList.contains('light');
      const nextStyle = isLight ? LIGHT_STYLE : DARK_STYLE;

      // Read the map's current style URL to avoid stale closure comparison
      const currentName = map.getStyle()?.name?.toLowerCase() ?? '';
      const alreadyCorrect = isLight
        ? currentName.includes('positron')
        : currentName.includes('dark');
      if (alreadyCorrect) return;

      swapping = true;
      map.once('style.load', () => {
        addLayers(map);
        swapping = false;
      });
      map.setStyle(nextStyle);
    });

    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => {
      observer.disconnect();
    };
  }, [addLayers]);

  // Fly to new view state
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !viewState || mode !== 'scoped') return;

    map.resize();
    map.flyTo({ center: viewState.center, zoom: viewState.zoom, duration: 2000 });
  }, [viewState, mode]);

  // Update layer visibility when layer state changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    for (const key of ALL_LAYERS) {
      const visibility = layers[key] ? 'visible' : 'none';
      for (const layerId of LAYER_MAP_IDS[key]) {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', visibility);
        }
      }
    }
  }, [layers]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-0"
      style={{
        opacity: mode === 'scoped' ? 1 : 0,
        transition: 'opacity 0.5s ease-out',
        pointerEvents: mode === 'scoped' ? 'auto' : 'none',
      }}
    />
  );
}
