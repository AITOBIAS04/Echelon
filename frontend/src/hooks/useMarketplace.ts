import { useState, useEffect, useCallback } from 'react';
import type { Market, RibbonEvent, Intercept, Breach } from '../types/marketplace';

/**
 * Mock market data for demo
 */
const mockMarkets: Market[] = [
  {
    id: 1,
    category: 'robotics',
    categoryIcon: '🦾',
    categoryName: 'Robotics',
    title: 'Orbital Salvage: Will Option B successfully secure debris?',
    stability: 87,
    stabilityStatus: 'Stable',
    yesPrice: 3.80,
    yesProb: 62,
    noPrice: 2.40,
    noProb: 38,
    liquidity: 12800,
    nextForkEtaSec: 272,
    gap: 12.4,
    volume24h: 125000,
    tradesCount: 342,
    agentLearnings: 156,
  },
  {
    id: 2,
    category: 'robotics',
    categoryIcon: '🦾',
    categoryName: 'Robotics',
    title: 'Disaster Response: Will rescue bot reach target within 5 min?',
    stability: 53,
    stabilityStatus: 'Degraded',
    yesPrice: 2.15,
    yesProb: 48,
    noPrice: 2.35,
    noProb: 52,
    liquidity: 8400,
    nextForkEtaSec: 495,
    gap: 47.0,
    gapWarning: true,
    gapDanger: true,
    volume24h: 89000,
    tradesCount: 187,
    agentLearnings: 89,
  },
  {
    id: 3,
    category: 'logistics',
    categoryIcon: '🚛',
    categoryName: 'Logistics',
    title: 'Neon Courier: Will delivery route optimize under constraints?',
    stability: 91,
    stabilityStatus: 'Stable',
    yesPrice: 4.20,
    yesProb: 78,
    noPrice: 1.40,
    noProb: 22,
    liquidity: 24200,
    nextForkEtaSec: 900,
    gap: 6.2,
    volume24h: 234000,
    tradesCount: 512,
    agentLearnings: 234,
  },
  {
    id: 4,
    category: 'defi',
    categoryIcon: '💸',
    categoryName: 'DeFi',
    title: 'DeFi Yield: Will strategy sustain 15% APY under stress?',
    stability: 34,
    stabilityStatus: 'Critical',
    yesPrice: 1.85,
    yesProb: 42,
    noPrice: 2.60,
    noProb: 58,
    liquidity: 18700,
    nextForkEtaSec: 1320,
    gap: 52.0,
    gapDanger: true,
    volume24h: 456000,
    tradesCount: 892,
    agentLearnings: 412,
  },
  {
    id: 5,
    category: 'physics',
    categoryIcon: '🧪',
    categoryName: 'Physics',
    title: 'Quantum Test: Will entanglement maintain coherence for 10s?',
    stability: 76,
    stabilityStatus: 'Stable',
    yesPrice: 2.90,
    yesProb: 55,
    noPrice: 2.45,
    noProb: 45,
    liquidity: 6200,
    nextForkEtaSec: 2700,
    gap: 18.0,
    gapWarning: true,
    volume24h: 78000,
    tradesCount: 234,
    agentLearnings: 112,
  },
  {
    id: 6,
    category: 'logistics',
    categoryIcon: '🚛',
    categoryName: 'Logistics',
    title: 'Asteroid Mining: Will extraction yield exceed 500kg?',
    stability: 62,
    stabilityStatus: 'Degraded',
    yesPrice: 3.45,
    yesProb: 68,
    noPrice: 1.90,
    noProb: 32,
    liquidity: 31500,
    nextForkEtaSec: 4320,
    gap: 24.0,
    gapWarning: true,
    volume24h: 567000,
    tradesCount: 1245,
    agentLearnings: 567,
  },
];

/**
 * Mock ribbon events
 */
const mockRibbonEvents: RibbonEvent[] = [
  { type: 'fork', title: 'Fork #7 — Option B', time: '4m' },
  { type: 'paradox', title: 'ORB_SALVAGE_F7 Paradox', time: '7m' },
  { type: 'flip', title: 'Consensus Shift Detected', time: '12m' },
  { type: 'sabotage', title: 'Signal Interference Detected', time: '18m' },
  { type: 'settle', title: 'Fork #6 Final Settlement', time: '24m' },
  { type: 'fork', title: 'Fork #5 — Option A', time: '32m' },
];

/**
 * Mock signal intercepts
 */
const mockIntercepts: Intercept[] = [
  {
    id: '1',
    agent: 'CARDINAL',
    theatre: 'orbital_salvage_v1',
    content: 'Detected micro-debris field approaching Station Alpha. Probability of Option B failure: 68%',
    time: '14:32:05',
    actions: ['Theatre', 'Trade'],
  },
  {
    id: '2',
    agent: 'MEGALODON',
    theatre: 'defi_yield_strategy',
    content: 'Flash loan vulnerability detected in reserve contract. Paradox spawn likely within 15 minutes',
    time: '14:26:42',
    actions: ['Shield'],
  },
  {
    id: '3',
    agent: 'CHAMELEON',
    theatre: 'blacksite_heist_b2',
    content: 'Target increased security posture. Deception success probability dropped from 72% to 54%',
    time: '14:18:11',
    actions: ['Adjust'],
  },
  {
    id: '4',
    agent: 'VULTURE',
    theatre: 'neon_courier_f3',
    content: 'Traffic pattern analysis complete. Optimal route deviation detected — may indicate sensor manipulation',
    time: '14:10:05',
    actions: ['Verify'],
  },
];

