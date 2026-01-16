import { useTimelines } from '../../hooks/useWingFlaps';
import { TimelineCard } from './TimelineCard';

const TimelineGrid = () => {
  const { data, isLoading, error } = useTimelines({ limit: 12 });

  if (isLoading) {
    return (
      <div className="terminal-panel p-6">
        <h3 className="terminal-header mb-4">TIMELINE HEALTH</h3>
        <div className="text-terminal-muted">Loading timelines...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="terminal-panel p-6">
        <h3 className="terminal-header mb-4">TIMELINE HEALTH</h3>
        <div className="text-echelon-red">Error loading timelines</div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="terminal-header mb-4">TIMELINE HEALTH</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.timelines.map((timeline) => (
          <TimelineCard key={timeline.id} timeline={timeline} />
        ))}
      </div>
    </div>
  );
};

export default TimelineGrid;

