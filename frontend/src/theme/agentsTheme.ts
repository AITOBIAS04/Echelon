/**
 * Centralized theme utility for Agents page colors.
 * Uses static Tailwind class strings to prevent purging in production builds.
 *
 * Color mappings based on tailwind.config.js theme:
 * - Agent archetypes map to: emerald (WHALE), blue (DIPLOMAT), amber (SABOTEUR), rose (SHARK), purple (SPY)
 * - Sanity status maps to: emerald (STABLE), amber (STRESSED), rose (CRITICAL), red (BREAKDOWN)
 */

import type { ComponentType } from 'react';
import { Anchor, Shield, Flame, Crosshair, Eye, Bot } from 'lucide-react';

// ============================================================================
// Archetype Theme Mapping
// ============================================================================

export type Archetype = 'WHALE' | 'DIPLOMAT' | 'SABOTEUR' | 'SHARK' | 'SPY' | string;

export interface ArchetypeTheme {
  /** Lucide icon component for the archetype */
  icon: ComponentType<{ className?: string }>;
  /** @deprecated Use `icon` instead */
  emoji: string;
  /** Text color class for labels */
  textClass: string;
  /** Border color class with opacity */
  borderClass: string;
  /** Background color class with opacity */
  bgClass: string;
  /** Hover border color class */
  hoverBorderClass: string;
  /** Icon component name (matches Lucide export name) */
  iconName: string;
  /** Short description of the archetype's role */
  description: string;
}

/**
 * Static theme mapping for each archetype.
 * All classes are fully written to prevent Tailwind purging.
 */
export const getArchetypeTheme = (archetype: Archetype): ArchetypeTheme => {
  const normalizedArchetype = archetype?.toUpperCase();

  switch (normalizedArchetype) {
    case 'WHALE':
      return {
        icon: Anchor,
        emoji: '🐋',
        textClass: 'text-emerald-400',
        borderClass: 'border-emerald-500/30',
        bgClass: 'bg-emerald-500/10',
        hoverBorderClass: 'hover:border-emerald-400/50',
        iconName: 'Anchor',
        description: 'Deep-capital market mover with high liquidity influence',
      };
    case 'DIPLOMAT':
      return {
        icon: Shield,
        emoji: '🤝',
        textClass: 'text-blue-400',
        borderClass: 'border-blue-500/30',
        bgClass: 'bg-blue-500/10',
        hoverBorderClass: 'hover:border-blue-400/50',
        iconName: 'Shield',
        description: 'Stability-focused agent that mediates cross-timeline conflicts',
      };
    case 'SABOTEUR':
      return {
        icon: Flame,
        emoji: '💣',
        textClass: 'text-amber-400',
        borderClass: 'border-amber-500/30',
        bgClass: 'bg-amber-500/10',
        hoverBorderClass: 'hover:border-amber-400/50',
        iconName: 'Flame',
        description: 'Adversarial agent that exploits logic gaps and destabilises markets',
      };
    case 'SHARK':
      return {
        icon: Crosshair,
        emoji: '🦈',
        textClass: 'text-rose-400',
        borderClass: 'border-rose-500/30',
        bgClass: 'bg-rose-500/10',
        hoverBorderClass: 'hover:border-rose-400/50',
        iconName: 'Crosshair',
        description: 'High-volatility precision trader targeting price dislocations',
      };
    case 'SPY':
      return {
        icon: Eye,
        emoji: '🕵️',
        textClass: 'text-purple-400',
        borderClass: 'border-purple-500/30',
        bgClass: 'bg-purple-500/10',
        hoverBorderClass: 'hover:border-purple-400/50',
        iconName: 'Eye',
        description: 'Intelligence gatherer specialising in OSINT and signal interception',
      };
    default:
      return {
        icon: Bot,
        emoji: '🤖',
        textClass: 'text-slate-400',
        borderClass: 'border-slate-500/30',
        bgClass: 'bg-slate-500/10',
        hoverBorderClass: 'hover:border-slate-400/50',
        iconName: 'Bot',
        description: 'General-purpose autonomous market agent',
      };
  }
};

// ============================================================================
// Sanity Status Theme Mapping
// ============================================================================

export type SanityStatus = 'stable' | 'stressed' | 'critical' | 'breakdown';

export interface SanityTheme {
  /** Status label text */
  label: string;
  /** Bar background color */
  barClass: string;
  /** Status indicator color */
  indicatorClass: string;
  /** Card border color for agents with this status */
  cardBorderClass: string;
  /** Card hover border color */
  cardHoverClass: string;
  /** Glow effect for critical/breakdown states */
  glowClass: string;
}

/**
 * Static theme mapping for sanity status levels.
 */
