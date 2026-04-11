"""AI Agent 抽象基类"""

from __future__ import annotations

import abc

from xiangqi.state import GameState
from xiangqi.types import Move


class Agent(abc.ABC):
    @abc.abstractmethod
    def select_move(self, state: GameState) -> Move:
        """根据当前局面选择一步走法"""
        ...
