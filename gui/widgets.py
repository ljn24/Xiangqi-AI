"""可复用 UI 小组件。"""

from __future__ import annotations

import pygame

from .constants import C_BTN, C_BTN_HOVER, C_BTN_TEXT, C_LINE


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
