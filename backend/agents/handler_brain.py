"""
Handler Brain - LLM integration for AI-assisted trading guidance.

Provides contextual responses from handler personalities based on user context.
"""

import os
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Initialize Anthropic client
# Set ANTHROPIC_API_KEY in environment or use default
try:
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
except Exception as e:
    logger.warning(f"Anthropic client initialization failed: {e}")
    client = None


async def generate_handler_response(
    handler_personality: str,
    user_message: str,
    context: Dict[str, Any]
) -> str:
    """
    Generate contextual response from handler based on personality and context.
    
    Args:
        handler_personality: System prompt defining handler's personality
        user_message: User's question/message
        context: Dictionary containing positions, signals, market state, operation
        
    Returns:
        Handler's response as string
    """
    if not client:
        # Fallback response if LLM client not available
        return "Handler service temporarily unavailable. Please try again later."
    
    # Format context for system prompt
    positions_str = format_positions(context.get("positions", []))
    signals_str = format_signals(context.get("signals", []))
    market_state_str = format_market_state(context.get("market_state"))
    operation_str = format_operation(context.get("operation"))
    
    system_prompt = f"""
{handler_personality}

CURRENT CONTEXT:
- User Positions: {positions_str}
- Recent Signals: {signals_str}
- Market State: {market_state_str}
- Current Operation: {operation_str}

Respond to the user's message based on this context. Keep responses concise and actionable.
"""
    
    try:
        # Run synchronous Anthropic call in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cheap for real-time chat
                max_tokens=200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
        )
        
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Error generating handler response: {e}")
        return "Error processing request. Please try again."


def format_positions(positions: list) -> str:
    """Format user positions for context."""
    if not positions:
        return "None"
    
    formatted = []
    for pos in positions:
        formatted.append(
            f"{pos.get('type', 'Unknown')} position: ${pos.get('amount', 0):.2f} "
            f"on market {pos.get('marketId', 'unknown')}"
        )
    
    return "; ".join(formatted) if formatted else "None"


def format_signals(signals: list) -> str:
    """Format recent signals for context."""
    if not signals:
        return "None"
    
    formatted = []
    for sig in signals[:5]:  # Last 5 signals
        formatted.append(
            f"{sig.get('type', 'Unknown')}: {sig.get('message', '')}"
        )
    
    return "; ".join(formatted) if formatted else "None"


def format_market_state(market_state: Optional[Dict[str, Any]]) -> str:
    """Format market state for context."""
    if not market_state:
        return "Unknown"
    
    return (
        f"Market {market_state.get('marketId', 'unknown')}: "
        f"Price ${market_state.get('currentPrice', 0):.2f}, "
        f"Volume {market_state.get('volume', 0)}, "
        f"Trend {market_state.get('trend', 'unknown')}"
    )


def format_operation(operation: Optional[Dict[str, Any]]) -> str:
    """Format current operation for context."""
    if not operation:
        return "None"
    
    return (
        f"{operation.get('codename', 'Unknown')}: "
        f"{operation.get('description', '')}"
    )

