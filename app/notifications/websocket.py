import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections for real-time notifications"""

    def __init__(self):
        # Maps user_id strings to list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new connection and store it"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a disconnected connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to all active connections for a specific user"""
        user_id_str = str(user_id)
        if user_id_str in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id_str]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Mark for removal if connection is dead
                    disconnected.append(connection)
            
            # Cleanup dead connections
            for connection in disconnected:
                self.disconnect(connection, user_id_str)


# Global manager instance
manager = ConnectionManager()
