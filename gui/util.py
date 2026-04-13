"""字体、缩放与棋盘坐标等通用工具。"""

from __future__ import annotations

import os

import pygame

from xiangqi.types import Position

from .constants import (
    ARROW_H,
    ARROW_W,
    CLICK_TOL,
    COL_X,
    C_SETUP_ARROW,
    C_SETUP_ARROW_GLYPH,
    C_SETUP_ARROW_HOVER,
    C_SETUP_HEADER,
    C_SETUP_LABEL,
    C_SETUP_VALUE,
    ROW_Y,
    SELECTOR_CX,
    SETUP_HEADER_H,
    SPLASH_BTN_NORM,
    WINDOW_W,
)


def find_font(size: int) -> pygame.font.Font:
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


def scaled_contain(
    img: pygame.Surface, target_w: int, target_h: int
) -> tuple[pygame.Surface, pygame.Rect]:
    iw, ih = img.get_size()
    scale = min(target_w / iw, target_h / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    x = (target_w - nw) // 2
    y = (target_h - nh) // 2
    return scaled, pygame.Rect(x, y, nw, nh)


def grid_to_pixel(row: int, col: int) -> tuple[int, int]:
    return COL_X[col], ROW_Y[row]


def pixel_to_grid(x: int, y: int) -> Position | None:
    best_col = min(range(9), key=lambda c: abs(x - COL_X[c]))
    best_row = min(range(10), key=lambda r: abs(y - ROW_Y[r]))
    if abs(x - COL_X[best_col]) < CLICK_TOL and abs(y - ROW_Y[best_row]) < CLICK_TOL:
        return Position(best_row, best_col)
    return None


def arrow_rects_at(y: int) -> tuple[pygame.Rect, pygame.Rect]:
    left = pygame.Rect(SELECTOR_CX - 160, y - ARROW_H // 2, ARROW_W, ARROW_H)
    right = pygame.Rect(SELECTOR_CX + 116, y - ARROW_H // 2, ARROW_W, ARROW_H)
    return left, right


def splash_button_window_rect(
    raw: pygame.Surface, splash_dest: pygame.Rect
) -> pygame.Rect:
    iw, ih = raw.get_size()
    nx, ny, nw, nh = SPLASH_BTN_NORM
    ix, iy = nx * iw, ny * ih
    bw, bh = nw * iw, nh * ih
    k = splash_dest.w / iw
    return pygame.Rect(
        int(splash_dest.x + ix * k),
        int(splash_dest.y + iy * k),
        max(1, int(bw * k)),
        max(1, int(bh * k)),
    )


def draw_setup_row(
    surface: pygame.Surface,
    font: pygame.font.Font,
    row: dict,
    mouse: tuple[int, int],
) -> None:
    y = row["y"]
    if row["type"] == "header":
        hdr = font.render(row["label"], True, C_SETUP_HEADER)
        surface.blit(
            hdr,
            hdr.get_rect(center=(WINDOW_W // 2, y + SETUP_HEADER_H // 2 - 5)),
        )
        return

    label_surf = font.render(row["label"], True, C_SETUP_LABEL)
    surface.blit(label_surf, label_surf.get_rect(midright=(SELECTOR_CX - 170, y)))

    val_surf = font.render(row["value"], True, C_SETUP_VALUE)
    surface.blit(val_surf, val_surf.get_rect(center=(SELECTOR_CX, y)))

    left_r, right_r = arrow_rects_at(y)
    for rect, direction in ((left_r, "left"), (right_r, "right")):
        hovered = rect.collidepoint(mouse)
        bg = C_SETUP_ARROW_HOVER if hovered else C_SETUP_ARROW
        pygame.draw.rect(surface, bg, rect, border_radius=6)
        pygame.draw.rect(surface, C_SETUP_VALUE, rect, width=1, border_radius=6)
        tri_cx, tri_cy = rect.center
        th, tw = 12, 10
        if direction == "left":
            pts = [
                (tri_cx - tw, tri_cy),
                (tri_cx + tw, tri_cy - th),
                (tri_cx + tw, tri_cy + th),
            ]
        else:
            pts = [
                (tri_cx + tw, tri_cy),
                (tri_cx - tw, tri_cy - th),
                (tri_cx - tw, tri_cy + th),
            ]
        pygame.draw.polygon(surface, C_SETUP_ARROW_GLYPH, pts)
