/**
 * Hot Potato Event Component
 * ==========================
 * 
 * High-drama "Musical Chairs" mechanic where a bomb passes between timeline bubbles.
 * Creates viral moments with real stakes.
 * 
 * Features:
 * - Real-time countdown timer
 * - Animated bomb passing
 * - Bribe fee escalation display
 * - Prize pool tracker
 * - Survivor rewards
 * 
 * @author Echelon Protocol
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';

// =============================================================================
// TYPES
// =============================================================================

interface TimelineBubble {
  id: string;
  timelineId: number;
  name: string;
  description: string;
  shardCount: number;
  totalValue: number;
  isEliminated: boolean;
  position: { x: number; y: number };
}

interface HotPotatoEvent {
  eventId: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  bubbles: TimelineBubble[];
  currentHolderIndex: number;
  bombPlacedAt: number; // timestamp
  currentTimer: number; // seconds remaining
  passCount: number;
  prizePool: number;
  currentBribeFee: number;
  lastPasser: string | null;
  eliminatedIndices: number[];
}

interface PassAttempt {
  passer: string;
  fromBubble: string;
  toBubble: string;
  fee: number;
  timestamp: number;
  newTimer: number;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const BASE_TIMER = 60 * 60; // 60 minutes in seconds
const TIMER_REDUCTION = 10 * 60; // 10 minutes per pass
const MIN_TIMER = 10 * 60; // 10 minutes minimum

const COLORS = {
  bomb: '#FF4136',
  safe: '#2ECC40',
  eliminated: '#AAAAAA',
  warning: '#FF851B',
  danger: '#FF4136',
  prize: '#FFDC00',
  background: '#1a1a2e',
  surface: '#16213e',
  text: '#ffffff',
  textMuted: '#a0a0a0',
};

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

/**
 * Countdown Timer Display
 */
const CountdownTimer: React.FC<{
  seconds: number;
  isHolder: boolean;
}> = ({ seconds, isHolder }) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  
  const urgencyColor = useMemo(() => {
    if (seconds <= 60) return COLORS.danger;
    if (seconds <= 300) return COLORS.warning;
    return isHolder ? COLORS.bomb : COLORS.safe;
  }, [seconds, isHolder]);
  
  return (
    <div style={{
      fontFamily: 'monospace',
      fontSize: isHolder ? '3rem' : '1.5rem',
      fontWeight: 'bold',
      color: urgencyColor,
      textShadow: isHolder ? `0 0 20px ${urgencyColor}` : 'none',
      animation: seconds <= 60 ? 'pulse 1s infinite' : 'none',
    }}>
      {String(minutes).padStart(2, '0')}:{String(secs).padStart(2, '0')}
    </div>
  );
};

/**
 * Animated Bomb Icon
 */
const BombIcon: React.FC<{
  size?: number;
  isActive?: boolean;
}> = ({ size = 48, isActive = true }) => (
  <div style={{
    width: size,
    height: size,
    position: 'relative',
    animation: isActive ? 'shake 0.5s infinite' : 'none',
  }}>
    <svg viewBox="0 0 64 64" width={size} height={size}>
      {/* Bomb body */}
      <circle cx="32" cy="36" r="24" fill="#333" />
      <circle cx="32" cy="36" r="20" fill="#444" />
      
      {/* Fuse */}
      <path
        d="M32 12 Q40 8 44 4"
        stroke="#8B4513"
        strokeWidth="3"
        fill="none"
      />
      
      {/* Spark */}
      {isActive && (
        <circle cx="44" cy="4" r="4" fill={COLORS.bomb}>
          <animate
            attributeName="r"
            values="3;5;3"
            dur="0.3s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="fill"
            values="#FF4136;#FFDC00;#FF4136"
            dur="0.3s"
            repeatCount="indefinite"
          />
        </circle>
      )}
      
      {/* Highlight */}
      <ellipse cx="26" cy="30" rx="6" ry="4" fill="rgba(255,255,255,0.2)" />
    </svg>
  </div>
);

/**
 * Timeline Bubble Component
 */