/**
 * Mock breaches
 */
const mockBreaches: Breach[] = [
  { id: '1', severity: 'critical', category: 'PARADOX', title: 'Logical contradiction in Fork #7 scenario', time: '4m' },
  { id: '2', severity: 'high', category: 'STABILITY', title: 'Stability collapse detected in Option B', time: '12m' },
  { id: '3', severity: 'medium', category: 'ORACLE', title: 'Oracle price deviation exceeds threshold', time: '28m' },
  { id: '4', severity: 'low', category: 'SENSOR', title: 'Minor sensor contradiction in data feed', time: '1h' },
];

/**
 * Hook for market data
 */
export function useMarketData() {
  const [data, setData] = useState<Market[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        setIsLoading(true);
        await new Promise(resolve => setTimeout(resolve, 500));
        setData(mockMarkets);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch markets'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchMarkets();
  }, []);

  return { data, isLoading, error };
}

/**
 * Hook for ribbon events
 */
export function useRibbonEvents() {
  const [data, setData] = useState<RibbonEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      await new Promise(resolve => setTimeout(resolve, 300));
      setData(mockRibbonEvents);
      setIsLoading(false);
    };

    fetchEvents();

    const interval = setInterval(() => {
      setData(prev => {
        const updated = [...prev];
        const randomIndex = Math.floor(Math.random() * updated.length);
        const timeMatch = updated[randomIndex].time.match(/(\d+)m/);
        if (timeMatch) {
          const mins = parseInt(timeMatch[1]) + 1;
          updated[randomIndex] = { ...updated[randomIndex], time: `${mins}m` };
        }
        return updated;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return { data, isLoading };
}

/**
 * Hook for signal intercepts
 */
export function useIntercepts() {
  const [data, setData] = useState<Intercept[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchIntercepts = async () => {
      await new Promise(resolve => setTimeout(resolve, 400));
      setData(mockIntercepts);
      setIsLoading(false);
    };

    fetchIntercepts();
  }, []);

  return { data, isLoading };
}

/**
 * Hook for breaches
 */
export function useBreaches() {
  const [data, setData] = useState<Breach[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchBreaches = async () => {
      await new Promise(resolve => setTimeout(resolve, 350));
      setData(mockBreaches);
      setIsLoading(false);
    };

    fetchBreaches();
  }, []);

  return { data, isLoading };
}

/**
 * Hook for real-time market updates
 */
export function useMarketUpdates(marketId: string | number) {
  const[market, setMarket] = useState<Market | null>(null);

  useEffect(() => {
    const targetMarket = mockMarkets.find(m => m.id === marketId);
    if (!targetMarket) return;

    setMarket(targetMarket);

    const interval = setInterval(() => {
      setMarket(prev => {
        if (!prev) return prev;
        const volatility = 0.02;
        const priceChange = (Math.random() - 0.5) * volatility;
        const newYesPrice = Math.max(0.01, prev.yesPrice * (1 + priceChange));
        const newNoPrice = Math.max(0.01, 5 - newYesPrice);
        const newYesProb = (newYesPrice / 5) * 100;

        return {
          ...prev,
          yesPrice: newYesPrice,
          noPrice: newNoPrice,
          yesProb: Math.round(newYesProb),
          noProb: Math.round(100 - newYesProb),
        };
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [marketId]);

  return market;
}

/**
 * Hook for betting functionality
 */
export function useBetting() {
  const [isBetting, setIsBetting] = useState(false);
  const [betError, setBetError] = useState<string | null>(null);

  const placeBet = useCallback(async (
    _marketId: string | number,
    _outcome: 'YES' | 'NO',
    amount: number
  ) => {
    setIsBetting(true);
    setBetError(null);

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (Math.random() < 0.05) {
        throw new Error('Transaction failed. Please try again.');
      }

      return {
        success: true,
        transactionId: `0x${Math.random().toString(16).slice(2, 10)}`,
        newBalance: 127500 - amount,
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bet failed';
      setBetError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsBetting(false);
    }
  }, []);

  return { placeBet, isBetting, betError };
}

/**
 * Hook for market statistics
 */
export function useMarketStats() {
  const [stats, setStats] = useState({
    totalMarkets: 0,
    activeMarkets: 0,
    totalVolume24h: 0,
    activeForks: 0,
    activeBreaches: 0,
  });

  useEffect(() => {
    const totalVolume = mockMarkets.reduce((sum, m) => sum + m.volume24h, 0);
    const activeForks = mockMarkets.filter(m => m.nextForkEtaSec && m.nextForkEtaSec < 3600).length;

    setStats({
      totalMarkets: mockMarkets.length,
      activeMarkets: mockMarkets.length,
      totalVolume24h: totalVolume,
      activeForks,
      activeBreaches: mockBreaches.length,
    });
  }, []);

  return stats;
}
