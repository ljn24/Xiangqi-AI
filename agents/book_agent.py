"""开局库 Agent：装饰器模式，优先查询开局库，未命中时退化为内部 Agent"""

from __future__ import annotations

import json
import random as _random
from pathlib import Path

from xiangqi.state import GameState
from xiangqi.types import Move, Position, Side

from .base import Agent


# ── ICCS 坐标转换 ────────────────────────────────────────
# ICCS: 列 a-i (左→右), 行 0-9 (0=红方底线, 9=黑方底线)
# 内部: row 0=黑方底线(顶), row 9=红方底线(底), col 0-8


def move_to_iccs(move: Move) -> str:
    """内部 Move → ICCS 表示 (如 'h2e2')"""
    return (
        chr(ord("a") + move.src.col)
        + str(9 - move.src.row)
        + chr(ord("a") + move.dst.col)
        + str(9 - move.dst.row)
    )


def iccs_to_move(iccs: str) -> Move:
    """ICCS 表示 → 内部 Move"""
    return Move(
        Position(9 - int(iccs[1]), ord(iccs[0]) - ord("a")),
        Position(9 - int(iccs[3]), ord(iccs[2]) - ord("a")),
    )


def _book_key(zobrist_hash: int, side: Side) -> str:
    return f"{zobrist_hash:016x}:{side.value}"


# ── 开局库 ───────────────────────────────────────────────


class OpeningBook:
    """开局库：基于 Zobrist 哈希的局面 → 候选走法映射

    JSON 格式::

        {
          "meta": { ... },
          "positions": {
            "<hash_hex>:<side>": [
              {"move": "h2e2", "weight": 523},
              ...
            ]
          }
        }
    """

    def __init__(self, entries: dict[str, list[tuple[Move, int]]]) -> None:
        self._entries = entries

    def __len__(self) -> int:
        return len(self._entries)

    @classmethod
    def load(cls, path: str | Path) -> OpeningBook:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"开局库文件不存在: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        entries: dict[str, list[tuple[Move, int]]] = {}
        for key, candidates in data.get("positions", {}).items():
            entries[key] = [
                (iccs_to_move(c["move"]), c["weight"]) for c in candidates
            ]
        return cls(entries)

    def probe(
        self,
        zobrist_hash: int,
        side: Side,
        *,
        legal_moves: list[Move] | None = None,
    ) -> Move | None:
        """查询开局库，返回一步走法（按权重随机选择）或 None"""
        key = _book_key(zobrist_hash, side)
        candidates = self._entries.get(key)
        if not candidates:
            return None
        if legal_moves is not None:
            legal_set = set(legal_moves)
            candidates = [(m, w) for m, w in candidates if m in legal_set]
        if not candidates:
            return None
        moves, weights = zip(*candidates)
        return _random.choices(moves, weights=weights, k=1)[0]


# ── 装饰器 Agent ─────────────────────────────────────────


class BookAgent(Agent):
    """装饰器 Agent：优先查询开局库，未命中时退化为内部 Agent"""

    def __init__(self, inner: Agent, book: OpeningBook) -> None:
        self.inner = inner
        self.book = book

    def select_move(self, state: GameState) -> Move:
        book_move = self.book.probe(
            state.board.zobrist_hash,
            state.current_side,
            legal_moves=state.legal_moves(),
        )
        if book_move is not None:
            return book_move
        return self.inner.select_move(state)
