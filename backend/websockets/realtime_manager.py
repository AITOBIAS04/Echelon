from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Supports:
    - Global broadcasts (all connected clients)
    - Channel subscriptions (specific timelines, agents)
    - User-specific messages (alerts, position updates)
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions: channel -> set of connection IDs
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
        # User connections: user_id -> connection_id
        self.user_connections: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            self.user_connections[user_id] = connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all subscriptions
        for channel in self.channel_subscriptions.values():
            channel.discard(connection_id)
        
        # Remove user mapping
        for user_id, conn_id in list(self.user_connections.items()):
            if conn_id == connection_id:
                del self.user_connections[user_id]
    
    def subscribe(self, connection_id: str, channel: str):
        """Subscribe a connection to a channel."""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(connection_id)
    
    def unsubscribe(self, connection_id: str, channel: str):
        """Unsubscribe from a channel."""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(connection_id)
    
    # =========================================
    # BROADCAST METHODS
    # =========================================
    
    async def broadcast_global(self, event_type: str, data: dict):
        """Send to ALL connected clients."""
        message = self._format_message(event_type, data)
        await self._send_to_all(message)
    
    async def broadcast_to_channel(self, channel: str, event_type: str, data: dict):
        """Send to all subscribers of a channel."""
        if channel not in self.channel_subscriptions:
            return
        
        message = self._format_message(event_type, data)
        connection_ids = self.channel_subscriptions[channel]
        
        for conn_id in connection_ids:
            if conn_id in self.active_connections:
                await self._send_to_connection(conn_id, message)
    
    async def send_to_user(self, user_id: str, event_type: str, data: dict):
        """Send to a specific user."""
        if user_id not in self.user_connections:
            return
        
        conn_id = self.user_connections[user_id]
        if conn_id in self.active_connections:
            message = self._format_message(event_type, data)
            await self._send_to_connection(conn_id, message)
    
    # =========================================
    # EVENT TYPES
    # =========================================
    
    async def broadcast_wing_flap(self, flap: dict):
        """Broadcast a new Wing Flap to relevant subscribers."""
        # Global (for SIGINT feed)
        await self.broadcast_global("WING_FLAP", flap)
        
        # Timeline channel
        await self.broadcast_to_channel(
            f"timeline:{flap['timeline_id']}", 
            "WING_FLAP", 
            flap
        )
        
        # Agent channel
        await self.broadcast_to_channel(
            f"agent:{flap['agent_id']}", 
            "WING_FLAP", 
            flap
        )
    
    async def broadcast_paradox_spawn(self, paradox: dict):
        """Broadcast new Containment Breach."""
        await self.broadcast_global("PARADOX_SPAWN", paradox)
        
        await self.broadcast_to_channel(
            f"timeline:{paradox['timeline_id']}", 
            "PARADOX_SPAWN", 
            paradox
        )
    
    async def broadcast_paradox_moved(self, paradox: dict, old_timeline_id: str):
        """Broadcast Paradox extraction."""
        await self.broadcast_global("PARADOX_MOVED", {
            "paradox": paradox,
            "from_timeline": old_timeline_id
        })
        
        # Notify both timelines
        await self.broadcast_to_channel(
            f"timeline:{old_timeline_id}", 
            "PARADOX_MOVED", 
            {"paradox": paradox, "direction": "OUT"}
        )
        await self.broadcast_to_channel(
            f"timeline:{paradox['timeline_id']}", 
            "PARADOX_MOVED", 
            {"paradox": paradox, "direction": "IN"}
        )
    
    async def broadcast_detonation(self, event: dict):
        """Broadcast Paradox detonation."""
        await self.broadcast_global("DETONATION", event)
        
        await self.broadcast_to_channel(
            f"timeline:{event['timeline_id']}", 
            "DETONATION", 
            event
        )
    
    async def broadcast_ripple(self, ripple: dict):
        """Broadcast new fork."""
        await self.broadcast_global("RIPPLE", ripple)
        
        await self.broadcast_to_channel(
            f"timeline:{ripple['parent_timeline_id']}", 
            "RIPPLE", 
            ripple
        )
    
    async def send_position_update(self, user_id: str, position: dict):
        """Send position update to specific user."""
        await self.send_to_user(user_id, "POSITION_UPDATE", position)
    
    async def send_alert(self, user_id: str, alert: dict):
        """Send alert to specific user."""
        await self.send_to_user(user_id, "ALERT", alert)
    
    # =========================================
    # HELPERS
    # =========================================
    
    def _format_message(self, event_type: str, data: dict) -> str:
        return json.dumps({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
    
    async def _send_to_all(self, message: str):
        disconnected = []
        for conn_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(conn_id)
        
        for conn_id in disconnected:
            self.disconnect(conn_id)
    
    async def _send_to_connection(self, connection_id: str, message: str):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(message)
            except:
                self.disconnect(connection_id)


# Global instance
manager = ConnectionManager()


# =========================================
# WEBSOCKET ROUTES
# =========================================

from fastapi import APIRouter

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint.
    
    Client sends commands:
    - {"action": "subscribe", "channel": "timeline:TIMELINE_ID"}
    - {"action": "unsubscribe", "channel": "timeline:TIMELINE_ID"}
    - {"action": "ping"}
    
    Server sends events:
    - {"type": "WING_FLAP", "data": {...}}
    - {"type": "PARADOX_SPAWN", "data": {...}}
    - {"type": "ALERT", "data": {...}}
    """
    connection_id = str(id(websocket))
    
    # Get user from auth token (implementation depends on your auth)
    user_id = None  # Extract from query params or headers
    
    await manager.connect(websocket, connection_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "subscribe":
                manager.subscribe(connection_id, message["channel"])
                await websocket.send_text(json.dumps({
                    "type": "SUBSCRIBED",
                    "channel": message["channel"]
                }))
            
            elif action == "unsubscribe":
                manager.unsubscribe(connection_id, message["channel"])
                await websocket.send_text(json.dumps({
                    "type": "UNSUBSCRIBED",
                    "channel": message["channel"]
                }))
            
            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "PONG"}))
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)



