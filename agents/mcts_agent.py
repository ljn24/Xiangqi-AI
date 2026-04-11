"""Monte Carlo Tree Search (UCT) AI

经典 UCT-MCTS 实现：纯随机 rollout、固定迭代次数、UCB1 选择。
参考: Kocsis & Szepesvári, "Bandit based Monte-Carlo Planning", 2006.
"""

from __future__ import annotations

import math
import random

from xiangqi.board import Board
from xiangqi.rules import generate_pseudo_legal_moves
from xiangqi.state import GameState
from xiangqi.types import Move, Side

from .base import Agent

_ITERATIONS = 800
_EXPLORATION = math.sqrt(2)
_MAX_ROLLOUT_DEPTH = 50


class _MCTSNode:
    """MCTS 搜索树节点"""

    __slots__ = (
        "state", "parent", "move", "children",
        "untried_moves", "visits", "wins",
    )

    def __init__(
        self,
        state: GameState,
        parent: _MCTSNode | None = None,
        move: Move | None = None,
    ) -> None:
        self.state = state
        self.parent = parent
        self.move = move
        self.children: list[_MCTSNode] = []
        self.untried_moves: list[Move] = state.legal_moves()
        self.visits = 0
        self.wins = 0.0

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    @property
    def is_terminal(self) -> bool:
        return self.state.is_over()

    def ucb1(self, c: float) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.wins / self.visits
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)  # type: ignore[union-attr]
        return exploitation + exploration

    def best_child(self, c: float) -> _MCTSNode:
        return max(self.children, key=lambda child: child.ucb1(c))

    def expand(self) -> _MCTSNode:
        """随机选一个未尝试走法，创建并返回新子节点"""
        idx = random.randrange(len(self.untried_moves))
        move = self.untried_moves.pop(idx)
        child_state = self.state.apply_move(move)
        child = _MCTSNode(child_state, parent=self, move=move)
        self.children.append(child)
        return child


def _rollout_reward(board: Board, side: Side, root_side: Side) -> float:
    """纯随机 rollout（in-place），返回 root_side 视角的 reward ∈ {0, 0.5, 1}

    直接在 board 上 make_move，避免每步拷贝，大幅提升性能。
    使用 pseudo-legal moves；若王被吃则终局。
    """
    for _ in range(_MAX_ROLLOUT_DEPTH):
        if board.find_king(Side.RED) is None:
            return 1.0 if root_side is Side.BLACK else 0.0
        if board.find_king(Side.BLACK) is None:
            return 1.0 if root_side is Side.RED else 0.0

        moves = generate_pseudo_legal_moves(board, side)
        if not moves:
            return 0.0 if side is root_side else 1.0

        board.make_move(random.choice(moves))
        side = side.opposite

    return 0.5


class MCTSAgent(Agent):
    """经典 UCT-MCTS Agent（固定参数，用于对照实验）

    - 迭代次数: 800
    - 探索常数: √2
    - Rollout 深度上限: 50
    """

    def select_move(self, state: GameState) -> Move:
        root = _MCTSNode(state)
        root_side = state.current_side

        for _ in range(_ITERATIONS):
            node = root

            # ① Selection
            while node.is_fully_expanded and not node.is_terminal:
                node = node.best_child(_EXPLORATION)

            # ② Expansion
            if not node.is_terminal and not node.is_fully_expanded:
                node = node.expand()

            # ③ Simulation — 在独立的 board 副本上做 in-place rollout
            reward = _rollout_reward(
                node.state.board.copy(),
                node.state.current_side,
                root_side,
            )

            # ④ Backpropagation
            while node is not None:
                node.visits += 1
                if node.parent is None:
                    node.wins += reward
                else:
                    parent_side = node.state.current_side.opposite
                    if parent_side is root_side:
                        node.wins += reward
                    else:
                        node.wins += 1.0 - reward
                node = node.parent  # type: ignore[assignment]

        return max(root.children, key=lambda c: c.visits).move  # type: ignore[return-value]
