# Shadow Mario

基于 Python + Pygame 的 2D 平台游戏，当前版本包含 4 个关卡、场景系统、音频与存档系统，以及一套增强视觉效果（粒子、震动、过渡）。

## 版本说明（当前）

- 第 1/2/3 关保留 GitHub 经典平台玩法逻辑（平台/角色手感对齐老版）
- 第 2 关为单层平台挑战，第 3 关为双层平台 + Boss
- 第 4 关为双人竞速模式（P1 vs P2）
- 保留并启用增强效果：落地尘土、受击粒子、金币特效、Boss 死亡效果、屏幕震动

## 环境要求

- Python 3.10+
- Pygame 2.5.0+

## 安装与运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

也可以：

```bash
./run.sh
```

## 操作说明

### 菜单/通用

| 按键 | 功能 |
|------|------|
| `↑` / `↓` | 菜单选择 |
| `Enter` / `Space` | 确认 |
| `1` / `2` / `3` / `4` | 从菜单快速进入对应关卡 |
| `ESC` | 暂停 / 返回 / 退出（视场景而定） |
| `F12` | 截图（保存到 `screenshots/`） |

### 第 1-3 关（单人）

| 按键 | 功能 |
|------|------|
| `←` / `→` | 左右移动 |
| `↑` | 跳跃 |
| `S` | 发射火球（Boss 可交战范围内） |

### 第 4 关（双人竞速）

| 玩家 | 按键 |
|------|------|
| P1 | `W` / `A` / `D` |
| P2 | `↑` / `←` / `→` |

规则要点：

- 双方初始生命值 100，被敌人碰撞一次扣 25
- 任一玩家到达终点旗后结束，按分数判定胜者
- 若一方掉队并离开屏幕可视范围，另一方直接获胜

## 系统特性

- 场景管理：主菜单、选关、加载、游戏中、暂停、结算、设置
- 音频管理：BGM/SFX、主音量、静音开关
- 存档系统：关卡解锁、最高分、最佳时间、总金币
- 运行时配置：`res/runtime_config.json` 可调 UI/颜色/碰撞体缩放

## 项目结构

```
ShadowMarioPython/
├── main.py                    # 当前主入口（推荐）
├── run.sh                     # 便捷启动脚本
├── requirements.txt
├── res/
│   ├── app.properties         # 基础配置（含 level1~level4 路径）
│   ├── message_en.properties  # 文案
│   ├── level1.csv
│   ├── level2.csv
│   ├── level3.csv
│   ├── level4.csv
│   ├── runtime_config.json
│   ├── sounds/                # 音效与 BGM
│   └── *.png / *.TTF
├── shadow_mario/
│   ├── config.py
│   ├── level.py
│   ├── audio.py
│   ├── particles.py
│   ├── save.py
│   ├── runtime_config.py
│   ├── scenes/                # 场景系统
│   └── entities/              # 游戏实体
├── save.json                  # 运行时自动生成
└── screenshots/               # F12 截图输出目录
```

## 上传前检查（建议）

```bash
python3 -m py_compile main.py
python3 main.py
```

手工确认：

- 菜单可进入 1-4 关
- 第 2/3 关平台移动与落地手感符合预期
- 第 4 关双人竞速规则正常
- 音效、粒子与震动效果可见

## License

MIT（见 `LICENSE`）