const TimelineBubbleCard: React.FC<{
  bubble: TimelineBubble;
  isHolder: boolean;
  isEliminated: boolean;
  canPass: boolean;
  timeRemaining: number;
  onPass: () => void;
  bribeFee: number;
}> = ({ bubble, isHolder, isEliminated, canPass, timeRemaining, onPass, bribeFee }) => {
  const backgroundColor = useMemo(() => {
    if (isEliminated) return COLORS.eliminated;
    if (isHolder) return `linear-gradient(135deg, ${COLORS.bomb}33, ${COLORS.bomb}66)`;
    return COLORS.surface;
  }, [isEliminated, isHolder]);
  
  return (
    <div
      style={{
        position: 'absolute',
        left: bubble.position.x,
        top: bubble.position.y,
        width: 200,
        padding: 16,
        borderRadius: 16,
        background: backgroundColor,
        border: `3px solid ${isHolder ? COLORS.bomb : isEliminated ? COLORS.eliminated : COLORS.safe}`,
        opacity: isEliminated ? 0.5 : 1,
        transition: 'all 0.3s ease',
        boxShadow: isHolder ? `0 0 30px ${COLORS.bomb}` : '0 4px 12px rgba(0,0,0,0.3)',
      }}
    >
      {/* Bomb indicator */}
      {isHolder && !isEliminated && (
        <div style={{
          position: 'absolute',
          top: -30,
          left: '50%',
          transform: 'translateX(-50%)',
        }}>
          <BombIcon size={48} isActive={true} />
        </div>
      )}
      
      {/* Bubble content */}
      <h3 style={{
        margin: '0 0 8px 0',
        color: COLORS.text,
        fontSize: '1rem',
        textDecoration: isEliminated ? 'line-through' : 'none',
      }}>
        {bubble.name}
      </h3>
      
      <p style={{
        margin: '0 0 12px 0',
        color: COLORS.textMuted,
        fontSize: '0.8rem',
      }}>
        {bubble.description}
      </p>
      
      {/* Stats */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 12,
        fontSize: '0.75rem',
        color: COLORS.textMuted,
      }}>
        <span>Shards: {bubble.shardCount.toLocaleString()}</span>
        <span>${bubble.totalValue.toLocaleString()}</span>
      </div>
      
      {/* Timer for holder */}
      {isHolder && !isEliminated && (
        <div style={{ textAlign: 'center', marginBottom: 12 }}>
          <CountdownTimer seconds={timeRemaining} isHolder={true} />
        </div>
      )}
      
      {/* Pass button */}
      {canPass && !isEliminated && !isHolder && (
        <button
          onClick={onPass}
          style={{
            width: '100%',
            padding: '10px 16px',
            background: `linear-gradient(135deg, ${COLORS.bomb}, #FF6B6B)`,
            border: 'none',
            borderRadius: 8,
            color: 'white',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontSize: '0.9rem',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          Pass Bomb (${bribeFee.toLocaleString()})
        </button>
      )}
      
      {/* Eliminated badge */}
      {isEliminated && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%) rotate(-15deg)',
          background: COLORS.eliminated,
          padding: '8px 24px',
          borderRadius: 4,
          fontSize: '1.2rem',
          fontWeight: 'bold',
          color: '#333',
        }}>
          ELIMINATED
        </div>
      )}
    </div>
  );
};

/**
 * Prize Pool Display
 */
const PrizePoolDisplay: React.FC<{
  prizePool: number;
  survivorShare: number;
  lastPasserShare: number;
}> = ({ prizePool, survivorShare, lastPasserShare }) => (
  <div style={{
    background: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  }}>
    <h3 style={{
      margin: '0 0 12px 0',
      color: COLORS.prize,
      display: 'flex',
      alignItems: 'center',
      gap: 8,
    }}>
      🏆 Prize Pool
    </h3>
    
    <div style={{
      fontSize: '2rem',
      fontWeight: 'bold',
      color: COLORS.prize,
      marginBottom: 12,
    }}>
      ${prizePool.toLocaleString()}
    </div>
    
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.85rem',
      color: COLORS.textMuted,
    }}>
      <div>
        <div>Survivors (70%)</div>
        <div style={{ color: COLORS.text, fontWeight: 'bold' }}>
          ${survivorShare.toLocaleString()}
        </div>
      </div>
      <div>
        <div>Last Passer (20%)</div>
        <div style={{ color: COLORS.text, fontWeight: 'bold' }}>
          ${lastPasserShare.toLocaleString()}
        </div>
      </div>
    </div>
  </div>
);

/**
 * Pass History Feed
 */
