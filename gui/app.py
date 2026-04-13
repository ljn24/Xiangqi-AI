"""象棋 GUI：基于 pygame 的图形界面"""

from __future__ import annotations

import enum
import os
import threading
from pathlib import Path

import pygame

from agents.base import Agent
from agents.book_agent import BookAgent, OpeningBook
from agents.evaluation import EvalFunction, get_evaluator, list_evaluators
from agents.mcts_agent import MCTSAgent
from agents.minimax_agent import MinimaxAgent
from agents.random_agent import RandomAgent
from xiangqi.state import GameState
from xiangqi.types import Move, PieceType, Position, Side

# ── 布局常量（基于 board.png 实测） ──────────────────────────

BOARD_W = 932
BOARD_H = 1024
STATUS_H = 54
WINDOW_W = BOARD_W
WINDOW_H = BOARD_H + STATUS_H

COL_X = (93, 190, 282, 374, 465, 557, 649, 740, 838)
ROW_Y = (93, 190, 282, 374, 465, 557, 649, 740, 832, 930)

PIECE_SIZE = 100
PIECE_R = PIECE_SIZE // 2
CLICK_TOL = 52
LEGAL_DOT_R = 8

PIECE_OFFSET_X = 3.5
PIECE_OFFSET_Y = 3.5

ASSETS_DIR = Path(__file__).parent / "assets"

# ── 配色 ─────────────────────────────────────────────────

C_BG = (44, 36, 30)
C_LINE = (50, 30, 10)
C_SELECT = (255, 200, 50)
C_LEGAL = (80, 180, 80)
C_LAST = (100, 149, 237)
C_STATUS_BG = (56, 46, 38)
C_STATUS_TEXT = (220, 210, 190)
C_BTN = (160, 110, 60)
C_BTN_HOVER = (200, 150, 90)
C_BTN_TEXT = (255, 245, 230)

# 设置页（浅色背景）：深棕系，与 start/background 图色调一致
C_SETUP_HEADER = (105, 76, 52)
C_SETUP_LABEL = (78, 56, 40)
C_SETUP_VALUE = (42, 30, 22)
C_SETUP_ARROW = (140, 100, 68)
C_SETUP_ARROW_HOVER = (165, 125, 88)

# ── 评估函数 & Agent 类型元数据 ──────────────────────────

EVAL_DISPLAY_NAMES: dict[str, str] = {
    "piece_count": "棋子计数",
    "material": "子力价值",
    "material_position": "子力+位置",
    "material_position_mobility": "子力+位置+机动性",
}

AGENT_TYPES = ("human", "random", "minimax", "mcts")
AGENT_DISPLAY: dict[str, str] = {
    "human": "人类",
    "random": "随机AI",
    "minimax": "极大极小",
    "mcts": "蒙特卡洛",
}

DEPTH_MIN, DEPTH_MAX = 1, 8

# ── 设置行间距 ───────────────────────────────────────────

_HEADER_H = 50
_ROW_H = 58
_SECTION_GAP = 20
_SELECTOR_CX = WINDOW_W // 2 + 60
_ARROW_W, _ARROW_H = 44, 44


class Screen(enum.Enum):
    SPLASH = "splash"
    GAME_SETUP = "game_setup"
    PLAYING = "playing"
    GAME_OVER = "game_over"


# start.png 上「开始游戏」整块按钮（含 START GAME 英文行）；y 按暗色区域扫描对齐，略扩边便于点击
_SPLASH_BTN_NORM = (0.258, 0.752, 0.478, 0.134)

AI_MOVE_EVENT = pygame.USEREVENT + 1


# ── 辅助函数 ──────────────────────────────────────────────

def _grid_to_pixel(row: int, col: int) -> tuple[int, int]:
    return COL_X[col], ROW_Y[row]


def _pixel_to_grid(x: int, y: int) -> Position | None:
    best_col = min(range(9), key=lambda c: abs(x - COL_X[c]))
    best_row = min(range(10), key=lambda r: abs(y - ROW_Y[r]))
    if abs(x - COL_X[best_col]) < CLICK_TOL and abs(y - ROW_Y[best_row]) < CLICK_TOL:
        return Position(best_row, best_col)
    return None


