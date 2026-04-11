"""启发式评估函数：支持多种策略，通过注册机制选择"""

from __future__ import annotations

from typing import Callable

from xiangqi.board import Board
from xiangqi.rules import generate_pseudo_legal_moves
from xiangqi.types import PieceType, Side

EvalFunction = Callable[[Board, Side], int]

_REGISTRY: dict[str, EvalFunction] = {}


def register(name: str):
    """装饰器：将评估函数注册到全局表"""
    def decorator(fn: EvalFunction) -> EvalFunction:
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_evaluator(name: str) -> EvalFunction:
    """按名称获取评估函数，找不到则抛出异常"""
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"未知评估函数 '{name}'，可选: {available}")
    return _REGISTRY[name]


def list_evaluators() -> list[str]:
    return sorted(_REGISTRY)


# ── 子力基础价值 ──────────────────────────────────────────

PIECE_VALUES: dict[PieceType, int] = {
    PieceType.ROOK: 1000,
    PieceType.CANNON: 450,
    PieceType.HORSE: 400,
    PieceType.ADVISOR: 120,
    PieceType.ELEPHANT: 120,
    PieceType.PAWN: 100,
    PieceType.KING: 0,
}

# ── 位置加成表（红方视角，row 0=黑方底线，row 9=红方底线）──
# 黑方棋子翻转行号后使用同一张表

_ROOK_PST = (
    (14, 14, 12, 18, 16, 18, 12, 14, 14),
    (16, 20, 18, 24, 26, 24, 18, 20, 16),
    (12, 12, 12, 18, 18, 18, 12, 12, 12),
    (12, 18, 16, 22, 22, 22, 16, 18, 12),
    (12, 14, 12, 18, 18, 18, 12, 14, 12),
    (12, 16, 14, 20, 20, 20, 14, 16, 12),
    ( 6, 10,  8, 14, 14, 14,  8, 10,  6),
    ( 4,  8,  6, 14, 12, 14,  6,  8,  4),
    ( 8,  4,  8, 16,  8, 16,  8,  4,  8),
    (-2, 10,  6, 14, 12, 14,  6, 10, -2),
)

_HORSE_PST = (
    ( 4,  8, 16, 12,  4, 12, 16,  8,  4),
    ( 4, 10, 28, 16,  8, 16, 28, 10,  4),
    (12, 14, 16, 20, 18, 20, 16, 14, 12),
    ( 8, 24, 18, 24, 20, 24, 18, 24,  8),
    ( 6, 16, 14, 18, 16, 18, 14, 16,  6),
    ( 4, 12, 16, 14, 12, 14, 16, 12,  4),
    ( 2,  6,  8,  6, 10,  6,  8,  6,  2),
    ( 4,  2,  8,  8,  4,  8,  8,  2,  4),
    ( 0,  2,  4,  4, -2,  4,  4,  2,  0),
    ( 0, -4,  0,  0,  0,  0,  0, -4,  0),
)

_CANNON_PST = (
    ( 6,  4,  0, -10, -12, -10,  0,  4,  6),
    ( 2,  2,  0,  -4, -14,  -4,  0,  2,  2),
    ( 2,  2,  0, -10,  -8, -10,  0,  2,  2),
    ( 0,  0, -2,   4,  10,   4, -2,  0,  0),
    ( 0,  0,  0,   2,   8,   2,  0,  0,  0),
    (-2,  0,  4,   2,   6,   2,  4,  0, -2),
    ( 0,  0,  0,   2,   4,   2,  0,  0,  0),
    ( 4,  0,  8,   6,  10,   6,  8,  0,  4),
    ( 0,  2,  4,   6,   6,   6,  4,  2,  0),
    ( 0,  0,  2,   6,   6,   6,  2,  0,  0),
)

_PAWN_PST = (
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0, 30, 50, 60, 70, 60, 50, 30,  0),
    ( 0, 30, 50, 60, 70, 60, 50, 30,  0),
    (10, 40, 60, 70, 80, 70, 60, 40, 10),
    (10, 30, 50, 60, 70, 60, 50, 30, 10),
    ( 0, 10, 20, 30, 40, 30, 20, 10,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
)

_ADVISOR_PST = (
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0, 20,  0, 20,  0,  0,  0),
    ( 0,  0,  0,  0, 25,  0,  0,  0,  0),
    ( 0,  0,  0, 20,  0, 20,  0,  0,  0),
)

_ELEPHANT_PST = (
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0, 20,  0,  0,  0, 20,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    (18,  0,  0,  0, 23,  0,  0,  0, 18),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0, 20,  0,  0,  0, 20,  0,  0),
)

_KING_PST = (
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0,  0,  0,  0,  0,  0,  0),
    ( 0,  0,  0, -2, -2, -2,  0,  0,  0),
    ( 0,  0,  0,  1,  5,  1,  0,  0,  0),
    ( 0,  0,  0,  2,  8,  2,  0,  0,  0),
)

_PST: dict[PieceType, tuple[tuple[int, ...], ...]] = {
    PieceType.ROOK: _ROOK_PST,
    PieceType.HORSE: _HORSE_PST,
    PieceType.CANNON: _CANNON_PST,
    PieceType.PAWN: _PAWN_PST,
    PieceType.ADVISOR: _ADVISOR_PST,
    PieceType.ELEPHANT: _ELEPHANT_PST,
    PieceType.KING: _KING_PST,
}

MOBILITY_WEIGHT = 8


# ── 评估函数实现 ──────────────────────────────────────────

@register("piece_count")
def eval_piece_count(board: Board, side: Side) -> int:
    """最基础：仅统计双方棋子数量差（不区分棋子类型）"""
    score = 0
    for r in range(10):
        row = board._grid[r]
        for c in range(9):
            piece = row[c]
            if piece is None:
                continue
            if piece.side is side:
                score += 1
            else:
                score -= 1
    return score


@register("material")
def eval_material(board: Board, side: Side) -> int:
    """棋子加权价值，不考虑位置"""
    score = 0
    for r in range(10):
        row = board._grid[r]
        for c in range(9):
            piece = row[c]
            if piece is None:
                continue
            value = PIECE_VALUES[piece.piece_type]
            if piece.side is side:
                score += value
            else:
                score -= value
    return score


@register("material_position")
def eval_material_position(board: Board, side: Side) -> int:
    """棋子价值 + PST 位置加成"""
    score = 0
    for r in range(10):
        row = board._grid[r]
        for c in range(9):
            piece = row[c]
            if piece is None:
                continue
            material = PIECE_VALUES[piece.piece_type]
            pst = _PST[piece.piece_type]
            bonus = pst[r][c] if piece.side is Side.RED else pst[9 - r][c]
            total = material + bonus
            if piece.side is side:
                score += total
            else:
                score -= total
    return score


@register("material_position_mobility")
def eval_material_position_mobility(board: Board, side: Side) -> int:
    """棋子价值 + 位置加成 + 机动性（伪合法走步数）"""
    score = 0
    for r in range(10):
        row = board._grid[r]
        for c in range(9):
            piece = row[c]
            if piece is None:
                continue
            material = PIECE_VALUES[piece.piece_type]
            pst = _PST[piece.piece_type]
            bonus = pst[r][c] if piece.side is Side.RED else pst[9 - r][c]
            total = material + bonus
            if piece.side is side:
                score += total
            else:
                score -= total

    my_moves = len(generate_pseudo_legal_moves(board, side))
    opp_moves = len(generate_pseudo_legal_moves(board, side.opposite))
    score += (my_moves - opp_moves) * MOBILITY_WEIGHT

    return score
