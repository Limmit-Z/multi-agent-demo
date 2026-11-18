"""Demo login and hashed, expiring in-memory sessions."""
import hashlib
import json
import secrets
import time
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data/users.json'


class Sessions:
    def __init__(self, ttl=1800, clock=None):
        self.users = {u['user_id']:u for u in json.loads(DATA.read_text(encoding='utf-8'))}
        self.ttl = ttl
        self.clock = clock or time.monotonic
        self._sessions = {}

    def login(self, user_id):
        if not isinstance(user_id, str) or user_id not in self.users:
            return None
        token = secrets.token_urlsafe(32)
        self._sessions[hashlib.sha256(token.encode()).hexdigest()] = (user_id, self.clock() + self.ttl)
        return token

    def get_user(self, token):
        if not isinstance(token, str):
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        session = self._sessions.get(digest)
        if not session:
            return None
        if self.clock() >= session[1]:
            del self._sessions[digest]
            return None
        return self.users[session[0]]
