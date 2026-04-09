"""棋盘表示：9×10 二维数组 + Zobrist 增量哈希"""

from __future__ import annotations

from .types import Move, Piece, PieceType, Position, Side, PIECE_CHARS
from .zobrist import piece_hash


class Board:
    __slots__ = ("_grid", "_hash")

    def __init__(self) -> None:
        self._grid: list[list[Piece | None]] = [[None] * 9 for _ in range(10)]
        self._hash: int = 0

    # ── 基础访问 ─────────────────────────────────────────

    def piece_at(self, pos: Position) -> Piece | None:
        return self._grid[pos.row][pos.col]

    @property
    def zobrist_hash(self) -> int:
        return self._hash

    # ── 走子 / 悔棋（make / unmake）────────────────────────

    def make_move(self, move: Move) -> Piece | None:
        """执行走子，返回被吃的棋子（无则 None）"""
        src_r, src_c = move.src.row, move.src.col
        dst_r, dst_c = move.dst.row, move.dst.col

        captured = self._grid[dst_r][dst_c]
        if captured is not None:
            self._hash ^= piece_hash(dst_r, dst_c, captured)

        piece = self._grid[src_r][src_c]
        self._hash ^= piece_hash(src_r, src_c, piece)  # type: ignore[arg-type]
        self._hash ^= piece_hash(dst_r, dst_c, piece)  # type: ignore[arg-type]

        self._grid[dst_r][dst_c] = piece
        self._grid[src_r][src_c] = None
        return captured

    def undo_move(self, move: Move, captured: Piece | None) -> None:
        """撤销走子"""
        src_r, src_c = move.src.row, move.src.col
        dst_r, dst_c = move.dst.row, move.dst.col

        piece = self._grid[dst_r][dst_c]
        self._hash ^= piece_hash(dst_r, dst_c, piece)  # type: ignore[arg-type]
        self._hash ^= piece_hash(src_r, src_c, piece)  # type: ignore[arg-type]

        self._grid[src_r][src_c] = piece
        self._grid[dst_r][dst_c] = captured
        if captured is not None:
            self._hash ^= piece_hash(dst_r, dst_c, captured)

    # ── 查询 ─────────────────────────────────────────────

    def find_king(self, side: Side) -> Position | None:
        """在九宫范围内查找将/帅"""
        rows = range(0, 3) if side is Side.BLACK else range(7, 10)
        for r in rows:
            for c in range(3, 6):
                p = self._grid[r][c]
                if p is not None and p.side is side and p.piece_type is PieceType.KING:
                    return Position(r, c)
        return None

    def pieces(self, side: Side | None = None) -> list[tuple[Position, Piece]]:
        result: list[tuple[Position, Piece]] = []
        for r in range(10):
            row = self._grid[r]
            for c in range(9):
                p = row[c]
                if p is not None and (side is None or p.side is side):
                    result.append((Position(r, c), p))
        return result

    # ── 复制 ─────────────────────────────────────────────

    def copy(self) -> Board:
        new = Board.__new__(Board)
        new._grid = [row[:] for row in self._grid]
        new._hash = self._hash
        return new

    # ── 初始局面 ──────────────────────────────────────────

    @classmethod
    def initial(cls) -> Board:
        board = cls()
        back_rank = [
            PieceType.ROOK, PieceType.HORSE, PieceType.ELEPHANT,
            PieceType.ADVISOR, PieceType.KING, PieceType.ADVISOR,
            PieceType.ELEPHANT, PieceType.HORSE, PieceType.ROOK,
        ]
        # 黑方（顶部 row 0-4）
        for c, pt in enumerate(back_rank):
            board._put(0, c, Piece(Side.BLACK, pt))
        board._put(2, 1, Piece(Side.BLACK, PieceType.CANNON))
        board._put(2, 7, Piece(Side.BLACK, PieceType.CANNON))
        for c in range(0, 9, 2):
            board._put(3, c, Piece(Side.BLACK, PieceType.PAWN))
        # 红方（底部 row 5-9）
        for c, pt in enumerate(back_rank):
            board._put(9, c, Piece(Side.RED, pt))
        board._put(7, 1, Piece(Side.RED, PieceType.CANNON))
        board._put(7, 7, Piece(Side.RED, PieceType.CANNON))
        for c in range(0, 9, 2):
            board._put(6, c, Piece(Side.RED, PieceType.PAWN))
        return board

    def _put(self, row: int, col: int, piece: Piece) -> None:
        self._grid[row][col] = piece
        self._hash ^= piece_hash(row, col, piece)

    # ── 文本显示 ──────────────────────────────────────────

    def __repr__(self) -> str:
        lines: list[str] = ["  " + " ".join(str(c) for c in range(9))]
        for r in range(10):
            row_str: list[str] = []
            for c in range(9):
                p = self._grid[r][c]
                row_str.append(repr(p) if p else "．")
            lines.append(f"{r} " + " ".join(row_str))
            if r == 4:
                lines.append("  ＝＝楚河　汉界＝＝")
        return "\n".join(lines)
