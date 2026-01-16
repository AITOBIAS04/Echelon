interface PriceDisplayProps {
  priceYes: number;
  priceNo: number;
}

const PriceDisplay = ({ priceYes, priceNo }: PriceDisplayProps) => {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-terminal-muted">YES</span>
          <span className="text-echelon-green font-medium">
            ${priceYes.toFixed(2)}
          </span>
        </div>
        <div className="h-1 bg-terminal-border rounded-full overflow-hidden">
          <div
            className="h-full bg-echelon-green transition-all"
            style={{ width: `${priceYes * 100}%` }}
          />
        </div>
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-terminal-muted">NO</span>
          <span className="text-echelon-red font-medium">
            ${priceNo.toFixed(2)}
          </span>
        </div>
        <div className="h-1 bg-terminal-border rounded-full overflow-hidden">
          <div
            className="h-full bg-echelon-red transition-all"
            style={{ width: `${priceNo * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default PriceDisplay;



