"""AI Agent 注册表"""

from .book_agent import BookAgent, OpeningBook
from .mcts_agent import MCTSAgent
from .minimax_agent import MinimaxAgent
from .random_agent import RandomAgent

__all__ = ["RandomAgent", "MinimaxAgent", "MCTSAgent", "BookAgent", "OpeningBook"]