export const getSanityTheme = (sanityPercent: number): SanityTheme => {
  if (sanityPercent > 70) {
    return {
      label: 'STABLE',
      barClass: 'bg-emerald-500',
      indicatorClass: 'bg-emerald-500',
      cardBorderClass: 'border-emerald-500/30',
      cardHoverClass: 'hover:border-emerald-400/50',
      glowClass: '',
    };
  } else if (sanityPercent > 40) {
    return {
      label: 'STRESSED',
      barClass: 'bg-amber-500',
      indicatorClass: 'bg-amber-500',
      cardBorderClass: 'border-amber-500/30',
      cardHoverClass: 'hover:border-amber-400/50',
      glowClass: '',
    };
  } else if (sanityPercent > 20) {
    return {
      label: 'CRITICAL',
      barClass: 'bg-rose-500',
      indicatorClass: 'bg-rose-500',
      cardBorderClass: 'border-rose-500/50',
      cardHoverClass: 'hover:border-rose-400/50',
      glowClass: 'animate-pulse',
    };
  } else {
    return {
      label: 'BREAKDOWN',
      barClass: 'bg-red-600',
      indicatorClass: 'bg-red-600',
      cardBorderClass: 'border-red-600/50',
      cardHoverClass: 'hover:border-red-500/50',
      glowClass: 'animate-pulse relative overflow-hidden',
    };
  }
};

// ============================================================================
// Theatre/Activity Theme Mapping
// ============================================================================

export type ActivityLevel = 'high' | 'medium' | 'low';

export interface TheatreTheme {
  /** Activity indicator icon name (Lucide) */
  indicatorIcon: 'Flame' | 'AlertCircle' | 'CheckCircle';
  /** @deprecated Use indicatorIcon */
  indicator: string;
  /** Border color class */
  borderClass: string;
  /** Background color class */
  bgClass: string;
  /** Text color for activity label */
  textClass: string;
}

/**
 * Static theme mapping for theatre activity levels.
 */
export const getTheatreTheme = (activity: ActivityLevel): TheatreTheme => {
  switch (activity) {
    case 'high':
      return {
        indicatorIcon: 'Flame',
        indicator: '🔥',
        borderClass: 'border-rose-500/50',
        bgClass: 'bg-rose-500/10',
        textClass: 'text-rose-400',
      };
    case 'medium':
      return {
        indicatorIcon: 'AlertCircle',
        indicator: '🟡',
        borderClass: 'border-amber-500/50',
        bgClass: 'bg-amber-500/10',
        textClass: 'text-amber-400',
      };
    case 'low':
      return {
        indicatorIcon: 'CheckCircle',
        indicator: '🟢',
        borderClass: 'border-emerald-500/50',
        bgClass: 'bg-emerald-500/10',
        textClass: 'text-emerald-400',
      };
    default:
      return {
        indicatorIcon: 'CheckCircle',
        indicator: '🟢',
        borderClass: 'border-slate-500/50',
        bgClass: 'bg-slate-500/10',
        textClass: 'text-slate-400',
      };
  }
};

// ============================================================================
// Movement Type Theme Mapping
// ============================================================================

export type MovementType = 'deploy' | 'withdraw' | 'strategy';

export interface MovementTheme {
  /** Icon to display */
  icon: string;
  /** Background color class */
  bgClass: string;
  /** Text color class */
  textClass: string;
}

/**
 * Static theme mapping for movement feed event types.
 */
export const getMovementTheme = (type: MovementType): MovementTheme => {
  switch (type) {
    case 'deploy':
      return {
        icon: '→',
        bgClass: 'bg-emerald-500/20',
        textClass: 'text-emerald-400',
      };
    case 'withdraw':
      return {
        icon: '←',
        bgClass: 'bg-rose-500/20',
        textClass: 'text-rose-400',
      };
    case 'strategy':
      return {
        icon: '⚡',
        bgClass: 'bg-amber-500/20',
        textClass: 'text-amber-400',
      };
    default:
      return {
        icon: '•',
        bgClass: 'bg-slate-500/20',
        textClass: 'text-slate-400',
      };
  }
};

// ============================================================================
// Velocity Theme Mapping
// ============================================================================

export interface VelocityTheme {
  /** Color class for velocity indicator */
  colorClass: string;
}

/**
 * Static theme mapping for movement velocity indicators.
 */
export const getVelocityTheme = (velocity: string): VelocityTheme => {
  if (velocity.includes('+')) {
    return { colorClass: 'text-emerald-400' };
  } else if (velocity.includes('-')) {
    return { colorClass: 'text-rose-400' };
  } else {
    return { colorClass: 'text-slate-400' };
  }
};

// ============================================================================
// Conflict Severity Theme Mapping
// ============================================================================

export type ConflictSeverity = 'high' | 'medium' | 'low';

export interface ConflictTheme {
  /** Severity badge text (no emoji) */
  badge: string;
  /** Severity badge icon name (Lucide) */
  badgeIcon: 'AlertTriangle' | 'AlertCircle' | 'CheckCircle';
  /** Badge background color */
  badgeBgClass: string;
  /** Badge text color */
  badgeTextClass: string;
  /** Card border color */
  borderClass: string;
  /** Card background color */
  bgClass: string;
  /** Impact text color (positive/negative) */
  impactClass: string;
}

/**
 * Static theme mapping for conflict severity levels.
 */
