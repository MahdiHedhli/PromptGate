from __future__ import annotations

import secrets
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field


@dataclass
class ConversationMap:
    raw_to_token: dict[tuple[str, str], str] = field(default_factory=dict)
    token_to_raw: dict[str, str] = field(default_factory=dict)
    last_access: float = 0.0


class TokenVault:
    def __init__(self, ttl_seconds: int = 3600, max_conversations: int = 100, now=time.time) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_conversations = max_conversations
        self._now = now
        self._tokens: dict[tuple[str, str], str] = {}
        self._counts: defaultdict[str, int] = defaultdict(int)
        self._conversations: OrderedDict[str, ConversationMap] = OrderedDict()

    def token_for(
        self,
        category: str,
        raw: str,
        prefix: str | None = None,
        conversation_id: str | None = None,
        mode: str = "scoped_random",
        ttl_seconds: int | None = None,
        max_conversations: int | None = None,
    ) -> str:
        if ttl_seconds is not None:
            self.ttl_seconds = ttl_seconds
        if max_conversations is not None:
            self.max_conversations = max_conversations
        if mode == "deterministic":
            return self._deterministic_token_for(category, raw, prefix)
        return self._scoped_token_for(category, raw, prefix, conversation_id or "default")

    def restore(self, text: str, conversation_id: str | None = None) -> str:
        if not conversation_id:
            return text
        now = self._now()
        self._evict(now)
        convo = self._conversations.get(conversation_id)
        if convo is None:
            return text
        convo.last_access = now
        self._conversations.move_to_end(conversation_id)
        restored = text
        for token, raw in convo.token_to_raw.items():
            restored = restored.replace(token, raw)
        return restored

    def _deterministic_token_for(self, category: str, raw: str, prefix: str | None = None) -> str:
        key = (category, raw)
        if key in self._tokens:
            return self._tokens[key]
        self._counts[category] += 1
        label = (prefix or category).upper()
        token = f"[{label}_{self._counts[category]:03d}]"
        self._tokens[key] = token
        return token

    def _scoped_token_for(self, category: str, raw: str, prefix: str | None, conversation_id: str) -> str:
        now = self._now()
        self._evict(now)
        convo = self._conversations.get(conversation_id)
        if convo is None:
            convo = ConversationMap(last_access=now)
            self._conversations[conversation_id] = convo
        convo.last_access = now
        self._conversations.move_to_end(conversation_id)
        key = (category, raw)
        if key in convo.raw_to_token:
            return convo.raw_to_token[key]
        label = (prefix or category).upper()
        while True:
            token = f"[{label}_{secrets.token_hex(8)}]"
            if token not in convo.token_to_raw:
                break
        convo.raw_to_token[key] = token
        convo.token_to_raw[token] = raw
        self._evict(now)
        return token

    def _evict(self, now: float) -> None:
        expired = [conversation_id for conversation_id, convo in self._conversations.items() if now - convo.last_access > self.ttl_seconds]
        for conversation_id in expired:
            self._conversations.pop(conversation_id, None)
        while len(self._conversations) > self.max_conversations:
            self._conversations.popitem(last=False)
