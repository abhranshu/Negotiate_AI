"""
NegotiateAI — WebSocket Connection Manager for Real-Time Negotiation Room.

Manages bi-directional WebSocket connections for Claimant, Respondent, and AI Mediator.
Supports:
1. Public Broadcasting: Messages visible to both Claimant & Respondent.
2. Private Direct Messaging: AI Mediator strategy suggestions sent strictly to one party.
3. Party Presence Tracking: Monitoring active participants in a case session.
"""

import logging
from typing import Dict, List, Optional
from fastapi import WebSocket

logger = logging.getLogger("negotiate_ai.websockets")


class ConnectionManager:
    """Manages live WebSocket connections per case_id."""

    def __init__(self):
        # Maps case_id -> list of connection dicts:
        # [{"socket": WebSocket, "party": "claimant" | "respondent", "user_id": str}]
        self.active_connections: Dict[str, List[Dict]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        case_id: str,
        party: str,
        user_id: Optional[str] = None
    ):
        """Accept connection and register client under case_id."""
        await websocket.accept()
        if case_id not in self.active_connections:
            self.active_connections[case_id] = []

        connection_info = {
            "socket": websocket,
            "party": party.lower(),
            "user_id": user_id
        }
        self.active_connections[case_id].append(connection_info)
        logger.info(f"Client connected to case '{case_id}' as '{party}' (user_id={user_id})")

        # Broadcast party presence update
        await self.broadcast_public(case_id, {
            "type": "presence_update",
            "event": "user_joined",
            "party": party.lower(),
            "active_parties": self.get_active_parties(case_id)
        })

    def disconnect(self, websocket: WebSocket, case_id: str):
        """Remove a disconnected WebSocket from active pool."""
        if case_id in self.active_connections:
            disconnected_party = None
            connections = self.active_connections[case_id]
            for conn in connections:
                if conn["socket"] == websocket:
                    disconnected_party = conn["party"]
                    break

            self.active_connections[case_id] = [
                conn for conn in connections if conn["socket"] != websocket
            ]

            if not self.active_connections[case_id]:
                del self.active_connections[case_id]

            logger.info(f"Client '{disconnected_party}' disconnected from case '{case_id}'")

    def get_active_parties(self, case_id: str) -> List[str]:
        """Return list of distinct active party roles ('claimant', 'respondent') for a case."""
        if case_id not in self.active_connections:
            return []
        return list({conn["party"] for conn in self.active_connections[case_id]})

    async def send_to_socket(self, websocket: WebSocket, message: dict):
        """Send JSON message directly to a specific socket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending direct socket message: {e}")

    async def broadcast_public(self, case_id: str, message: dict):
        """Broadcast JSON message to ALL participants connected to case_id."""
        if case_id not in self.active_connections:
            return

        dead_sockets = []
        for conn in self.active_connections[case_id]:
            try:
                await conn["socket"].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send public broadcast to {conn['party']}: {e}")
                dead_sockets.append(conn["socket"])

        for dead_ws in dead_sockets:
            self.disconnect(dead_ws, case_id)

    async def send_private(self, case_id: str, target_party: str, message: dict):
        """Send JSON message strictly to connections belonging to target_party ('claimant' or 'respondent')."""
        if case_id not in self.active_connections:
            return

        target_party = target_party.lower()
        dead_sockets = []
        sent_count = 0

        for conn in self.active_connections[case_id]:
            if conn["party"] == target_party:
                try:
                    await conn["socket"].send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send private message to {target_party}: {e}")
                    dead_sockets.append(conn["socket"])

        for dead_ws in dead_sockets:
            self.disconnect(dead_ws, case_id)

        if sent_count == 0:
            logger.warning(f"Private message intended for '{target_party}' in case '{case_id}' was not delivered (party offline)")


# Global singleton instance for connection management
manager = ConnectionManager()
