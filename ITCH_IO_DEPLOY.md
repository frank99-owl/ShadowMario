# itch.io 部署指南

## 1. 注册账号

访问 https://itch.io 注册一个免费账号。

## 2. 创建新项目

1. 登录后点击右上角头像 → **Create new project**
2. 填写项目信息：
   - **Title**: Shadow Mario
   - **Kind of project**: 选 `HTML`（关键！）
   - **Classification**: 选 `Game`
   - **Release status**: 选 `Released` 或 `In development`

## 3. 上传游戏文件

1. 在 **Uploads** 区域，点击 **Upload files**
2. 选择项目根目录下的 `shadow-mario-web.zip`（约 251KB）
3. 上传完成后，在文件列表中找到该文件，勾选：
   - ☑️ **This file will be played in the browser**

## 4. 设置画面尺寸（重要）

在 **Embed options** 区域：
- **Viewport width**: `1024`
- **Viewport height**: `768`
- **Fullscreen button**: 建议勾选

## 5. 保存并发布

1. 点击页面底部的 **Save & view page**
2. 你的游戏链接格式为：`https://你的用户名.itch.io/shadow-mario`
3. 把链接发给朋友，他们打开就能直接在浏览器里玩

## 文件说明

| 文件 | 说明 |
|------|------|
| `shadow-mario-web.zip` | 包含 index.html + 游戏资源包，直接上传即可 |
| `build/web/` | 解压后的目录，如果 itch.io 支持直接上传文件夹也可以用 |

## 注意事项

- 第一次打开游戏时，浏览器会下载约 250KB 的资源，加载需要几秒
- 游戏需要支持 WebAssembly 的现代浏览器（Chrome/Firefox/Safari/Edge 均支持）
- 由于浏览器安全限制，游戏可能需要用户点击一下页面才能开始（pygbag 会自动提示）
