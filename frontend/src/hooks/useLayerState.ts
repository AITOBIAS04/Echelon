import { useCallback, useRef, useState } from 'react';

export type LayerKey = 'gdelt' | 'ais' | 'adsb' | 'quakes' | 'evidence' | 'certified';

/** Maps UI layer keys to backend source_group values */
export const LAYER_SOURCE_GROUP: Record<LayerKey, string> = {
  gdelt: 'alt_data_behavioural',
  ais: 'maritime_ais',
  adsb: 'aviation_adsb',
  quakes: 'geophysical_hazard',
  evidence: '__all_provenance_evidence',
  certified: '__all_provenance_certified',
};

/** Maps UI layer keys to MapLibre layer IDs */
export const LAYER_MAP_IDS: Record<LayerKey, string[]> = {
  gdelt: ['scoped-clusters', 'scoped-cluster-counts', 'scoped-inferred-halo', 'scoped-inferred-points'],
  ais: ['scoped-routes'],
  adsb: ['scoped-adsb'],
  quakes: ['scoped-quakes'],
  evidence: ['scoped-evidence-halo', 'scoped-evidence-points'],
  certified: ['scoped-certified-halo', 'scoped-certified-points'],
};

export const LAYER_LABELS: Record<LayerKey, string> = {
  gdelt: 'GDELT',
  ais: 'AIS routes',
  adsb: 'ADS-B',
  quakes: 'Quakes',
  evidence: 'Evidence overlays',
  certified: 'Cert candidates',
};

/** Provenance colour for each layer toggle indicator */
export const LAYER_COLOURS: Record<LayerKey, string> = {
  gdelt: 'oklch(0.82 0.16 80)',    // amber/gold
  ais: 'oklch(0.76 0.14 210)',     // cyan
  adsb: 'oklch(0.78 0.13 220)',    // sky blue
  quakes: 'oklch(0.78 0.16 75)',   // orange
  evidence: 'oklch(0.65 0.24 300)', // purple
  certified: 'oklch(0.72 0.19 155)', // green
};

export const ALL_LAYERS: LayerKey[] = ['gdelt', 'ais', 'adsb', 'quakes', 'evidence', 'certified'];

export type LayerState = Record<LayerKey, boolean>;

const DEFAULT_LAYER_STATE: LayerState = {
  gdelt: true,
  ais: true,
  adsb: true,
  quakes: true,
  evidence: true,
  certified: true,
};

export function useLayerState() {
  const [layers, setLayers] = useState<LayerState>(DEFAULT_LAYER_STATE);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const setMapRef = useCallback((map: maplibregl.Map | null) => {
    mapRef.current = map;
  }, []);

  const toggleLayer = useCallback((key: LayerKey) => {
    setLayers((prev) => {
      const next = { ...prev, [key]: !prev[key] };

      // Apply to MapLibre immediately
      const map = mapRef.current;
      if (map) {
        const visibility = next[key] ? 'visible' : 'none';
        for (const layerId of LAYER_MAP_IDS[key]) {
          if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, 'visibility', visibility);
          }
        }
      }

      return next;
    });
  }, []);

  const applyAllLayers = useCallback((map: maplibregl.Map) => {
    for (const key of ALL_LAYERS) {
      const visibility = layers[key] ? 'visible' : 'none';
      for (const layerId of LAYER_MAP_IDS[key]) {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', visibility);
        }
      }
    }
  }, [layers]);

  const enabledCount = ALL_LAYERS.filter((k) => layers[k]).length;

  return {
    layers,
    toggleLayer,
    enabledCount,
    setMapRef,
    applyAllLayers,
  };
}
