"""象棋基础类型定义"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Side(enum.Enum):
    RED = "red"
    BLACK = "black"

    @property
    def opposite(self) -> Side:
        return Side.BLACK if self is Side.RED else Side.RED

    def __str__(self) -> str:
        return "红方" if self is Side.RED else "黑方"


class PieceType(enum.Enum):
    KING = "king"
    ADVISOR = "advisor"
    ELEPHANT = "elephant"
    HORSE = "horse"
    ROOK = "rook"
    CANNON = "cannon"
    PAWN = "pawn"


@dataclass(frozen=True, slots=True)
class Piece:
    side: Side
    piece_type: PieceType

    def __repr__(self) -> str:
        return PIECE_CHARS[(self.side, self.piece_type)]


@dataclass(frozen=True, slots=True)
class Position:
    row: int  # 0-9, 0=黑方底线(顶部), 9=红方底线(底部)
    col: int  # 0-8

    @property
    def is_valid(self) -> bool:
        return 0 <= self.row <= 9 and 0 <= self.col <= 8


@dataclass(frozen=True, slots=True)
class Move:
    src: Position
    dst: Position

    def __repr__(self) -> str:
        return f"({self.src.row},{self.src.col})->({self.dst.row},{self.dst.col})"


# 棋子中文字符映射
PIECE_CHARS: dict[tuple[Side, PieceType], str] = {
    (Side.RED, PieceType.KING): "帅",
    (Side.RED, PieceType.ADVISOR): "仕",
    (Side.RED, PieceType.ELEPHANT): "相",
    (Side.RED, PieceType.HORSE): "马",
    (Side.RED, PieceType.ROOK): "车",
    (Side.RED, PieceType.CANNON): "炮",
    (Side.RED, PieceType.PAWN): "兵",
    (Side.BLACK, PieceType.KING): "将",
    (Side.BLACK, PieceType.ADVISOR): "士",
    (Side.BLACK, PieceType.ELEPHANT): "象",
    (Side.BLACK, PieceType.HORSE): "马",
    (Side.BLACK, PieceType.ROOK): "车",
    (Side.BLACK, PieceType.CANNON): "炮",
    (Side.BLACK, PieceType.PAWN): "卒",
}
