"""走法生成与合法性校验"""

from __future__ import annotations

from .board import Board
from .types import Move, PieceType, Position, Side

# ── 棋盘区域判断 ───────────────────────────────────────────

def _in_palace(row: int, col: int, side: Side) -> bool:
    if side is Side.RED:
        return 7 <= row <= 9 and 3 <= col <= 5
    return 0 <= row <= 2 and 3 <= col <= 5


def _crossed_river(row: int, side: Side) -> bool:
    """棋子是否已过河"""
    return row <= 4 if side is Side.RED else row >= 5


# ── 各棋子伪合法走子生成 ──────────────────────────────────

def _king_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if _in_palace(nr, nc, side):
            t = grid[nr][nc]
            if t is None or t.side is not side:
                moves.append(Move(src, Position(nr, nc)))
    return moves


def _advisor_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        nr, nc = r + dr, c + dc
        if _in_palace(nr, nc, side):
            t = grid[nr][nc]
            if t is None or t.side is not side:
                moves.append(Move(src, Position(nr, nc)))
    return moves


def _elephant_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
        nr, nc = r + dr, c + dc
        if not (0 <= nr <= 9 and 0 <= nc <= 8):
            continue
        if _crossed_river(nr, side):  # 象不能过河
            continue
        er, ec = r + dr // 2, c + dc // 2  # 象眼
        if grid[er][ec] is not None:
            continue
        t = grid[nr][nc]
        if t is None or t.side is not side:
            moves.append(Move(src, Position(nr, nc)))
    return moves


def _horse_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for (lr, lc), targets in (
        ((-1, 0), ((-2, -1), (-2, 1))),
        ((1, 0), ((2, -1), (2, 1))),
        ((0, -1), ((-1, -2), (1, -2))),
        ((0, 1), ((-1, 2), (1, 2))),
    ):
        br, bc = r + lr, c + lc  # 马腿
        if not (0 <= br <= 9 and 0 <= bc <= 8) or grid[br][bc] is not None:
            continue
        for dr, dc in targets:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 9 and 0 <= nc <= 8:
                t = grid[nr][nc]
                if t is None or t.side is not side:
                    moves.append(Move(src, Position(nr, nc)))
    return moves


def _rook_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        while 0 <= nr <= 9 and 0 <= nc <= 8:
            t = grid[nr][nc]
            if t is None:
                moves.append(Move(src, Position(nr, nc)))
            else:
                if t.side is not side:
                    moves.append(Move(src, Position(nr, nc)))
                break
            nr += dr
            nc += dc
    return moves


def _cannon_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        # 无吃子移动（同车）
        while 0 <= nr <= 9 and 0 <= nc <= 8:
            if grid[nr][nc] is not None:
                # 找到炮架，继续搜索吃子目标
                nr += dr
                nc += dc
                while 0 <= nr <= 9 and 0 <= nc <= 8:
                    t = grid[nr][nc]
                    if t is not None:
                        if t.side is not side:
                            moves.append(Move(src, Position(nr, nc)))
                        break
                    nr += dr
                    nc += dc
                break
            moves.append(Move(src, Position(nr, nc)))
            nr += dr
            nc += dc
    return moves


def _pawn_moves(grid: list[list], r: int, c: int, side: Side) -> list[Move]:
    src = Position(r, c)
    moves: list[Move] = []
    forward = -1 if side is Side.RED else 1
    # 前进
    nr = r + forward
    if 0 <= nr <= 9:
        t = grid[nr][c]
        if t is None or t.side is not side:
            moves.append(Move(src, Position(nr, c)))
    # 过河后可横移
    if _crossed_river(r, side):
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc <= 8:
                t = grid[r][nc]
                if t is None or t.side is not side:
                    moves.append(Move(src, Position(r, nc)))
    return moves


