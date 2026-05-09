"""
Session management and conversation history persistence.
Supports named sessions per repository.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class SessionManager:
    """Manages named chat sessions for repositories."""

    def __init__(self, repo_path: Path, session_name: str = "default"):
        self.repo_path = Path(repo_path)
        self.session_name = session_name
        self.history_dir = Path.home() / ".breadcrumb" / "sessions"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Use repo hash to differentiate repos with same name
        import hashlib
        repo_hash = hashlib.md5(str(self.repo_path.absolute()).encode()).hexdigest()[:8]
        self.session_file = self.history_dir / f"{repo_hash}_{session_name}.json"
        
        self.messages: List[Dict[str, str]] = self._load()

    def _load(self) -> List[Dict[str, str]]:
        """Load session from disk."""
        if self.session_file.exists():
            try:
                data = json.loads(self.session_file.read_text())
                return data.get("messages", [])
            except Exception:
                return []
        return []

    def save(self) -> None:
        """Save session to disk."""
        data = {
            "repo": str(self.repo_path),
            "session": self.session_name,
            "created": self.session_file.stat().st_ctime if self.session_file.exists() else datetime.now().timestamp(),
            "updated": datetime.now().timestamp(),
            "messages": self.messages,
        }
        self.session_file.write_text(json.dumps(data, indent=2))

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the session."""
        return self.messages

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API calls (without timestamps)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self) -> None:
        """Clear session history."""
        self.messages = []
        self.save()

    def count_tokens(self) -> int:
        """Rough token count for current session."""
        content = "".join(m["content"] for m in self.messages)
        return len(content) // 4  # Rough estimate

    @staticmethod
    def list_sessions(repo_path: Path) -> List[str]:
        """List all available sessions for a repository."""
        import hashlib
        history_dir = Path.home() / ".breadcrumb" / "sessions"
        if not history_dir.exists():
            return []
        
        repo_hash = hashlib.md5(str(repo_path.absolute()).encode()).hexdigest()[:8]
        pattern = f"{repo_hash}_*.json"
        
        sessions = []
        for file in history_dir.glob(pattern):
            session_name = file.stem.replace(f"{repo_hash}_", "")
            sessions.append(session_name)
        
        return sorted(sessions)

    @staticmethod
    def delete_session(repo_path: Path, session_name: str) -> None:
        """Delete a named session."""
        import hashlib
        history_dir = Path.home() / ".breadcrumb" / "sessions"
        repo_hash = hashlib.md5(str(repo_path.absolute()).encode()).hexdigest()[:8]
        session_file = history_dir / f"{repo_hash}_{session_name}.json"
        
        if session_file.exists():
            session_file.unlink()