def _find_font(size: int) -> pygame.font.Font:
    candidates = [
        "/mnt/c/Windows/Fonts/msyh.ttc",
        "/mnt/c/Windows/Fonts/simhei.ttf",
        "/mnt/c/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return pygame.font.Font(p, size)
    return pygame.font.SysFont("", size)


def _arrow_rects_at(y: int) -> tuple[pygame.Rect, pygame.Rect]:
    left = pygame.Rect(_SELECTOR_CX - 160, y - _ARROW_H // 2, _ARROW_W, _ARROW_H)
    right = pygame.Rect(_SELECTOR_CX + 116, y - _ARROW_H // 2, _ARROW_W, _ARROW_H)
    return left, right


# ── 按钮组件 ──────────────────────────────────────────────

class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        *,
        fill: tuple[int, int, int] | None = None,
        fill_hover: tuple[int, int, int] | None = None,
        border: tuple[int, int, int] | None = None,
        text_color: tuple[int, int, int] | None = None,
    ) -> None:
        self.rect = rect
        self.text = text
        self.font = font
        self._fill = fill
        self._fill_hover = fill_hover
        self._border = border
        self._text_color = text_color

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        hovered = self.rect.collidepoint(mouse_pos)
        base, hi = self._fill or C_BTN, self._fill_hover or C_BTN_HOVER
        color = hi if hovered else base
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        brd = self._border or C_LINE
        pygame.draw.rect(surface, brd, self.rect, width=2, border_radius=8)
        tc = self._text_color or C_BTN_TEXT
        txt = self.font.render(self.text, True, tc)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


# ══════════════════════════════════════════════════════════
#  主应用
# ══════════════════════════════════════════════════════════

class XiangqiApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("中国象棋 AI")
        self.surface = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()

        self.font = _find_font(24)
        self.font_lg = _find_font(42)
        self.font_sm = _find_font(20)

        self._eval_names = list_evaluators()
        self._default_eval_idx = self._eval_names.index("material_position")

        self.piece_imgs = self._load_piece_images()
        self.board_img = self._load_board_image()
        self._start_raw = self._load_start_image()
        self._bg_setup_raw = self._load_setup_background_image()
        self._start_scaled, self._splash_dest = self._scaled_contain(
            self._start_raw, WINDOW_W, WINDOW_H
        )
        self._bg_setup_scaled, self._bg_setup_dest = self._scaled_contain(
            self._bg_setup_raw, WINDOW_W, WINDOW_H
        )

        self._opening_book = self._load_opening_book()
        self._init_setup_defaults()
        self._reset_to_setup()
        self.screen = Screen.SPLASH

    # ── 资源加载 ──────────────────────────────────────────

    def _load_piece_images(self) -> dict[tuple[Side, PieceType], pygame.Surface]:
        mapping: dict[tuple[Side, PieceType], str] = {
            (s, pt): f"{s.value}_{pt.value}.png" for s in Side for pt in PieceType
        }
        imgs: dict[tuple[Side, PieceType], pygame.Surface] = {}
        for key, filename in mapping.items():
            path = ASSETS_DIR / filename
            if not path.exists():
                raise FileNotFoundError(f"棋子图片缺失: {path}")
            raw = pygame.image.load(str(path)).convert_alpha()
            imgs[key] = pygame.transform.smoothscale(raw, (PIECE_SIZE, PIECE_SIZE))
        return imgs

    def _load_board_image(self) -> pygame.Surface:
        path = ASSETS_DIR / "board.png"
        if not path.exists():
            raise FileNotFoundError(f"棋盘图片缺失: {path}")
        return pygame.image.load(str(path)).convert()

    def _load_start_image(self) -> pygame.Surface:
        path = ASSETS_DIR / "start.png"
        if not path.exists():
            raise FileNotFoundError(f"启动图缺失: {path}")
        return pygame.image.load(str(path)).convert_alpha()

    def _load_setup_background_image(self) -> pygame.Surface:
        path = ASSETS_DIR / "background.png"
        if not path.exists():
            raise FileNotFoundError(f"设置页背景缺失: {path}")
        return pygame.image.load(str(path)).convert_alpha()

    @staticmethod
    def _scaled_contain(
        img: pygame.Surface, target_w: int, target_h: int
    ) -> tuple[pygame.Surface, pygame.Rect]:
        """等比缩放至完全落入 target 矩形，居中；返回 (缩放图, 在 target 中的摆放矩形)。"""
        iw, ih = img.get_size()
        scale = min(target_w / iw, target_h / ih)
        nw = max(1, int(round(iw * scale)))
        nh = max(1, int(round(ih * scale)))
        scaled = pygame.transform.smoothscale(img, (nw, nh))
        x = (target_w - nw) // 2
        y = (target_h - nh) // 2
        return scaled, pygame.Rect(x, y, nw, nh)

    @staticmethod
    def _load_opening_book() -> OpeningBook | None:
        book_path = Path(__file__).resolve().parent.parent / "data" / "opening_book.json"
        if not book_path.exists():
            return None
        try:
            return OpeningBook.load(book_path)
        except Exception:
            return None

    # ── 状态管理 ──────────────────────────────────────────

    def _init_setup_defaults(self) -> None:
        """初始化对局设置（只在首次启动时调用）"""
        self._cfg_agent: dict[Side, int] = {
            Side.RED: 0,   # human
            Side.BLACK: 2, # minimax
        }
        self._cfg_depth: dict[Side, int] = {
            Side.RED: 4, Side.BLACK: 4,
        }
        self._cfg_eval: dict[Side, int] = {
            Side.RED: self._default_eval_idx,
            Side.BLACK: self._default_eval_idx,
        }
        self._cfg_use_book: bool = self._opening_book is not None

    def _reset_to_setup(self) -> None:
        self.state: GameState | None = None
        self.human_side: Side | None = None
        self.agents: dict[Side, Agent | None] = {
            Side.RED: None, Side.BLACK: None,
        }
        self.selected: Position | None = None
        self.legal_targets: list[Position] = []
        self.last_move: Move | None = None
        self.ai_thinking = False

    def _build_agent_for(self, side: Side) -> Agent | None:
        agent_key = AGENT_TYPES[self._cfg_agent[side]]
        if agent_key == "human":
            return None
        if agent_key == "random":
            agent: Agent = RandomAgent()
        elif agent_key == "mcts":
            agent = MCTSAgent()
        else:
            eval_fn = get_evaluator(self._eval_names[self._cfg_eval[side]])
            agent = MinimaxAgent(max_depth=self._cfg_depth[side], eval_fn=eval_fn)
        if self._cfg_use_book and self._opening_book is not None:
            agent = BookAgent(agent, self._opening_book)
        return agent

    def _start_game_from_setup(self) -> None:
        self.state = GameState.initial()
        self.last_move = None
        self.selected = None
        self.legal_targets = []
        self.ai_thinking = False

        self.agents[Side.RED] = self._build_agent_for(Side.RED)
        self.agents[Side.BLACK] = self._build_agent_for(Side.BLACK)

        red_is_human = AGENT_TYPES[self._cfg_agent[Side.RED]] == "human"
        black_is_human = AGENT_TYPES[self._cfg_agent[Side.BLACK]] == "human"
        if red_is_human and not black_is_human:
            self.human_side = Side.RED
        elif black_is_human and not red_is_human:
            self.human_side = Side.BLACK
        else:
            self.human_side = None

        self.screen = Screen.PLAYING

    # ── AI 线程 ───────────────────────────────────────────

    def _start_ai(self) -> None:
        if self.state is None or self.ai_thinking:
            return
        agent = self.agents.get(self.state.current_side)
        if agent is None:
            return

        self.ai_thinking = True
        board_copy = self.state.board.copy()
        ai_state = GameState(
            board_copy,
            self.state.current_side,
            list(self.state.move_history),
            list(self.state.position_history),
        )

        def think() -> None:
            move = agent.select_move(ai_state)
            evt = pygame.event.Event(AI_MOVE_EVENT, {"move": move})
            pygame.event.post(evt)

        threading.Thread(target=think, daemon=True).start()

    # ── 设置界面布局 ──────────────────────────────────────

    def _setup_layout(self) -> tuple[list[dict], int]:
        """构建设置行列表和按钮 y 坐标。每行带 type/key/label/value/y。"""
        rows: list[dict] = []
        y = 200

        for side in (Side.RED, Side.BLACK):
            side_label = "红方" if side is Side.RED else "黑方"
            rows.append({"type": "header", "label": f"── {side_label} ──", "y": y})
            y += _HEADER_H

            agent_key = AGENT_TYPES[self._cfg_agent[side]]
            rows.append({
                "type": "selector", "key": f"{side.value}_agent",
                "label": "类型",
                "value": AGENT_DISPLAY[agent_key],
                "y": y,
            })
            y += _ROW_H

            if agent_key == "minimax":
                rows.append({
                    "type": "selector", "key": f"{side.value}_depth",
                    "label": "搜索深度",
                    "value": str(self._cfg_depth[side]),
                    "y": y,
                })
                y += _ROW_H

                eval_k = self._eval_names[self._cfg_eval[side]]
                rows.append({
                    "type": "selector", "key": f"{side.value}_eval",
                    "label": "评估函数",
                    "value": EVAL_DISPLAY_NAMES.get(eval_k, eval_k),
                    "y": y,
                })
                y += _ROW_H

            y += _SECTION_GAP

        if self._opening_book is not None:
            rows.append({"type": "header", "label": "── 通用 ──", "y": y})
            y += _HEADER_H
            rows.append({
                "type": "selector", "key": "use_book",
                "label": "开局库",
                "value": "开启" if self._cfg_use_book else "关闭",
                "y": y,
            })
            y += _ROW_H
            y += _SECTION_GAP

        return rows, y + 10

    def _apply_selector_change(self, key: str, delta: int) -> None:
        if key == "use_book":
            self._cfg_use_book = not self._cfg_use_book
            return
        side_str, field = key.split("_", 1)
        side = Side.RED if side_str == "red" else Side.BLACK

        if field == "agent":
            n = len(AGENT_TYPES)
            self._cfg_agent[side] = (self._cfg_agent[side] + delta) % n
        elif field == "depth":
            self._cfg_depth[side] = max(DEPTH_MIN, min(DEPTH_MAX, self._cfg_depth[side] + delta))
        elif field == "eval":
            n = len(self._eval_names)
            self._cfg_eval[side] = (self._cfg_eval[side] + delta) % n

    # ── 事件处理 ──────────────────────────────────────────

    def _splash_button_window_rect(self) -> pygame.Rect:
        """将 start.png 上的按钮归一化区域映射到窗口坐标。"""
        iw, ih = self._start_raw.get_size()
        nx, ny, nw, nh = _SPLASH_BTN_NORM
        ix, iy = nx * iw, ny * ih
        bw, bh = nw * iw, nh * ih
        dest = self._splash_dest
        k = dest.w / iw
        return pygame.Rect(
            int(dest.x + ix * k),
            int(dest.y + iy * k),
            max(1, int(bw * k)),
            max(1, int(bh * k)),
        )

    def _splash_start_clicked(self, pos: tuple[int, int]) -> bool:
        return self._splash_button_window_rect().collidepoint(pos)

    def _handle_click_splash(self, pos: tuple[int, int]) -> None:
        if self._splash_start_clicked(pos):
            self.screen = Screen.GAME_SETUP

    def _handle_click_game_setup(self, pos: tuple[int, int]) -> None:
        rows, btn_y = self._setup_layout()

        for row in rows:
            if row["type"] != "selector":
                continue
            left_r, right_r = _arrow_rects_at(row["y"])
            if left_r.collidepoint(pos):
                self._apply_selector_change(row["key"], -1)
                return
            if right_r.collidepoint(pos):
                self._apply_selector_change(row["key"], 1)
                return

        btn_w, btn_h = 260, 52
        start_rect = pygame.Rect(WINDOW_W // 2 - btn_w // 2, btn_y, btn_w, btn_h)
        if start_rect.collidepoint(pos):
            self._start_game_from_setup()

    def _handle_click_playing(self, pos: tuple[int, int]) -> None:
        if self.state is None or self.state.is_over() or self.ai_thinking:
            return
        if self.agents.get(self.state.current_side) is not None:
            return

        grid_pos = _pixel_to_grid(*pos)
        if grid_pos is None:
            return

        if self.selected and grid_pos in self.legal_targets:
            move = Move(self.selected, grid_pos)
            self.state = self.state.apply_move(move)
            self.last_move = move
            self.selected = None
            self.legal_targets = []
            return

        piece = self.state.board.piece_at(grid_pos)
        if piece is not None and piece.side is self.state.current_side:
            self.selected = grid_pos
            legal = self.state.legal_moves()
            self.legal_targets = [m.dst for m in legal if m.src == grid_pos]
        else:
            self.selected = None
            self.legal_targets = []

    def _handle_click_game_over(self, pos: tuple[int, int]) -> None:
        cx = WINDOW_W // 2
        btn = pygame.Rect(cx - 120, WINDOW_H // 2 + 50, 240, 52)
        if btn.collidepoint(pos):
            self._reset_to_setup()
            self.screen = Screen.GAME_SETUP

    def _handle_ai_move(self, move: Move) -> None:
        if self.state is None:
            return
        self.state = self.state.apply_move(move)
        self.last_move = move
        self.ai_thinking = False

    # ── 绘制 ─────────────────────────────────────────────

    def _draw_board(self) -> None:
        self.surface.blit(self.board_img, (0, 0))

    def _draw_highlights(self) -> None:
        if self.last_move:
            for pos in (self.last_move.src, self.last_move.dst):
                px, py = _grid_to_pixel(pos.row, pos.col)
                pygame.draw.circle(self.surface, C_LAST, (px, py), PIECE_R + 5, 3)
        if self.selected:
            px, py = _grid_to_pixel(self.selected.row, self.selected.col)
            pygame.draw.circle(self.surface, C_SELECT, (px, py), PIECE_R + 5, 3)
        d = LEGAL_DOT_R * 2
        for pos in self.legal_targets:
            px, py = _grid_to_pixel(pos.row, pos.col)
            s = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_LEGAL, 170), (LEGAL_DOT_R, LEGAL_DOT_R), LEGAL_DOT_R)
            self.surface.blit(s, (px - LEGAL_DOT_R, py - LEGAL_DOT_R))

    def _draw_piece(self, row: int, col: int, side: Side, pt: PieceType) -> None:
        px, py = _grid_to_pixel(row, col)
        px += PIECE_OFFSET_X
        py += PIECE_OFFSET_Y
        img = self.piece_imgs[(side, pt)]
        iw, ih = img.get_size()
        self.surface.blit(img, (px - iw // 2, py - ih // 2))

    def _draw_pieces(self) -> None:
        if self.state is None:
            return
        for r in range(10):
            row = self.state.board._grid[r]
            for c in range(9):
                p = row[c]
                if p is not None:
                    self._draw_piece(r, c, p.side, p.piece_type)

    def _draw_status(self) -> None:
        bar = pygame.Rect(0, BOARD_H, WINDOW_W, STATUS_H)
        pygame.draw.rect(self.surface, C_STATUS_BG, bar)
        if self.state is None:
            return
        if self.state.is_over():
            w = self.state.winner()
            text = f"{w} 获胜！" if w else "和棋"
        elif self.ai_thinking:
            text = f"{self.state.current_side} AI 思考中..."
        else:
            check = " 将军！" if self.state.is_in_check() else ""
            text = f"轮到 {self.state.current_side}{check}"
        txt_surf = self.font.render(text, True, C_STATUS_TEXT)
        self.surface.blit(txt_surf, txt_surf.get_rect(center=bar.center))

    def _draw_splash(self) -> None:
        self.surface.fill(C_BG)
        self.surface.blit(self._start_scaled, self._splash_dest.topleft)
        mouse = pygame.mouse.get_pos()
        btn_r = self._splash_button_window_rect()
        if btn_r.collidepoint(mouse):
            hi = pygame.Surface(btn_r.size, pygame.SRCALPHA)
            hi.fill((255, 255, 255, 28))
            self.surface.blit(hi, btn_r.topleft)

    def _draw_game_setup(self) -> None:
        self.surface.fill(C_BG)
        self.surface.blit(self._bg_setup_scaled, self._bg_setup_dest.topleft)

        title = self.font_lg.render("对局设置", True, C_SETUP_VALUE)
        self.surface.blit(title, title.get_rect(center=(WINDOW_W // 2, 120)))

        mouse = pygame.mouse.get_pos()
        rows, btn_y = self._setup_layout()

        for row in rows:
            y = row["y"]

            if row["type"] == "header":
                hdr = self.font.render(row["label"], True, C_SETUP_HEADER)
                self.surface.blit(hdr, hdr.get_rect(center=(WINDOW_W // 2, y + _HEADER_H // 2 - 5)))
                continue

            # 标签
            label_surf = self.font.render(row["label"], True, C_SETUP_LABEL)
            self.surface.blit(label_surf, label_surf.get_rect(midright=(_SELECTOR_CX - 170, y)))

            # 当前值
            val_surf = self.font.render(row["value"], True, C_SETUP_VALUE)
            self.surface.blit(val_surf, val_surf.get_rect(center=(_SELECTOR_CX, y)))

            # 左右箭头
            left_r, right_r = _arrow_rects_at(y)
            for rect, direction in ((left_r, "left"), (right_r, "right")):
                hovered = rect.collidepoint(mouse)
                bg = C_SETUP_ARROW_HOVER if hovered else C_SETUP_ARROW
                pygame.draw.rect(self.surface, bg, rect, border_radius=6)
                pygame.draw.rect(self.surface, C_SETUP_VALUE, rect, width=1, border_radius=6)
                tri_cx, tri_cy = rect.center
                th, tw = 12, 10
                if direction == "left":
                    pts = [(tri_cx - tw, tri_cy), (tri_cx + tw, tri_cy - th), (tri_cx + tw, tri_cy + th)]
                else:
                    pts = [(tri_cx + tw, tri_cy), (tri_cx - tw, tri_cy - th), (tri_cx - tw, tri_cy + th)]
                pygame.draw.polygon(self.surface, C_BTN_TEXT, pts)

        btn_w, btn_h = 260, 52
        setup_start_btn = Button(
            pygame.Rect(WINDOW_W // 2 - btn_w // 2, btn_y, btn_w, btn_h),
            "开始对弈",
            self.font,
            fill=C_SETUP_VALUE,
            fill_hover=(62, 44, 30),
            border=C_SETUP_HEADER,
            text_color=C_BTN_TEXT,
        )
        setup_start_btn.draw(self.surface, mouse)

    def _draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.surface.blit(overlay, (0, 0))

        w = self.state.winner() if self.state else None
        text = f"{w} 获胜！" if w else "和棋"
        txt = self.font_lg.render(text, True, (255, 220, 100))
        self.surface.blit(txt, txt.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 - 30)))

        mouse = pygame.mouse.get_pos()
        Button(
            pygame.Rect(WINDOW_W // 2 - 120, WINDOW_H // 2 + 50, 240, 52),
            "再来一局", self.font,
        ).draw(self.surface, mouse)

    # ── 主循环 ────────────────────────────────────────────

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == AI_MOVE_EVENT:
                    self._handle_ai_move(event.move)
                    if self.state and self.state.is_over():
                        self.screen = Screen.GAME_OVER

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.screen == Screen.SPLASH:
                        self._handle_click_splash(event.pos)
                    elif self.screen == Screen.GAME_SETUP:
                        self._handle_click_game_setup(event.pos)
                    elif self.screen == Screen.PLAYING:
                        self._handle_click_playing(event.pos)
                        if self.state and self.state.is_over():
                            self.screen = Screen.GAME_OVER
                    elif self.screen == Screen.GAME_OVER:
                        self._handle_click_game_over(event.pos)

            if (
                self.screen == Screen.PLAYING
                and self.state is not None
                and not self.state.is_over()
                and not self.ai_thinking
                and self.agents.get(self.state.current_side) is not None
            ):
                self._start_ai()

            self.surface.fill(C_BG)
            if self.screen == Screen.SPLASH:
                self._draw_splash()
            elif self.screen == Screen.GAME_SETUP:
                self._draw_game_setup()
            elif self.screen in (Screen.PLAYING, Screen.GAME_OVER):
                self._draw_board()
                self._draw_pieces()
                self._draw_highlights()
                self._draw_status()
                if self.screen == Screen.GAME_OVER:
                    self._draw_game_over_overlay()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
