"""随机走子 AI：在所有合法走法中随机选择"""

from __future__ import annotations

import random

from xiangqi.state import GameState
from xiangqi.types import Move

from .base import Agent


class RandomAgent(Agent):
    def select_move(self, state: GameState) -> Move:
        moves = state.legal_moves()
        return random.choice(moves)
