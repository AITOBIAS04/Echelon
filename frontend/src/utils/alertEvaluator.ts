import type { WatchlistTimeline } from '../types/watchlist';
import type { AlertRule } from '../types/presets';

export interface AlertTrigger {
  ruleId: string;
  ruleName: string;
  timelineId: string;
  timelineName: string;
  severity: 'info' | 'warn' | 'critical';
  timestamp: string;
}

/**
 * Evaluate alert rules against watchlist timelines
 */
export function evaluateAlerts(
  timelines: WatchlistTimeline[],
  rules: AlertRule[]
): AlertTrigger[] {
  const triggers: AlertTrigger[] = [];
  const now = new Date().toISOString();

  for (const rule of rules) {
    if (!rule.enabled) continue;

    for (const timeline of timelines) {
      // Check scope
      if (rule.scope.scopeType === 'timeline' && rule.scope.timelineId !== timeline.id) {
        continue;
      }

      const triggered = evaluateRule(rule, timeline);
      if (triggered) {
        triggers.push({
          ruleId: rule.id,
          ruleName: rule.name,
          timelineId: timeline.id,
          timelineName: timeline.name,
          severity: rule.severity,
          timestamp: now,
        });
      }
    }
  }

  return triggers;
}

/**
 * Evaluate a single alert rule against a timeline
 */
function evaluateRule(rule: AlertRule, timeline: WatchlistTimeline): boolean {
  const { condition } = rule;

  if (condition.type === 'event') {
    // Event-based alerts are stubbed - would require event stream
    // For demo, we'll simulate some events based on timeline state
    if (condition.eventType === 'paradox_spawn' && timeline.paradoxProximity >= 90) {
      return true;
    }
    if (condition.eventType === 'sabotage_disclosed' && timeline.sabotageCount1h > 0) {
      return true;
    }
    if (condition.eventType === 'fork_live') {
      // Stub - would require fork data
      return false;
    }
    if (condition.eventType === 'evidence_flip') {
      // Stub - would require evidence data
      return false;
    }
    return false;
  }

  if (condition.type === 'threshold') {
    const metric = condition.metric;
    const op = condition.op || '>=';
    const value = condition.value ?? 0;

    let timelineValue: number;
    switch (metric) {
      case 'stability':
        timelineValue = timeline.stability;
        break;
      case 'logic_gap':
        timelineValue = timeline.logicGap;
        break;
      case 'paradox_proximity':
        timelineValue = timeline.paradoxProximity;
        break;
      case 'entropy_rate':
        timelineValue = Math.abs(timeline.entropyRate); // Use absolute value
        break;
      case 'sabotage_heat':
        timelineValue = timeline.sabotageCount24h;
        break;
      default:
        return false;
    }

    return compareValues(timelineValue, op, value);
  }

  if (condition.type === 'rate_of_change') {
    // Rate of change evaluation is stubbed
    // Would require historical data to calculate rate
    // For demo, we'll use current value as approximation
    const metric = condition.metric;
    const op = condition.op || '>=';
    const value = condition.value ?? 0;

    let timelineValue: number;
    switch (metric) {
      case 'stability':
        timelineValue = timeline.stability;
        break;
      case 'logic_gap':
        timelineValue = timeline.logicGap;
        break;
      case 'paradox_proximity':
        timelineValue = timeline.paradoxProximity;
        break;
      case 'entropy_rate':
        timelineValue = Math.abs(timeline.entropyRate);
        break;
      case 'sabotage_heat':
        timelineValue = timeline.sabotageCount24h;
        break;
      default:
        return false;
    }

    // Simplified: check if value exceeds threshold (would need history for true rate calc)
    return compareValues(timelineValue, op, value);
  }

  return false;
}

/**
 * Compare two values using an operator
 */
function compareValues(a: number, op: '>' | '>=' | '<' | '<=', b: number): boolean {
  switch (op) {
    case '>':
      return a > b;
    case '>=':
      return a >= b;
    case '<':
      return a < b;
    case '<=':
      return a <= b;
    default:
      return false;
  }
}
