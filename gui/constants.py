"""GUI 布局、配色与对局设置相关常量。"""

from __future__ import annotations

import enum
from pathlib import Path

import pygame

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
C_ARROW = (180, 140, 80)
C_ARROW_HOVER = (220, 180, 110)
C_VALUE_TEXT = (255, 220, 120)
C_HEADER_TEXT = (180, 160, 130)

C_SETUP_TITLE = (48, 34, 24)
C_SETUP_HEADER = (105, 76, 52)
C_SETUP_LABEL = (78, 56, 40)
C_SETUP_VALUE = (42, 30, 22)
C_SETUP_ARROW = (140, 100, 68)
C_SETUP_ARROW_HOVER = (165, 125, 88)
C_SETUP_ARROW_GLYPH = (252, 246, 236)

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

SETUP_HEADER_H = 50
SETUP_ROW_H = 58
SETUP_SECTION_GAP = 20
SELECTOR_CX = WINDOW_W // 2 + 60
ARROW_W, ARROW_H = 44, 44

SPLASH_BTN_NORM = (0.258, 0.752, 0.478, 0.134)


class Screen(enum.Enum):
    SPLASH = "splash"
    GAME_SETUP = "game_setup"
    PLAYING = "playing"
    GAME_OVER = "game_over"


AI_MOVE_EVENT = pygame.USEREVENT + 1
