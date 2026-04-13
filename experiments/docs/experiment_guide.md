# 实验操作指南

本文档说明如何使用实验脚本开展实验，以及如何解读实验结果。

---

## 前置准备

确保已安装项目依赖（`pygame`、`pyyaml`），并且处于项目根目录：

```bash
cd HW/Xiangqi-AI
```

---

## 文件结构

```
Xiangqi-AI/
└── experiments/
    ├── scripts/                       # 实验脚本
    │   └── run_experiments.py
    ├── configs/                       # 实验配置文件（YAML）
    │   ├── A_algorithm/               # 实验 A：搜索算法对比
    │   │   ├── A1_random_vs_mcts.yaml
    │   │   ├── A2_random_vs_minimax.yaml
    │   │   └── A3_mcts_vs_minimax.yaml
    │   ├── B_depth/                   # 实验 B：搜索深度对比
    │   │   ├── B1_depth2_vs_depth3.yaml
    │   │   ├── B2_depth3_vs_depth4.yaml
    │   │   ├── B3_depth4_vs_depth5.yaml
    │   │   ├── B4_depth5_vs_depth6.yaml
    │   │   ├── B5_depth2_vs_mcts.yaml       # vs MCTS 基准
    │   │   ├── B6_depth3_vs_mcts.yaml
    │   │   ├── B7_depth4_vs_mcts.yaml
    │   │   ├── B8_depth5_vs_mcts.yaml
    │   │   └── B9_depth6_vs_mcts.yaml
    │   ├── C_evaluation/              # 实验 C：评估函数对比
    │   │   ├── C1_piece_count_vs_material.yaml
    │   │   ├── C2_piece_count_vs_material_position.yaml
    │   │   ├── C3_piece_count_vs_material_position_mobility.yaml
    │   │   ├── C4_material_vs_material_position.yaml
    │   │   ├── C5_material_vs_material_position_mobility.yaml
    │   │   ├── C6_material_position_vs_material_position_mobility.yaml
    │   │   ├── C7_piece_count_vs_mcts.yaml   # vs MCTS 基准
    │   │   ├── C8_material_vs_mcts.yaml
    │   │   ├── C9_material_position_vs_mcts.yaml
    │   │   └── C10_material_position_mobility_vs_mcts.yaml
    │   └── D_book/                    # 实验 D：开局库对比
    │       ├── D1_both_book_vs_both_no_book.yaml
    │       ├── D1_both_no_book.yaml
    │       ├── D2_book_vs_no_book.yaml
    │       ├── D3_book_vs_mcts.yaml           # vs MCTS 基准
    │       └── D4_no_book_vs_mcts.yaml
    ├── docs/                          # 实验文档
    │   ├── experiment_design.md
    │   └── experiment_guide.md
    └── results/                       # 实验结果输出（自动创建）
        └── *.json
```

---

## 脚本用法

所有命令均在项目根目录下运行。

### 基本用法

```bash
# 运行单个配置文件
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/A1_random_vs_mcts.yaml

# 运行一组实验（目录下所有 YAML 配置）
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/

# 运行全部实验
python experiments/scripts/run_experiments.py experiments/configs/
```

### 可选参数

| 参数 | 说明 | 默认值 |
|:---|:---|:---|
| `--games N` | 覆盖配置文件中的对弈局数 | 配置文件中的值（通常 20） |
| `--max-moves N` | 覆盖每局最大步数 | 300 |
| `--output-dir DIR` | 结果输出目录 | `./experiments/results` |

```bash
# 快速测试（每组只跑 2 局）
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/ --games 2

# 正式实验（20 局，结果输出到自定义目录）
python experiments/scripts/run_experiments.py experiments/configs/ --output-dir my_results
```

---

## 建议的实验步骤

### 第一步：快速冒烟测试

先用少量对局验证脚本和配置能正常运行：

```bash
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/A1_random_vs_mcts.yaml --games 2
```

确认 `experiments/results/` 下生成了 JSON 结果文件，并检查内容格式正确。

### 第二步：按顺序运行正式实验

建议按以下顺序开展，从快到慢：

**实验 A — 搜索算法对比**（耗时：中等）

```bash
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/
```

- A1（Random vs MCTS）：每局约 10-30 秒（MCTS 800 次迭代 × 每步）
- A2（Random vs MiniMax）：每局约 5-15 秒
- A3（MCTS vs MiniMax）：每局约 30-60 秒

**实验 B — 搜索深度对比**（耗时：低→高）

```bash
python experiments/scripts/run_experiments.py experiments/configs/B_depth/
```

两两对弈（B1-B4，确定性对局，各 2 局）：
- B1（depth 2 vs 3）：很快，总计几秒
- B2（depth 3 vs 4）：总计约 20 秒
- B3（depth 4 vs 5）：总计约几分钟
- B4（depth 5 vs 6）：总计可能 20+ 分钟

