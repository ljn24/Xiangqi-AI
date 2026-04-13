"""象棋 AI 实验脚本

读取 YAML 配置文件，运行 AI vs AI 对弈，收集指标，输出 JSON 结果。

用法（从项目根目录运行）:
    python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/A1_random_vs_mcts.yaml
    python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/
    python experiments/scripts/run_experiments.py experiments/configs/
    python experiments/scripts/run_experiments.py experiments/configs/ --games 10 --output-dir my_results
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from agents.book_agent import BookAgent, OpeningBook, move_to_iccs
from agents.evaluation import get_evaluator
from agents.mcts_agent import MCTSAgent
from agents.minimax_agent import MinimaxAgent
from agents.random_agent import RandomAgent
from xiangqi.state import GameState
from xiangqi.types import Side


def _build_agent(cfg: dict[str, Any]):
    """根据配置字典构建 Agent 实例"""
    agent_type = cfg.get("agent", "random")
    if agent_type == "random":
        agent = RandomAgent()
    elif agent_type == "minimax":
        depth = cfg.get("depth", 4)
        eval_name = cfg.get("evaluation", "material_position")
        agent = MinimaxAgent(max_depth=depth, eval_fn=get_evaluator(eval_name))
    elif agent_type == "mcts":
        agent = MCTSAgent()
    else:
        raise ValueError(f"未知 agent 类型: '{agent_type}'")

    book_path = cfg.get("opening_book")
    if book_path:
        book = OpeningBook.load(book_path)
        agent = BookAgent(agent, book)

    return agent


def _get_nodes(agent) -> int | None:
    """从 agent 中提取 nodes_searched（仅 MinimaxAgent 支持）"""
    inner = agent.inner if isinstance(agent, BookAgent) else agent
    if isinstance(inner, MinimaxAgent):
        return inner.nodes_searched
    return None


def _cfg_label(cfg: dict[str, Any]) -> str:
    """为配置生成简短标签，用于汇总输出"""
    agent = cfg.get("agent", "random")
    parts = [agent]
    if agent == "minimax":
        parts.append(f"d{cfg.get('depth', 4)}")
        eval_name = cfg.get("evaluation", "material_position")
        if eval_name != "material_position":
            parts.append(eval_name)
    if cfg.get("opening_book"):
        parts.append("book")
    return "_".join(parts)


def play_game(
    red_agent,
    black_agent,
    max_moves: int = 300,
    *,
    player_of_side: dict[str, str] | None = None,
) -> dict[str, Any]:
    """运行一局对弈，返回详细记录

    player_of_side 映射 "red"/"black" -> "player_1"/"player_2"，
    用于标记每步属于哪个逻辑选手（不受颜色交换影响）。
    """
    agents = {Side.RED: red_agent, Side.BLACK: black_agent}
    state = GameState.initial()
    move_stats: list[dict[str, Any]] = []
    move_count = 0

    while not state.is_over() and move_count < max_moves:
        side = state.current_side
        agent = agents[side]

        t0 = time.perf_counter()
        move = agent.select_move(state)
        elapsed = time.perf_counter() - t0

        nodes = _get_nodes(agent)
        entry: dict[str, Any] = {
            "side": side.value,
            "move": move_to_iccs(move),
            "time_s": round(elapsed, 6),
            "nodes": nodes,
        }
        if player_of_side:
            entry["player"] = player_of_side[side.value]
        move_stats.append(entry)

        state = state.apply_move(move)
        move_count += 1

    winner = state.winner()
    winner_str = winner.value if winner else "draw"
    result: dict[str, Any] = {
        "winner": winner_str,
        "total_moves": move_count,
        "move_stats": move_stats,
    }
    if player_of_side and winner_str != "draw":
        result["winner_player"] = player_of_side[winner_str]
    return result


def _summarize(games: list[dict], p1_cfg: dict, p2_cfg: dict) -> dict[str, Any]:
    """按逻辑选手（player_1 / player_2）汇总统计，不受颜色交换影响"""
    total = len(games)
    p1_wins = sum(1 for g in games if g.get("winner_player") == "player_1")
    p2_wins = sum(1 for g in games if g.get("winner_player") == "player_2")
    draws = total - p1_wins - p2_wins
    avg_moves = sum(g["total_moves"] for g in games) / total if total else 0

    p1_times: list[float] = []
    p2_times: list[float] = []
    p1_nodes: list[int] = []
    p2_nodes: list[int] = []

    for g in games:
        for ms in g["move_stats"]:
            player = ms.get("player")
            if player == "player_1":
                p1_times.append(ms["time_s"])
                if ms["nodes"] is not None:
                    p1_nodes.append(ms["nodes"])
            elif player == "player_2":
                p2_times.append(ms["time_s"])
                if ms["nodes"] is not None:
                    p2_nodes.append(ms["nodes"])

    def _avg(lst: list) -> float | None:
        return round(sum(lst) / len(lst), 6) if lst else None

    p1_label = _cfg_label(p1_cfg)
    p2_label = _cfg_label(p2_cfg)

    return {
        "total_games": total,
        "player_1": p1_label,
        "player_2": p2_label,
        "player_1_wins": p1_wins,
        "player_2_wins": p2_wins,
        "draws": draws,
        "avg_moves": round(avg_moves, 1),
        f"player_1_avg_time_per_move": _avg(p1_times),
        f"player_2_avg_time_per_move": _avg(p2_times),
        f"player_1_avg_nodes_per_move": round(_avg(p1_nodes)) if p1_nodes else None,
        f"player_2_avg_nodes_per_move": round(_avg(p2_nodes)) if p2_nodes else None,
    }


def run_matchup(config: dict[str, Any], *, games_override: int | None = None) -> dict[str, Any]:
    """根据配置运行一组 matchup，返回完整结果"""
    n_games = games_override or config.get("games", 20)
    max_moves = config.get("max_moves", 300)
    swap = config.get("swap_colors", True)
    p1_cfg = config["red"]
    p2_cfg = config["black"]

    if swap:
        half = n_games // 2
        schedule: list[tuple[dict, dict, bool]] = (
            [(p1_cfg, p2_cfg, False)] * half
            + [(p2_cfg, p1_cfg, True)] * (n_games - half)
        )
    else:
        schedule = [(p1_cfg, p2_cfg, False)] * n_games

    p1_label = _cfg_label(p1_cfg)
    p2_label = _cfg_label(p2_cfg)

    all_games: list[dict[str, Any]] = []
    for i, (r_cfg, b_cfg, swapped) in enumerate(schedule):
        _log(f"  对局 {i + 1}/{n_games} ...")
        red_agent = _build_agent(r_cfg)
        black_agent = _build_agent(b_cfg)

        if swapped:
            player_of_side = {"red": "player_2", "black": "player_1"}
        else:
            player_of_side = {"red": "player_1", "black": "player_2"}

        record = play_game(
            red_agent, black_agent, max_moves,
            player_of_side=player_of_side,
        )
        record["game_id"] = i + 1
        record["red_config"] = r_cfg
        record["black_config"] = b_cfg
        record["swapped"] = swapped
        all_games.append(record)

        wp = record.get("winner_player", "draw")
        if wp == "player_1":
            winner_desc = p1_label
        elif wp == "player_2":
            winner_desc = p2_label
        else:
            winner_desc = "和棋"
        _log(f"    结果: {winner_desc}{'胜' if wp != 'draw' else ''}，"
             f"共 {record['total_moves']} 步")

    summary = _summarize(all_games, p1_cfg, p2_cfg)
    return {
        "experiment": config.get("experiment", ""),
        "description": config.get("description", ""),
        "player_1_config": p1_cfg,
        "player_2_config": p2_cfg,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "games": all_games,
        "summary": summary,
    }


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _collect_configs(path: Path) -> list[Path]:
    """从给定路径收集所有 YAML 配置文件（按名称排序）"""
    if path.is_file():
        return [path]
    configs: list[Path] = sorted(
        p for p in path.rglob("*") if p.suffix in (".yaml", ".yml")
    )
    if not configs:
        _log(f"在 {path} 下未找到 YAML 配置文件")
        sys.exit(1)
    return configs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="象棋 AI 实验脚本：读取 YAML 配置并运行对弈实验",
    )
    parser.add_argument(
        "path",
        help="YAML 配置文件或包含配置文件的目录",
    )
    parser.add_argument(
        "--games", type=int, default=None,
        help="覆盖配置文件中的对弈局数",
    )
    parser.add_argument(
        "--max-moves", type=int, default=None,
        help="覆盖每局最大步数（默认 300）",
    )
    parser.add_argument(
        "--output-dir", type=str, default="experiments/results",
        help="结果输出目录（默认 ./experiments/results）",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        _log(f"路径不存在: {target}")
        sys.exit(1)

    configs = _collect_configs(target)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _log(f"共找到 {len(configs)} 个配置文件，结果将保存到 {output_dir}/")
    _log("")

    for cfg_path in configs:
        _log(f"{'=' * 60}")
        _log(f"配置: {cfg_path}")
        with open(cfg_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if args.max_moves is not None:
            config["max_moves"] = args.max_moves

        result = run_matchup(config, games_override=args.games)
        result["config_file"] = str(cfg_path)

        stem = cfg_path.stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"{stem}_{ts}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        s = result["summary"]
        _log(f"  汇总: {s['player_1']} 胜 {s['player_1_wins']}  "
             f"{s['player_2']} 胜 {s['player_2_wins']}  "
             f"和棋 {s['draws']}  平均步数 {s['avg_moves']}")
        _log(f"  结果已保存: {out_path}")
        _log("")

    _log("全部实验完成。")


if __name__ == "__main__":
    main()