const PassHistoryFeed: React.FC<{
  passes: PassAttempt[];
}> = ({ passes }) => (
  <div style={{
    background: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    maxHeight: 300,
    overflowY: 'auto',
  }}>
    <h3 style={{
      margin: '0 0 12px 0',
      color: COLORS.text,
    }}>
      📜 Pass History
    </h3>
    
    {passes.length === 0 ? (
      <p style={{ color: COLORS.textMuted, fontSize: '0.9rem' }}>
        No passes yet. The bomb is waiting...
      </p>
    ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {passes.slice().reverse().map((pass, idx) => (
          <div
            key={idx}
            style={{
              padding: 8,
              background: 'rgba(255,255,255,0.05)',
              borderRadius: 8,
              fontSize: '0.85rem',
            }}
          >
            <div style={{ color: COLORS.text }}>
              <strong>{pass.passer.slice(0, 8)}...</strong> passed bomb
            </div>
            <div style={{ color: COLORS.textMuted, fontSize: '0.75rem' }}>
              {pass.fromBubble} → {pass.toBubble} | Fee: ${pass.fee} | Timer: {Math.floor(pass.newTimer / 60)}m
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const HotPotatoGame: React.FC<{
  eventId: string;
  userAddress: string;
  onPassBomb?: (targetIndex: number) => Promise<void>;
  onClaimReward?: () => Promise<void>;
}> = ({ eventId, userAddress, onPassBomb, onClaimReward }) => {
  // State
  const [event, setEvent] = useState<HotPotatoEvent | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [passHistory, setPassHistory] = useState<PassAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPassing, setIsPassing] = useState(false);
  
  // Mock data for demo
  useEffect(() => {
    // In production, fetch from API/contract
    const mockEvent: HotPotatoEvent = {
      eventId,
      status: 'active',
      bubbles: [
        {
          id: 'b1',
          timelineId: 1,
          name: 'Fed Cut Timeline',
          description: 'What if Fed cut rates?',
          shardCount: 15000,
          totalValue: 45000,
          isEliminated: false,
          position: { x: 50, y: 100 },
        },
        {
          id: 'b2',
          timelineId: 2,
          name: 'Fed Hold Timeline',
          description: 'What if Fed held steady?',
          shardCount: 12000,
          totalValue: 36000,
          isEliminated: false,
          position: { x: 300, y: 50 },
        },
        {
          id: 'b3',
          timelineId: 3,
          name: 'Fed Hike Timeline',
          description: 'What if Fed raised rates?',
          shardCount: 8000,
          totalValue: 24000,
          isEliminated: false,
          position: { x: 550, y: 100 },
        },
        {
          id: 'b4',
          timelineId: 4,
          name: 'Emergency Cut',
          description: 'What if emergency cut?',
          shardCount: 5000,
          totalValue: 15000,
          isEliminated: true,
          position: { x: 175, y: 280 },
        },
        {
          id: 'b5',
          timelineId: 5,
          name: 'Double Hike',
          description: 'What if double hike?',
          shardCount: 3000,
          totalValue: 9000,
          isEliminated: false,
          position: { x: 425, y: 280 },
        },
      ],
      currentHolderIndex: 0,
      bombPlacedAt: Date.now() - 1800000, // 30 mins ago
      currentTimer: 1800, // 30 mins remaining
      passCount: 3,
      prizePool: 2500,
      currentBribeFee: 75,
      lastPasser: '0x1234...5678',
      eliminatedIndices: [3],
    };
    
    setEvent(mockEvent);
    setTimeRemaining(mockEvent.currentTimer);
    setIsLoading(false);
  }, [eventId]);
  
  // Countdown timer
  useEffect(() => {
    if (!event || event.status !== 'active') return;
    
    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          // Trigger explosion
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [event]);
  
  // Handle pass bomb
  const handlePassBomb = useCallback(async (targetIndex: number) => {
    if (!event || isPassing) return;
    
    setIsPassing(true);
    
    try {
      if (onPassBomb) {
        await onPassBomb(targetIndex);
      }
      
      // Optimistic update
      const pass: PassAttempt = {
        passer: userAddress,
        fromBubble: event.bubbles[event.currentHolderIndex].name,
        toBubble: event.bubbles[targetIndex].name,
        fee: event.currentBribeFee,
        timestamp: Date.now(),
        newTimer: Math.max(timeRemaining - TIMER_REDUCTION / 60, MIN_TIMER / 60) * 60,
      };
      
      setPassHistory(prev => [...prev, pass]);
      
      setEvent(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          currentHolderIndex: targetIndex,
          passCount: prev.passCount + 1,
          prizePool: prev.prizePool + prev.currentBribeFee,
          currentBribeFee: Math.round(prev.currentBribeFee * 1.1),
          currentTimer: Math.max(prev.currentTimer - TIMER_REDUCTION, MIN_TIMER),
          lastPasser: userAddress,
        };
      });
      
      setTimeRemaining(prev => Math.max(prev - TIMER_REDUCTION, MIN_TIMER));
      
    } catch (error) {
      console.error('Failed to pass bomb:', error);
    } finally {
      setIsPassing(false);
    }
  }, [event, isPassing, onPassBomb, userAddress, timeRemaining]);
  
  // Calculate prize shares
  const survivorShare = event ? Math.round(event.prizePool * 0.7) : 0;
  const lastPasserShare = event ? Math.round(event.prizePool * 0.2) : 0;
  
  if (isLoading || !event) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: 400,
        color: COLORS.text,
      }}>
        Loading Hot Potato Event...
      </div>
    );
  }
  
  return (
    <div style={{
      background: COLORS.background,
      borderRadius: 16,
      padding: 24,
      color: COLORS.text,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
      }}>
        <div>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
            <BombIcon size={32} />
            Hot Potato: Fed Decision
          </h2>
          <p style={{ margin: '4px 0 0 0', color: COLORS.textMuted }}>
            Pass the bomb or get eliminated!
          </p>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: COLORS.textMuted, fontSize: '0.85rem' }}>
            Pass #{event.passCount + 1}
          </div>
          <div style={{ color: COLORS.bomb, fontWeight: 'bold' }}>
            Bribe Fee: ${event.currentBribeFee}
          </div>
        </div>
      </div>
      
      {/* Main game area */}
      <div style={{ display: 'flex', gap: 24 }}>
        {/* Bubble arena */}
        <div style={{
          flex: 2,
          position: 'relative',
          height: 450,
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 12,
          overflow: 'hidden',
        }}>
          {event.bubbles.map((bubble, idx) => (
            <TimelineBubbleCard
              key={bubble.id}
              bubble={bubble}
              isHolder={idx === event.currentHolderIndex}
              isEliminated={event.eliminatedIndices.includes(idx)}
              canPass={idx === event.currentHolderIndex}
              timeRemaining={timeRemaining}
              onPass={() => {
                // Find next valid target
                const validTargets = event.bubbles
                  .map((_, i) => i)
                  .filter(i => i !== idx && !event.eliminatedIndices.includes(i));
                
                if (validTargets.length > 0) {
                  // Show target selection UI in production
                  handlePassBomb(validTargets[0]);
                }
              }}
              bribeFee={event.currentBribeFee}
            />
          ))}
          
          {/* Connection lines */}
          <svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
            }}
          >
            {event.bubbles.map((bubble, idx) => {
              if (event.eliminatedIndices.includes(idx)) return null;
              
              // Draw lines to adjacent bubbles
              return event.bubbles.map((target, tIdx) => {
                if (tIdx <= idx || event.eliminatedIndices.includes(tIdx)) return null;
                
                return (
                  <line
                    key={`${idx}-${tIdx}`}
                    x1={bubble.position.x + 100}
                    y1={bubble.position.y + 60}
                    x2={target.position.x + 100}
                    y2={target.position.y + 60}
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth={2}
                    strokeDasharray="5,5"
                  />
                );
              });
            })}
          </svg>
        </div>
        
        {/* Side panel */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Global timer */}
          <div style={{
            background: COLORS.surface,
            borderRadius: 12,
            padding: 16,
            textAlign: 'center',
          }}>
            <div style={{ color: COLORS.textMuted, marginBottom: 8 }}>
              Time Until Explosion
            </div>
            <CountdownTimer seconds={timeRemaining} isHolder={false} />
          </div>
          
          {/* Prize pool */}
          <PrizePoolDisplay
            prizePool={event.prizePool}
            survivorShare={survivorShare}
            lastPasserShare={lastPasserShare}
          />
          
          {/* Pass history */}
          <PassHistoryFeed passes={passHistory} />
        </div>
      </div>
      
      {/* CSS animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-2px) rotate(-1deg); }
          75% { transform: translateX(2px) rotate(1deg); }
        }
      `}</style>
    </div>
  );
};

export default HotPotatoGame;
export { TimelineBubbleCard, CountdownTimer, BombIcon, PrizePoolDisplay };
