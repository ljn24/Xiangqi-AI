# 实验设计方案

## 概述

本文档为象棋 AI 项目的实验设计方案，旨在通过系统性的对比实验展示不同搜索算法、搜索深度、启发式评估函数以及开局库对 AI 棋力的影响。实验围绕以下核心问题展开：

1. 不同搜索算法（随机、MCTS、MiniMax）的棋力差异有多大？
2. 搜索深度如何影响 AI 棋力和搜索效率？
3. 不同启发式评估函数对 AI 棋力的影响有多大？
4. 开局库对 AI 开局表现和整体棋力有何贡献？

---

## 一、评估指标

### 1.1 棋力指标

| 指标 | 定义 | 用途 |
|:---|:---|:---|
| **胜率** | 多局对弈中获胜的比例 | 衡量不同配置之间的棋力强弱 |
| **平均对局步数** | 从开局到终局的平均步数 | 反映 AI 进攻性——更强的 AI 通常能更快取胜 |

### 1.2 效率指标

| 指标 | 定义 | 用途 |
|:---|:---|:---|
| **搜索节点数** | 每步搜索中访问的节点总数（`nodes_searched`） | 衡量搜索效率，值已内建于 `MinimaxAgent` |
| **每步平均耗时** | 单步搜索的平均时间（秒） | 衡量实际运行速度 |
| **有效分支因子** | `N^(1/d)`，N 为搜索节点数，d 为深度 | 反映剪枝效率，理想 Alpha-Beta 可将分支因子降至 `√b` |
| **时间-深度曲线** | 搜索耗时随深度的增长趋势 | 展示指数级增长及优化手段的效果 |

### 1.3 数据收集建议

- 涉及随机算法（MCTS、Random、开局库）的实验至少进行 **20 局对弈**（红黑各半，消除先后手偏差）
- 纯确定性对局（MiniMax vs MiniMax，无开局库）只需 **2 局**（红黑各 1 局），因为结果完全确定
- 记录每步的 `nodes_searched`、耗时，用于计算均值和标准差
- 使用实验脚本 `experiments/scripts/run_experiments.py` 读取 YAML 配置文件，自动运行 AI vs AI 对弈并收集数据

---

## 二、实验方案

### 实验 A：搜索算法对比

**目的：** 比较三种搜索算法（随机、MCTS、MiniMax）的棋力差异。

**三种算法：**

| 算法 | 说明 | 关键参数 |
|:---|:---|:---|
| `random` | 均匀随机选择合法走法 | 无 |
| `mcts` | UCT-MCTS，固定迭代次数 | 800 次迭代，UCB1 探索常数 √2 |
| `minimax` | Negamax + Alpha-Beta 剪枝 + MVV-LVA 走法排序 | depth=4，评估函数 `material_position` |

**实验方式：**

循环赛（Round-Robin）：三种算法两两对弈，每组 20 局（红黑各 10 局），共 3 组 matchup。

| 组别 | 红方 | 黑方 |
|:---|:---|:---|
| A1 | random | mcts |
| A2 | random | minimax |
| A3 | mcts | minimax |

**预期结果：**
- `random` 棋力最弱，基本上对任何有搜索能力的算法都会落败
- `minimax`（depth=4）应强于 `mcts`（800 次迭代），但 MCTS 在计算预算更大时可能反超
- 可构建 3×3 胜率矩阵

**配置文件示例（`A3_mcts_vs_minimax.yaml`）：**
```yaml
experiment: A_algorithm
description: MCTS vs MiniMax (depth=4)
games: 20
max_moves: 300
swap_colors: true

red:
  agent: mcts

black:
  agent: minimax
  depth: 4
  evaluation: material_position
```

---

### 实验 B：搜索深度对比

**目的：** 展示搜索深度对 MiniMax AI 棋力和搜索开销的影响。

**配置：**

| 变量 | 值 |
|:---|:---|
| 算法 | `minimax`（固定） |
| 评估函数 | `material_position`（固定） |
| 搜索深度 | 2, 3, 4, 5, 6 |

