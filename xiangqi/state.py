"""游戏状态：封装棋盘 + 当前行棋方 + 历史记录"""

from __future__ import annotations

from .board import Board
from .repetition import detect_repetition
from .rules import generate_legal_moves, is_in_check
from .types import Move, Side

_UNSET: tuple[bool, Side | None] = (False, None)


class GameState:
    __slots__ = (
        "board", "current_side", "move_history", "position_history",
        "_rep_cache", "_rep_done",
    )

    def __init__(
        self,
        board: Board,
        current_side: Side,
        move_history: list[Move] | None = None,
        position_history: list[int] | None = None,
    ) -> None:
        self.board = board
        self.current_side = current_side
        self.move_history: list[Move] = move_history if move_history is not None else []
        self.position_history: list[int] = (
            position_history if position_history is not None else []
        )
        self._rep_cache: tuple[bool, Side | None] = _UNSET
        self._rep_done: bool = False

    def _check_repetition(self) -> tuple[bool, Side | None]:
        if not self._rep_done:
            self._rep_cache = detect_repetition(self)
            self._rep_done = True
        return self._rep_cache

    @classmethod
    def initial(cls) -> GameState:
        """标准初始局面，红方先行"""
        board = Board.initial()
        return cls(board, Side.RED, [], [board.zobrist_hash])

    def apply_move(self, move: Move) -> GameState:
        """走子后返回新的 GameState（不修改当前对象）"""
        new_board = self.board.copy()
        new_board.make_move(move)
        return GameState(
            new_board,
            self.current_side.opposite,
            self.move_history + [move],
            self.position_history + [new_board.zobrist_hash],
        )

    def legal_moves(self) -> list[Move]:
        return generate_legal_moves(self.board, self.current_side)

    def is_in_check(self) -> bool:
        return is_in_check(self.board, self.current_side)

    def is_over(self) -> bool:
        if self.board.find_king(Side.RED) is None or self.board.find_king(Side.BLACK) is None:
            return True
        rep_over, _ = self._check_repetition()
        if rep_over:
            return True
        return len(self.legal_moves()) == 0

    def winner(self) -> Side | None:
        if self.board.find_king(Side.RED) is None:
            return Side.BLACK
        if self.board.find_king(Side.BLACK) is None:
            return Side.RED
        rep_over, violator = self._check_repetition()
        if rep_over:
            return violator.opposite if violator else None
        if len(self.legal_moves()) == 0:
            return self.current_side.opposite
        return None
