# Shadow Mario（Python + Pygame）

Shadow Mario 是一个基于 Python + Pygame 的 2D 平台游戏项目。  
当前项目包含 4 个关卡、完整场景系统（菜单/加载/游戏/暂停/设置/结算）、音频与存档系统，以及粒子/震屏/过渡等效果模块。

## 功能概览

- 四个可游玩关卡
- 第 2/3 关平台行为对齐经典实现逻辑
- 第 4 关为双人竞速模式（P1 vs P2）
- 运行时配置支持（`res/runtime_config.json`）
- 存档支持关卡解锁、最高分、最佳时间与音量设置

## 玩法规则

- 第 1 关：教学风格的单人关卡
- 第 2 关：双层移动平台关卡
- 第 3 关：单层平台 + Boss 战关卡
- 第 4 关：双人竞速，按得分判定胜负
- 终点规则：在关卡数据中，终点旗帜右侧不再生成实体

## 环境要求

- Python 3.10+
- pip
- 可用的桌面图形环境（Pygame/SDL）

## 快速运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

也可以使用：

```bash
./run.sh
```

## 操作说明

### 菜单/全局

- `Up` / `Down`：菜单选择
- `Enter` / `Space`：确认
- `1` / `2` / `3` / `4`：菜单快速进关
- `Esc`：返回/暂停/退出（视场景而定）
- `F12`：截图到 `screenshots/`

### 第 1-3 关（单人）

- `Left` / `Right`：移动
- `Up`：跳跃
- `S`：Boss 进入激活范围后可发射，火球方向跟随角色朝向（左/右）

### 第 4 关（双人）

- `P1`：`W` / `A` / `D`
- `P2`：`Up` / `Left` / `Right`

## 项目结构

```text
ShadowMarioPython/
├── main.py                    # 脚本入口
├── run.sh
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── res/                       # 资源与配置
├── shadow_mario/
│   ├── app.py                 # 统一运行入口
│   ├── app_context.py         # 共享上下文依赖
│   ├── scene_payloads.py      # 场景跳转数据模型
│   ├── level.py               # 关卡主编排
│   ├── level_components.py    # 关卡协作组件
│   ├── scenes/
│   └── entities/
├── tests/
└── .github/workflows/ci.yml
```

## 开发与检查

安装开发依赖：

```bash
pip install -r requirements-dev.txt
```

执行统一检查：

```bash
make check
```

## itch.io 自动发布

仓库已包含 `.github/workflows/deploy-itch.yml`，可在每次推送 `main` 后自动上传到 itch.io。

1. 在 GitHub 仓库里添加 Secret：`BUTLER_API_KEY`（来自 itch.io API keys）。
2. 可选添加仓库变量：
   - `ITCH_GAME`（默认：`frank-owl/shadowmario`）
   - `ITCH_SOURCE_CHANNEL`（默认：`source`）
   - `ITCH_WEB_CHANNEL`（仅兜底，默认：`web`）
3. 推送到 `main`（或在 Actions 页面手动触发）。

工作流每次会上传两份产物：

- 源码包（`git archive`）：

```bash
butler push dist/shadowmario-source.zip frank-owl/shadowmario:source
```

- 网页包（`pygbag`，用于网页可玩版本同步）：

```bash
butler push build/web.zip frank-owl/shadowmario:web
```

针对网页可玩版本，工作流会先自动识别 itch 页面当前嵌入运行的 HTML 通道，并优先推送到该通道；只有自动识别失败时，才回退到 `ITCH_WEB_CHANNEL`。

## 常见问题

- 无法初始化图形窗口：确认本机图形环境可用。
- 没有声音：检查系统音频设备、游戏内静音和音量配置。
- 存档异常：删除 `save.json` 后重启。

## 其他文档

- 英文主文档：[README.md](README.md)
- 英文兼容入口：[README_EN.md](README_EN.md)

## 许可证

MIT，详见 [LICENSE](LICENSE)。