**实验方式：**

1. **相邻深度两两对弈：** depth=2 vs depth=3, depth=3 vs depth=4, ...，每组 2 局（红黑各 1 局，MiniMax 为确定性算法），统计胜率和效率指标。
2. **统一基准对比：** 每个深度（2-6）分别与 MCTS（800 次迭代）对弈 20 局，提供统一的棋力参照。

| 组别 | 红方 | 黑方 | 类型 |
|:---|:---|:---|:---|
| B1 | minimax depth=2 | minimax depth=3 | 两两对弈 |
| B2 | minimax depth=3 | minimax depth=4 | 两两对弈 |
| B3 | minimax depth=4 | minimax depth=5 | 两两对弈 |
| B4 | minimax depth=5 | minimax depth=6 | 两两对弈 |
| B5 | minimax depth=2 | mcts | vs 基准 |
| B6 | minimax depth=3 | mcts | vs 基准 |
| B7 | minimax depth=4 | mcts | vs 基准 |
| B8 | minimax depth=5 | mcts | vs 基准 |
| B9 | minimax depth=6 | mcts | vs 基准 |

**预期结果：**
- 更大的深度带来更高的胜率
- 搜索节点数和耗时呈指数增长
- 可以绘制 "深度 → 平均耗时" 和 "深度 → 平均节点数" 折线图
- vs MCTS 基准的胜率随深度上升，可绘制 "深度 → 对 MCTS 胜率" 曲线

---

### 实验 C：评估函数对比

**目的：** 展示不同复杂度的启发式评估函数对 AI 棋力的影响。

**四种评估函数：**

| 名称 | 考虑因素 | 复杂度 |
|:---|:---|:---|
| `piece_count` | 仅棋子数量差（不区分类型） | 最低 |
| `material` | 棋子加权价值（车>炮>马>...） | 低 |
| `material_position` | 棋子价值 + 位置加成（PST） | 中 |
| `material_position_mobility` | 棋子价值 + 位置 + 机动性 | 高 |

**实验方式：**

1. **循环赛（Round-Robin）：** 四种评估函数两两对弈，固定算法为 `minimax`、深度为 4，每组 2 局（红黑各 1 局，确定性对局），共 6 组 matchup。
2. **统一基准对比：** 每种评估函数（depth=4）分别与 MCTS（800 次迭代）对弈 20 局，提供统一的棋力参照。

| 组别 | 红方 | 黑方 | 类型 |
|:---|:---|:---|:---|
| C1-C6 | 评估函数 X | 评估函数 Y | 两两循环赛（6 组） |
| C7 | piece_count | mcts | vs 基准 |
| C8 | material | mcts | vs 基准 |
| C9 | material_position | mcts | vs 基准 |
| C10 | material_position_mobility | mcts | vs 基准 |

**预期结果：**
- `piece_count` 最弱，`material_position` 或 `material_position_mobility` 最强
- `material` vs `piece_count` 应有明显优势
- `material_position_mobility` 可能因机动性计算的额外开销而在相同深度下有略微不同的表现
- vs MCTS 基准的胜率随评估函数复杂度提升而上升

**分析要点：**
- 构建一个 4×4 的胜率矩阵（循环赛）
- 绘制各评估函数对 MCTS 的胜率柱状图（基准对比）
- 比较不同评估函数在相同深度下的每步耗时差异（尤其是 `material_position_mobility`）

---

### 实验 D：开局库对比

**目的：** 衡量开局库对 AI 开局阶段表现和整体棋力的影响。

**基础配置：**

| 变量 | 值 |
|:---|:---|
| 算法 | `minimax`（固定） |
| 搜索深度 | 4（固定） |
| 评估函数 | `material_position`（固定） |
| 开局库 | `data/opening_book.json` |

**实验方式：**

1. **MiniMax 内部对比：** 有/无开局库的 MiniMax 之间对弈。
2. **统一基准对比：** 有/无开局库的 MiniMax 分别与 MCTS 对弈，观察开局库对棋力的提升。

