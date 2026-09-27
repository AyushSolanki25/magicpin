"""
State Manager for Vera AI Assistant Bot
Manages context storage, versioning, conversation histories, auto-reply detection,
and intent state transitions.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import threading
import re

class StateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = datetime.utcnow()
        # Storage: (scope, context_id) -> {"version": int, "payload": dict}
        self.contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        # Storage: conversation_id -> dict state
        self.conversations: Dict[str, Dict[str, Any]] = {}

    def get_uptime_seconds(self) -> int:
        return int((datetime.utcnow() - self.start_time).total_seconds())

    def get_context_counts(self) -> Dict[str, int]:
        with self._lock:
            counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
            for (scope, _), _ in self.contexts.items():
                if scope in counts:
                    counts[scope] += 1
            return counts

    def push_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            key = (scope, context_id)
            current = self.contexts.get(key)
            if current and current["version"] > version:
                return {
                    "accepted": False,
                    "reason": "stale_version",
                    "current_version": current["version"]
                }
            self.contexts[key] = {
                "version": version,
                "payload": payload,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }

            return {
                "accepted": True,
                "ack_id": f"ack_{context_id}_v{version}",
                "stored_at": datetime.utcnow().isoformat() + "Z"
            }

    def get_context(self, scope: str, context_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self.contexts.get((scope, context_id))
            return data["payload"] if data else None

    def record_incoming_reply(self, conv_id: str, merchant_id: Optional[str],
                               customer_id: Optional[str], from_role: str,
                               message: str, turn_number: int) -> Dict[str, Any]:
        with self._lock:
            if conv_id not in self.conversations:
                self.conversations[conv_id] = {
                    "conversation_id": conv_id,
                    "merchant_id": merchant_id,
                    "customer_id": customer_id,
                    "turns": [],
                    "auto_reply_count": 0,
                    "is_action_mode": False,
                    "is_ended": False,
                    "last_sent_body": ""
                }
            
            conv = self.conversations[conv_id]
            conv["turns"].append({
                "from": from_role,
                "message": message,
                "turn": turn_number,
                "ts": datetime.utcnow().isoformat() + "Z"
            })
            
            # Check for auto-reply signatures
            msg_lower = message.lower()
            auto_reply_keywords = [
                "thank you for contacting", "automated assistant", "sujhaav hamari team tak",
                "response shortly", "automated message", "auto-reply", "canned response",
                "out of office", "currently unavailable", "will respond as soon as possible"
            ]
            
            # Count verbatim repeats from merchant
            merchant_msgs = [t["message"].strip() for t in conv["turns"] if t["from"] == "merchant"]
            is_repeated = len(merchant_msgs) >= 2 and (merchant_msgs[-1] == merchant_msgs[-2])
            
            if any(kw in msg_lower for kw in auto_reply_keywords) or is_repeated:
                conv["auto_reply_count"] += 1
            
            # Check for explicit commitment / intent transition
            commitment_keywords = [
                "yes", "do it", "whats next", "what's next", "go ahead", "send me",
                "update my", "update profile", "i want to join", "let's do it",
                "proceed", "sure", "okay", "ok", "cool", "agree"
            ]
            if any(re.search(r'\b' + re.escape(kw) + r'\b', msg_lower) for kw in commitment_keywords):
                conv["is_action_mode"] = True
                
            return conv

    def update_last_sent(self, conv_id: str, body: str):
        with self._lock:
            if conv_id in self.conversations:
                self.conversations[conv_id]["last_sent_body"] = body

    def is_duplicate_send(self, conv_id: str, body: str) -> bool:
        with self._lock:
            conv = self.conversations.get(conv_id)
            if conv and conv.get("last_sent_body") == body:
                return True
            return False