export const getConflictTheme = (severity: ConflictSeverity, impact: number): ConflictTheme => {
  const impactClass = impact > 0 ? 'text-emerald-400' : 'text-rose-400';

  switch (severity) {
    case 'high':
      return {
        badge: 'HIGH IMPACT',
        badgeIcon: 'AlertTriangle',
        badgeBgClass: 'bg-rose-500/20',
        badgeTextClass: 'text-rose-400',
        borderClass: 'border-rose-500/50',
        bgClass: 'bg-rose-500/5',
        impactClass,
      };
    case 'medium':
      return {
        badge: 'MEDIUM',
        badgeIcon: 'AlertCircle',
        badgeBgClass: 'bg-amber-500/20',
        badgeTextClass: 'text-amber-400',
        borderClass: 'border-amber-500/50',
        bgClass: 'bg-amber-500/5',
        impactClass,
      };
    case 'low':
      return {
        badge: 'LOW',
        badgeIcon: 'CheckCircle',
        badgeBgClass: 'bg-emerald-500/20',
        badgeTextClass: 'text-emerald-400',
        borderClass: 'border-emerald-500/50',
        bgClass: 'bg-emerald-500/5',
        impactClass,
      };
    default:
      return {
        badge: '•',
        badgeIcon: 'CheckCircle',
        badgeBgClass: 'bg-slate-500/20',
        badgeTextClass: 'text-slate-400',
        borderClass: 'border-slate-500/50',
        bgClass: 'bg-slate-500/5',
        impactClass,
      };
  }
};

// ============================================================================
// KPI Card Theme Mapping
// ============================================================================

export interface KpiTheme {
  /** Icon background color */
  iconBgClass: string;
  /** Icon color */
  iconClass: string;
  /** Change indicator color (positive) */
  changeUpClass: string;
  /** Change indicator color (negative/down) */
  changeDownClass: string;
}

/**
 * Static theme for KPI card types.
 */
export const getKpiTheme = (type: 'agents' | 'deployed' | 'movements' | 'conflicts'): KpiTheme => {
  switch (type) {
    case 'agents':
      return {
        iconBgClass: 'bg-cyan-500/20',
        iconClass: 'text-cyan-400',
        changeUpClass: 'text-emerald-400',
        changeDownClass: 'text-rose-400',
      };
    case 'deployed':
      return {
        iconBgClass: 'bg-emerald-500/20',
        iconClass: 'text-emerald-400',
        changeUpClass: 'text-emerald-400',
        changeDownClass: 'text-rose-400',
      };
    case 'movements':
      return {
        iconBgClass: 'bg-purple-500/20',
        iconClass: 'text-purple-400',
        changeUpClass: 'text-emerald-400',
        changeDownClass: 'text-rose-400',
      };
    case 'conflicts':
      return {
        iconBgClass: 'bg-rose-500/20',
        iconClass: 'text-rose-400',
        changeUpClass: 'text-emerald-400',
        changeDownClass: 'text-emerald-400',
      };
    default:
      return {
        iconBgClass: 'bg-slate-500/20',
        iconClass: 'text-slate-400',
        changeUpClass: 'text-emerald-400',
        changeDownClass: 'text-rose-400',
      };
  }
};

// ============================================================================
// Cluster Card Theme Mapping
// ============================================================================

export interface ClusterTheme {
  /** Icon color */
  iconClass: string;
  /** Win rate color (good) */
  winRateGoodClass: string;
  /** Win rate color (warning) */
  winRateWarningClass: string;
  /** Win rate color (danger) */
  winRateDangerClass: string;
}

/**
 * Static theme for strategy cluster cards.
 */
export const getClusterTheme = (_winRate: number): ClusterTheme => {
  return {
    iconClass: 'text-cyan-400',
    winRateGoodClass: 'text-emerald-400',
    winRateWarningClass: 'text-amber-400',
    winRateDangerClass: 'text-rose-400',
  };
};

// ============================================================================
// Sanity Distribution Theme Mapping
// ============================================================================

export interface SanityDistributionTheme {
  /** Text color for stable count */
  stableClass: string;
  /** Text color for stressed count */
  stressedClass: string;
  /** Text color for critical count */
  criticalClass: string;
  /** Text color for breakdown count */
  breakdownClass: string;
}

/**
 * Static theme for sanity distribution panel.
 */
export const getSanityDistributionTheme = (): SanityDistributionTheme => ({
  stableClass: 'text-emerald-400',
  stressedClass: 'text-amber-400',
  criticalClass: 'text-rose-400',
  breakdownClass: 'text-red-500',
});

// ============================================================================
// Performance Summary Theme Mapping
// ============================================================================

export interface PerformanceTheme {
  /** Positive P/L color */
  plPositiveClass: string;
  /** Negative P/L color */
  plNegativeClass: string;
}

/**
 * Static theme for performance summary panel.
 */
export const getPerformanceTheme = (_pl: number): PerformanceTheme => ({
  plPositiveClass: 'text-emerald-400',
  plNegativeClass: 'text-rose-400',
});
