"""从 B5–B9（Minimax 各 depth vs MCTS）结果 JSON 生成三张折线图。

指标：平均对局步数、Minimax 侧每步平均耗时、Minimax 侧每步平均节点数。
输出目录：experiments/figures/b_depth_vs_mcts/

用法（在项目根目录）:
    uv run python experiments/scripts/plot_b_depth_vs_mcts.py
    uv run python experiments/scripts/plot_b_depth_vs_mcts.py --dpi 400
    uv run python experiments/scripts/plot_b_depth_vs_mcts.py --results-dir experiments/results
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RESULTS_GLOB = "B*_depth*_vs_mcts*.json"
_DEPTH_FILE_RE = re.compile(r"B\d+_depth(\d+)_vs_mcts", re.IGNORECASE)
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


def _load_b_vs_mcts_series(results_dir: Path) -> tuple[list[int], list[float], list[float], list[float]]:
    """返回按 depth 升序排列的 (depths, avg_moves, p1_time, p1_nodes)。"""
    rows: list[tuple[int, dict]] = []
    for path in sorted(results_dir.glob(_RESULTS_GLOB)):
        m = _DEPTH_FILE_RE.search(path.name)
        if not m:
            continue
        depth = int(m.group(1))
        if depth < 2 or depth > 6:
            continue
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if data.get("experiment") != "B_depth":
            continue
        p1 = data.get("player_1_config") or {}
        if p1.get("agent") != "minimax":
            continue
        summary = data.get("summary") or {}
        rows.append((depth, summary))

    if not rows:
        raise FileNotFoundError(
            f"未在 {results_dir} 找到匹配的 B_depth vs MCTS 结果（glob: {_RESULTS_GLOB}）"
        )

    rows.sort(key=lambda r: r[0])
    depths = [r[0] for r in rows]
    avg_moves = [float(r[1]["avg_moves"]) for r in rows]
    p1_time = [float(r[1]["player_1_avg_time_per_move"]) for r in rows]
    nodes_raw = [r[1].get("player_1_avg_nodes_per_move") for r in rows]
    if any(n is None for n in nodes_raw):
        raise ValueError("部分对局的 Minimax 平均节点数为 null，无法作图")
    p1_nodes = [float(n) for n in nodes_raw]
    return depths, avg_moves, p1_time, p1_nodes


def _plot_line(
    depths: list[int],
    y: list[float],
    *,
    ylabel: str,
    title: str,
    outfile: Path,
    log_y: bool,
    series_label: str,
    color: str = "tab:blue",
    save_dpi: int = _DEFAULT_SAVE_DPI,
) -> None:
    # figsize（英寸）× save_dpi ≈ 像素尺寸；默认 300 dpi 约 2100×1350 px
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    (line,) = ax.plot(
        depths,
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
    ax.set_xticks(depths)
    ax.set_xlabel("Minimax search depth")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_y:
        ax.set_yscale("log")
    ax.legend(handles=[line], loc="upper right", fontsize=12)
    ax.margins(x=0.06)
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
    parser = argparse.ArgumentParser(description="绘制 B5–B9 三指标折线图")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=_PROJECT_ROOT / "experiments" / "results",
        help="实验结果 JSON 目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "experiments" / "figures" / "b_depth_vs_mcts",
        help="图片输出目录",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=_DEFAULT_SAVE_DPI,
        metavar="N",
        help=f"导出 PNG 分辨率（默认 {_DEFAULT_SAVE_DPI}，可改为 400 等以进一步提高清晰度）",
    )
    args = parser.parse_args()

    _apply_reference_style()
    depths, avg_moves, p1_time, p1_nodes = _load_b_vs_mcts_series(args.results_dir.resolve())
    out = args.output_dir.resolve()

    dpi = max(72, args.dpi)

    _plot_line(
        depths,
        avg_moves,
        ylabel="Avg. moves per game",
        title="Avg. game length vs depth (Minimax vs MCTS, n=20)",
        outfile=out / "b_depth_vs_mcts_avg_moves.png",
        log_y=False,
        series_label="Avg. moves",
        color="tab:green",
        save_dpi=dpi,
    )
    _plot_line(
        depths,
        p1_time,
        ylabel="Avg. time per move (s), log scale",
        title="Minimax avg. time per move vs depth (log y)",
        outfile=out / "b_depth_vs_mcts_minimax_time_per_move.png",
        log_y=True,
        series_label="Minimax time / move",
        color="tab:blue",
        save_dpi=dpi,
    )
    _plot_line(
        depths,
        p1_nodes,
        ylabel="Avg. nodes searched per move, log scale",
        title="Minimax avg. nodes per move vs depth (log y)",
        outfile=out / "b_depth_vs_mcts_minimax_nodes.png",
        log_y=True,
        series_label="Minimax nodes / move",
        color="tab:orange",
        save_dpi=dpi,
    )

    print(f"已写入 {out}:")
    for name in (
        "b_depth_vs_mcts_avg_moves.png",
        "b_depth_vs_mcts_minimax_time_per_move.png",
        "b_depth_vs_mcts_minimax_nodes.png",
    ):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
