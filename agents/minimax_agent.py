"""Minimax + Alpha-Beta 剪枝搜索 AI"""

from __future__ import annotations

from xiangqi.board import Board
from xiangqi.rules import generate_pseudo_legal_moves, is_in_check
from xiangqi.state import GameState
from xiangqi.types import Move, PieceType, Side

from .base import Agent
from .evaluation import EvalFunction, PIECE_VALUES, eval_material_position

MATE_SCORE = 50_000
INF = float("inf")


def _move_order_key(grid: list[list], move: Move) -> int:
    """走法排序：吃子走法按 MVV-LVA 排序，优先搜索好的走法以提高剪枝效率"""
    captured = grid[move.dst.row][move.dst.col]
    if captured is not None:
        attacker = grid[move.src.row][move.src.col]
        return PIECE_VALUES.get(captured.piece_type, 0) * 10 - PIECE_VALUES.get(
            attacker.piece_type, 0  # type: ignore[union-attr]
        )
    return 0


class MinimaxAgent(Agent):
    def __init__(
        self,
        max_depth: int = 4,
        eval_fn: EvalFunction | None = None,
    ) -> None:
        self.max_depth = max_depth
        self.eval_fn: EvalFunction = eval_fn or eval_material_position
        self.nodes_searched = 0
        self._history_set: set[int] = set()

    def select_move(self, state: GameState) -> Move:
        self.nodes_searched = 0
        self._history_set = set(state.position_history)

        board = state.board
        side = state.current_side
        grid = board._grid

        pseudo_moves = generate_pseudo_legal_moves(board, side)
        pseudo_moves.sort(key=lambda m: _move_order_key(grid, m), reverse=True)

        best_move: Move | None = None
        alpha = -INF

        for move in pseudo_moves:
            captured = board.make_move(move)
            if is_in_check(board, side):
                board.undo_move(move, captured)
                continue

            score = -self._negamax(board, side.opposite, self.max_depth - 1, -INF, -alpha)
            board.undo_move(move, captured)

            if score > alpha:
                alpha = score
                best_move = move

        return best_move  # type: ignore[return-value]

    def _negamax(
        self, board: Board, side: Side, depth: int, alpha: float, beta: float
    ) -> float:
        self.nodes_searched += 1

        h = board.zobrist_hash
        if h in self._history_set:
            return 0

        if depth == 0:
            return self.eval_fn(board, side)

        self._history_set.add(h)

        grid = board._grid
        pseudo_moves = generate_pseudo_legal_moves(board, side)
        pseudo_moves.sort(key=lambda m: _move_order_key(grid, m), reverse=True)

        has_legal = False
        for move in pseudo_moves:
            captured = board.make_move(move)
            if is_in_check(board, side):
                board.undo_move(move, captured)
                continue

            has_legal = True
            score = -self._negamax(board, side.opposite, depth - 1, -beta, -alpha)
            board.undo_move(move, captured)

            if score >= beta:
                self._history_set.discard(h)
                return beta
            if score > alpha:
                alpha = score

        self._history_set.discard(h)

        if not has_legal:
            return -(MATE_SCORE + depth)

        return alpha
