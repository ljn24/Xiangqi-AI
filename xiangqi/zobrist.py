"""Zobrist 哈希表：用于棋局状态的高效哈希"""

import random

from .types import Piece, PieceType, Side

_RNG = random.Random(2024)

# 哈希表: (row, col, side, piece_type) -> 64位随机数
HASH_TABLE: dict[tuple[int, int, Side, PieceType], int] = {
    (r, c, side, pt): _RNG.getrandbits(64)
    for r in range(10)
    for c in range(9)
    for side in Side
    for pt in PieceType
}

SIDE_HASH: int = _RNG.getrandbits(64)


def piece_hash(row: int, col: int, piece: Piece) -> int:
    return HASH_TABLE[(row, col, piece.side, piece.piece_type)]
