"""重复局面检测：长将 / 长捉判负"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from .board import Board
from .rules import generate_pseudo_legal_moves, is_in_check
from .types import Move, PieceType, Position, Side

if TYPE_CHECKING:
    from .state import GameState

_PIECE_VALUES: dict[PieceType, int] = {
    PieceType.ROOK: 1000,
    PieceType.CANNON: 450,
    PieceType.HORSE: 400,
    PieceType.ADVISOR: 120,
    PieceType.ELEPHANT: 120,
    PieceType.PAWN: 100,
    PieceType.KING: 0,
}

_EXCLUDED_CHASE_TARGETS = frozenset({PieceType.PAWN, PieceType.KING})


class MoveClass(enum.Enum):
    CHECK = "check"
    CHASE = "chase"
    IDLE = "idle"


# ── 捉子威胁分析 ──────────────────────────────────────────


def _get_capture_threats(board: Board, side: Side) -> set[Position]:
    """返回 *side* 方能有利吃到的对方棋子位置（排除兵/卒、将/帅）。

    "有利"定义：目标无保护，或虽有保护但 target_value > min_attacker_value。
    """
    grid = board._grid

    # 按目标位置记录最小价值合法攻击者
    target_best: dict[tuple[int, int], tuple[int, Position]] = {}

    for move in generate_pseudo_legal_moves(board, side):
        dr, dc = move.dst.row, move.dst.col
        target = grid[dr][dc]
        if target is None or target.side is side:
            continue
        if target.piece_type in _EXCLUDED_CHASE_TARGETS:
            continue

        captured = board.make_move(move)
        legal = not is_in_check(board, side)
        board.undo_move(move, captured)
        if not legal:
            continue

        attacker = grid[move.src.row][move.src.col]
        att_val = _PIECE_VALUES[attacker.piece_type]
        key = (dr, dc)
        if key not in target_best or att_val < target_best[key][0]:
            target_best[key] = (att_val, move.src)

    threats: set[Position] = set()
    opp = side.opposite

    for (tr, tc), (min_att_val, att_pos) in target_best.items():
        target_val = _PIECE_VALUES[grid[tr][tc].piece_type]  # type: ignore[union-attr]

        capture_move = Move(att_pos, Position(tr, tc))
        captured = board.make_move(capture_move)

        can_recapture = False
        for recap in generate_pseudo_legal_moves(board, opp):
            if recap.dst.row == tr and recap.dst.col == tc:
                rc = board.make_move(recap)
                if not is_in_check(board, opp):
                    can_recapture = True
                board.undo_move(recap, rc)
                if can_recapture:
                    break

        board.undo_move(capture_move, captured)

        if not can_recapture or target_val > min_att_val:
            threats.add(Position(tr, tc))

    return threats


# ── 走子分类 ──────────────────────────────────────────────


def classify_move(board: Board, move: Move, side: Side) -> MoveClass:
    """判定走子性质（将 / 捉 / 闲）。board 必须处于走子前的状态。"""
    threats_before = _get_capture_threats(board, side)

    captured = board.make_move(move)

    if is_in_check(board, side.opposite):
        board.undo_move(move, captured)
        return MoveClass.CHECK

    threats_after = _get_capture_threats(board, side)
    board.undo_move(move, captured)

    if threats_after - threats_before:
        return MoveClass.CHASE

    return MoveClass.IDLE


# ── 主入口 ────────────────────────────────────────────────


def detect_repetition(state: GameState) -> tuple[bool, Side | None]:
    """检测三次重复局面及违规方。

    返回 *(is_over, violator)*:

    * ``(False, None)`` — 未触发三次重复，继续对弈
    * ``(True, None)``  — 三次重复和棋（双方均闲 / 双方均为攻击着法）
    * ``(True, side)``  — *side* 长将或长捉，*side* 判负
    """
    pos_hist = state.position_history
    if len(pos_hist) < 5:
        return (False, None)

    current_hash = pos_hist[-1]
    if pos_hist.count(current_hash) < 3:
        return (False, None)

    # 找到上一次出现同一局面的位置，构成重复周期
    cycle_start = -1
    for i in range(len(pos_hist) - 2, -1, -1):
        if pos_hist[i] == current_hash:
            cycle_start = i
            break

    cycle_moves = state.move_history[cycle_start:]
    if not cycle_moves:
        return (True, None)

    board = state.board

    # 回退至 cycle_start 局面（重复周期内无吃子，captured 均为 None）
    for move in reversed(cycle_moves):
        board.undo_move(move, None)

    steps_back = len(pos_hist) - 1 - cycle_start
    first_side = state.current_side if steps_back % 2 == 0 else state.current_side.opposite

    side = first_side
    classifications: dict[Side, list[MoveClass]] = {Side.RED: [], Side.BLACK: []}
    for move in cycle_moves:
        cls = classify_move(board, move, side)
        classifications[side].append(cls)
        board.make_move(move)
        side = side.opposite
    # board 已恢复至当前局面

    def all_aggressive(classes: list[MoveClass]) -> bool:
        return len(classes) > 0 and all(
            c in (MoveClass.CHECK, MoveClass.CHASE) for c in classes
        )

    red_agg = all_aggressive(classifications[Side.RED])
    black_agg = all_aggressive(classifications[Side.BLACK])

    if red_agg and not black_agg:
        return (True, Side.RED)
    if black_agg and not red_agg:
        return (True, Side.BLACK)
    return (True, None)
