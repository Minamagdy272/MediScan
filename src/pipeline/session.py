"""
Session / Chat History Manager (Thread-Safe In-Memory Store).
"""

from typing import Dict, List


class ChatSessionStore:
    """Thread-safe in-memory session history store."""
    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._sessions.get(session_id, [])

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({"role": role, "content": content})

    def format_history(self, session_id: str, max_turns: int = 5) -> str:
        history = self.get_history(session_id)[-max_turns * 2:]
        if not history:
            return "No previous conversation history."
        formatted = []
        for msg in history:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{prefix}: {msg['content']}")
        return "\n".join(formatted)

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


session_store = ChatSessionStore()
