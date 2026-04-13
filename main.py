"""象棋 AI 入口

用法:
    python main.py                     # 启动 GUI（默认）
    python main.py --config cli.yaml   # 按配置文件运行 CLI 对弈
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from agents.evaluation import get_evaluator


def _load_config(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        print(f"配置文件不存在: {p}", file=sys.stderr)
        sys.exit(1)
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg or {}


def _build_agent(side_cfg: dict):
    """根据单方配置构建 Agent 实例"""
    agent_type = side_cfg.get("agent", "random")
    if agent_type == "random":
        from agents.random_agent import RandomAgent
        agent = RandomAgent()
    elif agent_type == "minimax":
        from agents.minimax_agent import MinimaxAgent
        depth = side_cfg.get("depth", 4)
        eval_name = side_cfg.get("evaluation", "material_position")
        eval_fn = get_evaluator(eval_name)
        agent = MinimaxAgent(max_depth=depth, eval_fn=eval_fn)
    elif agent_type == "mcts":
        from agents.mcts_agent import MCTSAgent
        agent = MCTSAgent()
    else:
        raise ValueError(f"未知 agent 类型: '{agent_type}'，可选: random, minimax, mcts")

    book_path = side_cfg.get("opening_book")
    if book_path:
        from agents.book_agent import BookAgent, OpeningBook
        book = OpeningBook.load(book_path)
        print(f"  已加载开局库: {book_path}（{len(book)} 个局面）")
        agent = BookAgent(agent, book)

    return agent


def main() -> None:
    parser = argparse.ArgumentParser(description="中国象棋 AI")
    parser.add_argument(
        "--config", type=str, default=None,
        help="CLI 模式配置文件路径（不指定则启动 GUI）",
    )
    args = parser.parse_args()

    if args.config is None:
        _run_gui()
    else:
        _run_cli(_load_config(args.config))


def _run_gui() -> None:
    from gui.app import XiangqiApp
    XiangqiApp().run()


def _run_cli(cfg: dict) -> None:
    """CLI 模式：两个 Agent 自动对弈"""
    from xiangqi.state import GameState
    from xiangqi.types import Side

    max_moves = cfg.get("max_moves", 300)

    red_agent = _build_agent(cfg.get("red", {}))
    black_agent = _build_agent(cfg.get("black", {}))
    agents = {Side.RED: red_agent, Side.BLACK: black_agent}

    state = GameState.initial()
    move_count = 0

    print(repr(state.board))
    print()

    while not state.is_over() and move_count < max_moves:
        agent = agents[state.current_side]
        move = agent.select_move(state)
        print(f"第 {move_count + 1} 步  {state.current_side}  {move}")
        state = state.apply_move(move)
        move_count += 1

    print()
    print(repr(state.board))
    winner = state.winner()
    if winner:
        print(f"\n{winner} 获胜！共 {move_count} 步")
    elif state.is_over():
        print(f"\n和棋！共 {move_count} 步")
    else:
        print(f"\n达到 {max_moves} 步上限，未分出胜负")


if __name__ == "__main__":
    main()