_GENERATORS = {
    PieceType.KING: _king_moves,
    PieceType.ADVISOR: _advisor_moves,
    PieceType.ELEPHANT: _elephant_moves,
    PieceType.HORSE: _horse_moves,
    PieceType.ROOK: _rook_moves,
    PieceType.CANNON: _cannon_moves,
    PieceType.PAWN: _pawn_moves,
}


# ── 攻击检测 ─────────────────────────────────────────────

# 反向马跳偏移：(马位置偏移, 马腿偏移) 均相对于被攻击目标
_HORSE_ATTACK_OFFSETS: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = (
    ((-2, -1), (-1, 0)), ((-2, 1), (-1, 0)),
    ((2, -1), (1, 0)),   ((2, 1), (1, 0)),
    ((-1, -2), (0, -1)), ((-1, 2), (0, 1)),
    ((1, -2), (0, -1)),  ((1, 2), (0, 1)),
)


def _is_attacked_by(grid: list[list], r: int, c: int, by: Side) -> bool:
    """检查 (r, c) 是否被 by 方任一棋子攻击（不含将帅对面）"""

    # 直线攻击：车 & 炮
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        platform = False
        while 0 <= nr <= 9 and 0 <= nc <= 8:
            p = grid[nr][nc]
            if p is not None:
                if p.side is by:
                    if not platform and p.piece_type is PieceType.ROOK:
                        return True
                    if platform and p.piece_type is PieceType.CANNON:
                        return True
                if not platform:
                    platform = True
                else:
                    break
            nr += dr
            nc += dc

    # 马攻击（反向跳）
    for (hdr, hdc), (bdr, bdc) in _HORSE_ATTACK_OFFSETS:
        hr, hc = r + hdr, c + hdc
        if 0 <= hr <= 9 and 0 <= hc <= 8:
            p = grid[hr][hc]
            if p is not None and p.side is by and p.piece_type is PieceType.HORSE:
                if grid[r + bdr][c + bdc] is None:
                    return True

    # 兵攻击
    if by is Side.RED:
        # 红兵向上攻击：兵在目标下方一格
        sources = [(r + 1, c)]
        if r <= 4:  # 目标在黑方区域，红兵可横攻
            sources += [(r, c - 1), (r, c + 1)]
    else:
        sources = [(r - 1, c)]
        if r >= 5:
            sources += [(r, c - 1), (r, c + 1)]
    for pr, pc in sources:
        if 0 <= pr <= 9 and 0 <= pc <= 8:
            p = grid[pr][pc]
            if p is not None and p.side is by and p.piece_type is PieceType.PAWN:
                return True

    return False


def is_in_check(board: Board, side: Side) -> bool:
    """判断 side 方是否被将军（含将帅对面检测）"""
    king_pos = board.find_king(side)
    if king_pos is None:
        return True

    grid = board._grid
    if _is_attacked_by(grid, king_pos.row, king_pos.col, side.opposite):
        return True

    # 将帅对面
    opp_king = board.find_king(side.opposite)
    if opp_king is not None and opp_king.col == king_pos.col:
        lo, hi = min(king_pos.row, opp_king.row), max(king_pos.row, opp_king.row)
        if not any(grid[row][king_pos.col] is not None for row in range(lo + 1, hi)):
            return True

    return False


# ── 合法走子生成 ──────────────────────────────────────────

def generate_pseudo_legal_moves(board: Board, side: Side) -> list[Move]:
    """生成所有伪合法走子（可能送将）"""
    grid = board._grid
    moves: list[Move] = []
    for r in range(10):
        row = grid[r]
        for c in range(9):
            p = row[c]
            if p is not None and p.side is side:
                moves.extend(_GENERATORS[p.piece_type](grid, r, c, side))
    return moves


def generate_legal_moves(board: Board, side: Side) -> list[Move]:
    """生成所有合法走子（过滤送将和将帅对面）"""
    legal: list[Move] = []
    for move in generate_pseudo_legal_moves(board, side):
        captured = board.make_move(move)
        if not is_in_check(board, side):
            legal.append(move)
        board.undo_move(move, captured)
    return legal
