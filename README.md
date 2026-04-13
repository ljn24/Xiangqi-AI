# ♟️ 中国象棋 AI（Xiangqi-AI）

课程项目：完整规则引擎 + 多种搜索/评估策略 + **pygame 图形界面**，支持人机对弈、机机对弈与批量实验。

---

## ✨ 功能概览

| 模块 | 说明 |
|------|------|
| 🧠 **Agent** | 随机、极大极小（可配深度与评估函数）、MCTS；可选开局库包装 |
| 🖥️ **GUI** | 对局前配置双方类型与参数，棋盘点击走子，状态栏与终局提示 |
| ⌨️ **CLI** | 通过 YAML 配置双方 Agent，终端自动对弈（适合脚本与调试） |
| 📊 **实验** | 批量跑局、输出 JSON 结果；详见 `experiments/docs/` |

---

## 🛠️ 环境要求

- **Python 3.11**（与 `pyproject.toml` 中 `requires-python` 一致）
- 依赖：`pygame`、`pyyaml`

### 安装（任选其一）

**使用 uv（推荐，项目含 `uv.lock`）：**

```bash
cd Xiangqi-AI
uv sync
uv run python main.py
```

**使用 pip：**

```bash
cd Xiangqi-AI
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "pygame>=2.5" "pyyaml>=6.0"
python main.py
```

> 💡 **Linux / WSL 中文显示**：界面会尝试加载系统中文字体。若文字方块，请安装如 `fonts-noto-cjk` 或文泉驿等字体包。

---

## 🎮 GUI 使用方式

1. 在项目根目录执行：`python main.py`（不加参数即启动 GUI）。
2. **对局设置**：为红方、黑方分别选择类型（人类 / 随机 / 极大极小 / 蒙特卡洛）。极大极小可切换**搜索深度**与**评估函数**；若存在 `data/opening_book.json`，可开关**开局库**。
3. 点击 **「开始对弈」** 进入棋盘。
4. **人类走子**：先点击己方棋子，再点击绿色提示的合法落点；最后一手会有高亮提示。
5. **AI 走子**：轮到 AI 时后台计算，状态栏会显示思考中；双方均为 AI 时为观战模式。
6. 终局后点 **「再来一局」** 返回设置页。

关闭窗口即可退出。

---

## ⌨️ CLI 模式（可选）

使用 YAML 指定双方 Agent，例如（可参照 `experiments/configs/` 下的字段写法）：

```yaml
max_moves: 300
red:
  agent: minimax
  depth: 4
  evaluation: material_position
black:
  agent: mcts
```

保存为如 `my_game.yaml` 后执行：

```bash
python main.py --config my_game.yaml
```

`opening_book` 可设为相对路径字符串以加载开局库。

---

## 📊 批量实验

设计与操作说明见：

- [`experiments/docs/experiment_design.md`](experiments/docs/experiment_design.md)
- [`experiments/docs/experiment_guide.md`](experiments/docs/experiment_guide.md)

示例：

```bash
python experiments/scripts/run_experiments.py experiments/configs/A_algorithm/A1_random_vs_mcts.yaml
```

---

## 📁 主要目录

```
xiangqi/     # 规则与局面
agents/      # AI 与评估
gui/         # 界面与素材
data/        # 开局库等数据
experiments/ # 实验配置、脚本与文档
main.py      # 入口（默认 GUI）
```

祝对弈愉快 🎉
