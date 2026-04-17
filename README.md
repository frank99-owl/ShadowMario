# Shadow Mario

一款 2D 平台跳跃游戏，使用 Python + Pygame 开发。玩家操控角色穿越三关，收集金币、躲避敌人、击败 Boss，最终抵达终点旗帜。

## 环境要求

- Python 3.11+
- Pygame 2.5.0+

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

## 操作说明

| 按键 | 功能 |
|------|------|
| `←` / `→` | 左右移动 |
| `↑` | 跳跃 |
| `S` | 发射火球（仅第三关 Boss 战） |
| `1` / `2` / `3` | 选择关卡 |
| `ESC` | 退出游戏 |
| `空格` | 返回主菜单 |

## 游戏机制

- **三关设计**：从基础教学关到飞行平台挑战，最终迎战 Boss
- **道具系统**：无敌状态（免疫伤害）、双倍分数（金币收益翻倍），持续约 8 秒
- **Boss 战**：第三关 Boss 会在玩家距离超过 500 像素时概率发射火球，需用火球反击
- **胜负条件**：生命值归零或掉出屏幕下方则失败，击败 Boss 并触碰终点旗则胜利

## 项目结构

```
ShadowMarioPython/
├── res/                    # 游戏资源
│   ├── app.properties      # 游戏参数配置
│   ├── level1.csv          # 关卡 1 数据
│   ├── level2.csv          # 关卡 2 数据
│   ├── level3.csv          # 关卡 3 数据
│   ├── *.png               # 精灵图
│   └── FSO8BITR.TTF        # 像素字体
├── shadow_mario/
│   ├── main.py             # 游戏入口、状态机
│   ├── config.py           # 配置加载
│   ├── level.py            # 关卡管理器
│   ├── io_utils.py         # CSV/properties 读取
│   └── entities/           # 游戏实体
│       ├── player.py       # 玩家角色
│       ├── platform.py     # 普通平台
│       ├── flying_platform.py  # 飞行平台
│       ├── enemy.py        # 普通敌人
│       ├── enemy_boss.py   # Boss
│       ├── coin.py         # 金币
│       ├── power_up.py     # 道具基类
│       ├── invincible_power.py  # 无敌道具
│       ├── double_score_power.py # 双倍分数
│       ├── fireball.py     # 火球
│       └── end_flag.py     # 终点旗帜
├── requirements.txt
├── run.sh
├── README.md               # 本文件（中文）
└── README_EN.md            # 英文版
```
