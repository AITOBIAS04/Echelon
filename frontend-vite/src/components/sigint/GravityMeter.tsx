interface GravityMeterProps {
  gravity: number;
}

const GravityMeter = ({ gravity }: GravityMeterProps) => {
  const gravityPercent = Math.min(100, (gravity / 100) * 100);
  const gravityColor =
    gravity > 75
      ? 'bg-echelon-green'
      : gravity > 50
      ? 'bg-echelon-amber'
      : 'bg-echelon-red';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-terminal-muted">Gravity</span>
        <span className="text-terminal-text">{gravity.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-terminal-border rounded-full overflow-hidden">
        <div
          className={`h-full ${gravityColor} transition-all duration-300`}
          style={{ width: `${gravityPercent}%` }}
        />
      </div>
    </div>
  );
};

export default GravityMeter;