vs MCTS 基准（B5-B9）：
- B5（depth 2 vs MCTS）：每局约 30-60 秒
- B6-B7（depth 3-4 vs MCTS）：每局约 30-90 秒
- B8-B9（depth 5-6 vs MCTS）：每局可能数分钟（取决于深层搜索耗时）

> 提示：如果 B4 或 B9 耗时过长，可以先用 `--games 4` 跑少量对局确认趋势。

**实验 C — 评估函数对比**（耗时：中等）

```bash
python experiments/scripts/run_experiments.py experiments/configs/C_evaluation/
```

循环赛（C1-C6，确定性对局，各 2 局）：6 组 matchup，都使用 depth=4，每组总计约 20-60 秒。
vs MCTS 基准（C7-C10）：4 组 matchup，每局约 30-90 秒。

**实验 D — 开局库对比**（耗时：中等）

```bash
python experiments/scripts/run_experiments.py experiments/configs/D_book/
```

MiniMax 内部对比（D1-D2）：D1 有开局库（20 局），D1' 无开局库对照组（2 局），D2 一方有开局库（20 局），均使用 depth=4。
vs MCTS 基准（D3-D4）：2 个配置文件，每局约 30-90 秒。

### 第三步：检查结果

```bash
ls experiments/results/
```

每个配置文件会生成一个带时间戳的 JSON 结果文件，例如 `A1_random_vs_mcts_20260413_143022.json`。

---

## 结果 JSON 格式说明

每个结果文件的结构如下：

```json
{
  "experiment": "A_algorithm",
  "description": "Random vs MCTS",
  "player_1_config": {"agent": "random"},
  "player_2_config": {"agent": "mcts"},
  "config_file": "experiments/configs/A_algorithm/A1_random_vs_mcts.yaml",
  "timestamp": "2026-04-13T06:30:22.123456+00:00",
  "games": [
    {
      "game_id": 1,
      "red_config": {"agent": "random"},
      "black_config": {"agent": "mcts"},
      "swapped": false,
      "winner": "black",
      "winner_player": "player_2",
      "total_moves": 67,
      "move_stats": [
        {"side": "red", "move": "h0g2", "time_s": 0.000012, "nodes": null, "player": "player_1"},
        {"side": "black", "move": "h9g7", "time_s": 1.234567, "nodes": null, "player": "player_2"}
      ]
    }
  ],
  "summary": {
    "total_games": 20,
    "player_1": "random",
    "player_2": "mcts",
    "player_1_wins": 1,
    "player_2_wins": 17,
    "draws": 2,
    "avg_moves": 72.4,
    "player_1_avg_time_per_move": 0.000015,
    "player_2_avg_time_per_move": 1.123456,
    "player_1_avg_nodes_per_move": null,
    "player_2_avg_nodes_per_move": null
  }
}
```

### 字段说明

| 字段 | 说明 |
|:---|:---|
| `player_1` / `player_2` | YAML 中 `red` / `black` 对应的逻辑选手，不受颜色交换影响 |
| `swapped` | 该局是否交换了红黑方（`true` 时 player_1 执黑） |
| `winner` | 棋盘上的获胜方：`"red"` / `"black"` / `"draw"` |
| `winner_player` | 逻辑上的获胜选手：`"player_1"` / `"player_2"`（和棋时无此字段） |
| `player` | 每步 move_stats 中标记该步属于哪个逻辑选手 |
| `time_s` | 该步搜索耗时（秒） |
| `nodes` | 搜索节点数（仅 MiniMax 有值，其他算法为 `null`） |
| `summary` | 按逻辑选手汇总的统计数据 |

### 关于颜色交换（swap_colors）

当配置中 `swap_colors: true` 时，脚本会自动将 N 局对弈分为两半：

- 前 N/2 局：按配置文件中的红黑方执行
- 后 N/2 局：交换红黑方

每局的 `red_config` / `black_config` 反映了实际执行时的配置。分析结果时请注意这一点：同一个算法可能在前半段是红方、后半段是黑方。

---

## 自定义实验

如果需要增加新的 matchup，只需在 `experiments/configs/` 中创建新的 YAML 配置文件。配置文件格式：

```yaml
experiment: 实验组名
description: 描述
games: 20
max_moves: 300
swap_colors: true

red:
  agent: minimax          # random | minimax | mcts
  depth: 4                # 仅 minimax 使用
  evaluation: material_position  # 仅 minimax 使用
  opening_book: data/opening_book.json  # 可选

black:
  agent: mcts
```

- `agent`：必填，可选 `random` / `minimax` / `mcts`
- `depth`、`evaluation`：仅 `minimax` 使用
- `opening_book`：可选，指定开局库文件路径
- `swap_colors`：是否自动交换红黑方（推荐 `true`）
