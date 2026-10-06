"""Local accounts, expiring opaque cookies, bounded rate limits."""

import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parent
USER_FILE = BASE / ".private" / "users.json"
COOKIE = "travel_session"


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt),
                          n=32768, r=8, p=3, dklen=32, maxmem=64 * 1024 * 1024).hex()


def read_users(path=USER_FILE):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def add_user(username, password, path=USER_FILE):
    if not re.fullmatch(r"[a-z0-9_]{3,32}", username):
        raise ValueError("Use 3–32 lowercase letters, digits, or underscores for the username.")
    if not 12 <= len(password) <= 128:
        raise ValueError("Use a unique password of 12–128 characters.")
    users = read_users(path)
    if username in users:
        raise ValueError("That account already exists.")
    salt = secrets.token_hex(16)
    users[username] = dict(id=uuid.uuid4().hex, salt=salt, hash=password_hash(password, salt))
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(users, f)
    temporary.replace(path)


def verify_user(username, password, path=USER_FILE):
    record = read_users(path).get(username)
    # Do the same expensive hash for unknown usernames; no account enumeration reply.
    salt = record["salt"] if record else "00" * 16
    candidate = password_hash(password, salt)
    expected = record["hash"] if record else "00" * 32
    return record["id"] if hmac.compare_digest(candidate, expected) and record else None


class RateLimiter:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.hits = {}

    def allow(self, key, count, period):
        now = self.clock()
        # Bound all limiter storage, including expired entries.
        for old in list(self.hits):
            if not self.hits[old] or self.hits[old][-1] < now - 3600:
                del self.hits[old]
        if key not in self.hits and len(self.hits) >= 500:
            return False
        values = self.hits.setdefault(key, deque())
        while values and values[0] <= now - period:
            values.popleft()
        if len(values) >= count:
            return False
        values.append(now)
        return True


@dataclass
class BrowserSession:
    user_id: str
    csrf: str
    created: float
    last_seen: float
    trip: object = None
    messages: list = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    revoked: bool = False


class SessionStore:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.sessions = {}

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def prune(self):
        now = self.clock()
        for key, session in list(self.sessions.items()):
            if now - session.created >= 1800 or now - session.last_seen >= 900:
                session.revoked = True
                session.trip = None
                session.messages.clear()
                del self.sessions[key]

    def create(self, user_id):
        self.prune()
        if len(self.sessions) >= 100:
            raise ValueError("Session capacity reached.")
        now = self.clock()
        token = secrets.token_urlsafe(32)
        self.sessions[self.digest(token)] = BrowserSession(user_id, secrets.token_urlsafe(32), now, now)
        return token

    def get(self, token):
        self.prune()
        if not token or len(token) > 100:
            return None
        session = self.sessions.get(self.digest(token))
        if session and not session.revoked:
            session.last_seen = self.clock()
            return session
        return None

    def revoke(self, token):
        if token:
            session = self.sessions.pop(self.digest(token), None)
            if session:
                session.revoked = True
                session.trip = None
                session.messages.clear()
