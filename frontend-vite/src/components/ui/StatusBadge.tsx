import { clsx } from 'clsx';

interface StatusBadgeProps {
  variant: 'success' | 'danger' | 'warning' | 'info';
  label: string;
}

const StatusBadge = ({ variant, label }: StatusBadgeProps) => {
  const variantClasses = {
    success: 'bg-echelon-green/20 text-echelon-green border-echelon-green',
    danger: 'bg-echelon-red/20 text-echelon-red border-echelon-red',
    warning: 'bg-echelon-amber/20 text-echelon-amber border-echelon-amber',
    info: 'bg-echelon-blue/20 text-echelon-blue border-echelon-blue',
  };

  return (
    <span
      className={clsx(
        'px-2 py-0.5 text-xs font-medium rounded border',
        variantClasses[variant]
      )}
    >
      {label}
    </span>
  );
};

export default StatusBadge;



