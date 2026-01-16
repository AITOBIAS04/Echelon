import { clsx } from 'clsx';
import type { AgentArchetype } from '../../types';

interface AgentAvatarProps {
  archetype: AgentArchetype;
  name: string;
  size?: 'sm' | 'md' | 'lg';
}

const AgentAvatar = ({ archetype, name, size = 'md' }: AgentAvatarProps) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-12 h-12 text-base',
  };

  const archetypeColors = {
    SHARK: 'bg-agent-shark/20 text-agent-shark border-agent-shark',
    SPY: 'bg-agent-spy/20 text-agent-spy border-agent-spy',
    DIPLOMAT: 'bg-agent-diplomat/20 text-agent-diplomat border-agent-diplomat',
    SABOTEUR: 'bg-agent-saboteur/20 text-agent-saboteur border-agent-saboteur',
    WHALE: 'bg-agent-whale/20 text-agent-whale border-agent-whale',
    DEGEN: 'bg-echelon-purple/20 text-echelon-purple border-echelon-purple',
  };

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className={clsx(
        'rounded-full border flex items-center justify-center font-medium',
        sizeClasses[size],
        archetypeColors[archetype]
      )}
      title={`${name} (${archetype})`}
    >
      {initials}
    </div>
  );
};

export default AgentAvatar;


