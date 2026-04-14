"""从 C7–C10（Minimax 各评估函数 depth=4 vs MCTS）结果 JSON 生成三张折线图。

横轴为评估函数（固定顺序：由简到繁），纵轴与 plot_b_depth_vs_mcts.py 一致：
平均对局步数、Minimax 侧每步平均耗时、Minimax 侧每步平均节点数。
输出目录：experiments/figures/c_eval_vs_mcts/

用法（在项目根目录）:
    uv run python experiments/scripts/plot_c_eval_vs_mcts.py
    uv run python experiments/scripts/plot_c_eval_vs_mcts.py --dpi 400
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RESULTS_GLOB = "C*_vs_mcts*.json"
# 与实验设计一致：由简到繁，横轴阅读顺序
_EVAL_ORDER: tuple[str, ...] = (
    "piece_count",
    "material",
    "material_position",
    "material_position_mobility",
)
_DEFAULT_SAVE_DPI = 300


def _apply_reference_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.linewidth": 1.0,
            "axes.grid": True,
            "grid.linestyle": "--",
            "grid.alpha": 0.6,
            "grid.color": "0.7",
            "legend.frameon": True,
            "legend.edgecolor": "0.6",
            "legend.facecolor": "white",
            "font.size": 12,
        }
    )


def _load_c_vs_mcts_series(
    results_dir: Path,
) -> tuple[list[str], list[float], list[float], list[float]]:
    """按 _EVAL_ORDER 返回 (eval_names, avg_moves, p1_time, p1_nodes)。"""
    by_eval: dict[str, dict] = {}
    for path in results_dir.glob(_RESULTS_GLOB):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if data.get("experiment") != "C_evaluation":
            continue
        p1 = data.get("player_1_config") or {}
        p2 = data.get("player_2_config") or {}
        if p1.get("agent") != "minimax" or p2.get("agent") != "mcts":
            continue
        ev = p1.get("evaluation")
        if not isinstance(ev, str):
            continue
        summary = data.get("summary") or {}
        if ev in by_eval:
            raise ValueError(f"重复的评估函数结果: {ev}（{path.name}）")
        by_eval[ev] = summary

    missing = [e for e in _EVAL_ORDER if e not in by_eval]
    if missing:
        raise FileNotFoundError(
            f"未找到以下评估函数 vs MCTS 的结果 JSON（在 {results_dir} 下 glob {_RESULTS_GLOB}）: {missing}"
        )

    names = list(_EVAL_ORDER)
    avg_moves = [float(by_eval[e]["avg_moves"]) for e in names]
    p1_time = [float(by_eval[e]["player_1_avg_time_per_move"]) for e in names]
    nodes_raw = [by_eval[e].get("player_1_avg_nodes_per_move") for e in names]
    if any(n is None for n in nodes_raw):
        raise ValueError("部分汇总的 Minimax 平均节点数为 null，无法作图")
    p1_nodes = [float(n) for n in nodes_raw]
    return names, avg_moves, p1_time, p1_nodes


def _plot_line_categorical(
    x_labels: list[str],
    y: list[float],
    *,
    ylabel: str,
    title: str,
    outfile: Path,
    log_y: bool,
    series_label: str,
    xaxis_label: str,
    color: str = "tab:blue",
    save_dpi: int = _DEFAULT_SAVE_DPI,
) -> None:
    xs = list(range(len(x_labels)))
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    (line,) = ax.plot(
        xs,
        y,
        color=color,
        linestyle="-",
        linewidth=2.25,
        marker="o",
        markersize=10,
        markerfacecolor=color,
        markeredgecolor=color,
        label=series_label,
    )
    ax.set_xticks(xs)
    ax.set_xticklabels(x_labels, rotation=22, ha="right")
    ax.set_xlabel(xaxis_label)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_y:
        ax.set_yscale("log")
    ax.legend(handles=[line], loc="upper right", fontsize=12)
    ax.margins(x=0.08)
    ax.tick_params(axis="both", labelsize=12)
    fig.tight_layout()
    outfile.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        outfile,
        bbox_inches="tight",
        dpi=save_dpi,
        facecolor="white",
        edgecolor="none",
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="绘制 C7–C10 评估函数 vs MCTS 三指标折线图")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=_PROJECT_ROOT / "experiments" / "results",
        help="实验结果 JSON 目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "experiments" / "figures" / "c_eval_vs_mcts",
        help="图片输出目录",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=_DEFAULT_SAVE_DPI,
        metavar="N",
        help=f"导出 PNG 分辨率（默认 {_DEFAULT_SAVE_DPI}）",
    )
    args = parser.parse_args()

    _apply_reference_style()
    names, avg_moves, p1_time, p1_nodes = _load_c_vs_mcts_series(args.results_dir.resolve())
    out = args.output_dir.resolve()
    dpi = max(72, args.dpi)

    xaxis_label = "Minimax evaluation function (depth=4)"
    display_labels = list(names)

    _plot_line_categorical(
        display_labels,
        avg_moves,
        ylabel="Avg. moves per game",
        title="Avg. game length vs evaluation (Minimax vs MCTS, n=20)",
        outfile=out / "c_eval_vs_mcts_avg_moves.png",
        log_y=False,
        series_label="Avg. moves",
        xaxis_label=xaxis_label,
        color="tab:green",
        save_dpi=dpi,
    )
    _plot_line_categorical(
        display_labels,
        p1_time,
        ylabel="Avg. time per move (s), log scale",
        title="Minimax avg. time per move vs evaluation (log y)",
        outfile=out / "c_eval_vs_mcts_minimax_time_per_move.png",
        log_y=True,
        series_label="Minimax time / move",
        xaxis_label=xaxis_label,
        color="tab:blue",
        save_dpi=dpi,
    )
    _plot_line_categorical(
        display_labels,
        p1_nodes,
        ylabel="Avg. nodes searched per move, log scale",
        title="Minimax avg. nodes per move vs evaluation (log y)",
        outfile=out / "c_eval_vs_mcts_minimax_nodes.png",
        log_y=True,
        series_label="Minimax nodes / move",
        xaxis_label=xaxis_label,
        color="tab:orange",
        save_dpi=dpi,
    )

    print(f"已写入 {out}:")
    for name in (
        "c_eval_vs_mcts_avg_moves.png",
        "c_eval_vs_mcts_minimax_time_per_move.png",
        "c_eval_vs_mcts_minimax_nodes.png",
    ):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
