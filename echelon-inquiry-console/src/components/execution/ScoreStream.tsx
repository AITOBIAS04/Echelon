import { useEffect, useRef, useState } from 'react';
import type { Episode } from '../../types/execution';

interface ScoreStreamProps {
  completedEpisodes: Episode[];
}

export function ScoreStream({ completedEpisodes }: ScoreStreamProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const animRef = useRef<number | null>(null);

  const targetScore =
    completedEpisodes.length > 0
      ? completedEpisodes.reduce((sum, ep) => sum + ep.composite_score, 0) /
        completedEpisodes.length
      : 0;

  useEffect(() => {
    const startScore = displayScore;
    const startTime = performance.now();
    const duration = 400;

    function animate(now: number) {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayScore(startScore + (targetScore - startScore) * eased);

      if (t < 1) {
        animRef.current = requestAnimationFrame(animate);
      }
    }

    animRef.current = requestAnimationFrame(animate);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
    // Only re-run when targetScore changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetScore]);

  if (completedEpisodes.length === 0) return null;

  return (
    <div className="rounded border border-echelon-border bg-white p-3">
      <p className="text-xs uppercase tracking-wider text-slate-500">
        Running Composite
      </p>
      <p className="mt-1 font-mono text-2xl font-semibold text-echelon-navy">
        {displayScore.toFixed(4)}
      </p>
    </div>
  );
}