| 组别 | 红方 | 黑方 | 类型 |
|:---|:---|:---|:---|
| D1 | minimax + 开局库 | minimax + 开局库 | 双方均有开局库（对照：D1 无开局库） |
| D1' | minimax（无开局库） | minimax（无开局库） | 双方均无开局库（对照组） |
| D2 | minimax + 开局库 | minimax（无开局库） | 单方有 vs 单方无 |
| D3 | minimax + 开局库 | mcts | vs 基准（有开局库） |
| D4 | minimax（无开局库） | mcts | vs 基准（无开局库） |

- D1：20 局（开局库含随机选择，需多次采样）。D1'：2 局（纯确定性对照组）。
- D2：20 局（红黑各半，开局库引入随机性）。
- D3/D4：各 20 局（MCTS 含随机性），对比有/无开局库时对 MCTS 的胜率差异。

**预期结果：**
- D1 中双方都有开局库时，对局可能更标准化，步数可能更长（开局不容易犯错）
- D2 中有开局库的一方在开局阶段应有时间优势（查表 vs 搜索），棋力可能略有提升
- D3 vs D4 的胜率差可直接量化开局库带来的棋力提升

---

## 三、实验优先级建议

| 优先级 | 实验 | 难度 | 说明 |
|:---|:---|:---|:---|
| ★★★ | A. 搜索算法对比 | 低 | 三种算法已实现，只需跑对弈 |
| ★★★ | B. 搜索深度对比 | 低 | 只需修改配置文件中的深度参数 |
| ★★★ | C. 评估函数对比 | 低 | 已实现 4 种评估函数，只需跑对弈 |
| ★★☆ | D. 开局库对比 | 低 | 开局库已实现，只需切换开关 |

---

## 四、数据展示建议

### 表格

- **算法胜率矩阵**（实验 A）：3×3 表格，行列分别为 3 种搜索算法
- **深度-效率表**（实验 B）：每行一个深度，列为平均节点数、平均耗时、有效分支因子
- **深度 vs MCTS 胜率表**（实验 B）：每行一个深度，列为对 MCTS 的胜率
- **评估函数胜率矩阵**（实验 C）：4×4 表格，行列分别为 4 种评估函数
- **评估函数 vs MCTS 胜率表**（实验 C）：每种评估函数对 MCTS 的胜率
- **开局库对比表**（实验 D）：有/无开局库的胜率、平均对局步数、对 MCTS 胜率

### 图表

- **柱状图**：三种算法的胜率对比（实验 A）
- **折线图**：深度 vs 平均搜索耗时 / 平均节点数（实验 B）
- **折线图**：深度 vs 对 MCTS 胜率（实验 B）
- **热力图**：评估函数循环赛胜率矩阵（实验 C）
- **柱状图**：各评估函数对 MCTS 的胜率（实验 C）
- **柱状图**：有/无开局库的胜率和平均步数对比，含对 MCTS 胜率（实验 D）

### 报告结构建议

1. 算法说明（Random / MCTS / Minimax + Alpha-Beta + 评估函数设计思路）
2. 实验设置（配置、对局数、指标定义）
3. 实验结果与分析（表格 + 图表 + 文字讨论）
4. 结论与展望

---

## 五、自动化实验

项目提供了实验脚本和预定义的 YAML 配置文件，统一组织在 `experiments/` 目录下：

```
experiments/
├── scripts/    # 实验脚本（run_experiments.py）
├── configs/    # YAML 配置文件（按实验分子目录）
├── docs/       # 实验设计和操作指南
└── results/    # 实验结果输出（自动创建）
```

自动化流程：

1. 读取 YAML 配置文件（每个配置文件定义一组 matchup）
2. 运行 AI vs AI 对弈，收集每步的 `nodes_searched` 和耗时
3. 汇总统计结果（胜率、均值、标准差）
4. 输出为 JSON 文件（保存至 `experiments/results/` 目录），方便后续绘图分析

详细使用说明见 `experiments/docs/experiment_guide.md`。
