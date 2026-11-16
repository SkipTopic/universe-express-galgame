# 宇宙快递员 / Universe Express

一部改编自作者童年手写小说的科幻视觉小说（GALGAME）。12 章、约 2414 步剧情，Godot 4.7 引擎，1080P 横屏，可导出 Android。

美术（42 张立绘 / 36 张背景 / CG / 标题主视觉）与代码全部通过 AI 协作完成，开发过程按 step00–step18 逐步提交，见 [`开发记录.md`](开发记录.md)。

## 下载

最新版本 **v1.4.2**，APK 在 [Releases](../../releases) 页面。

> 安装包为 debug 签名，安装时需允许「未知来源」。包名 `com.universeexpress.galgame`，arm64-v8a。

## 玩法

点击推进对话。底部控制条支持 **历史回顾 / 自动播放 / 快进 / 设置**。9 个手动存档位 + 1 个自动存档，自动存档保存在 `user://saves/slot_0.json`。

## 技术栈

| 项 | 说明 |
|---|---|
| 引擎 | Godot 4.7.2，GL Compatibility 渲染后端 |
| 脚本 | GDScript（`scripts/`，3 个 Autoload：GameManager / Settings / AudioManager） |
| 剧本 | 纯文本 `story/ch01.txt`–`ch12.txt`，一行一步，语法见 `story/格式说明.txt` |
| 分辨率 | 1920×1080，canvas_items 拉伸，横屏 |
| 字体 | 思源宋体 Noto Serif SC（正文 Regular + 名牌 Bold） |

## 仓库结构

```
assets/          美术、音频、字体（立绘 1489×2234 底对齐，背景 16:9）
scenes/          主场景与游戏场景
scripts/         GDScript：章节播放器、剧本解析、存档、音频、设置
story/           12 章剧本正文 + 格式说明（纯文本，可直接编辑）
docs/AI工作流/    AI 生图提示词规范、AI 漫剧生产阶段图
开发记录.md      step00–step18 逐步开发记录
交接文档.md      引擎能力、美术资产清单、工具链、踩坑规矩
```

## 关于 AI 工作流

这个项目从提取小说、生成美术到写代码、逐帧验收，全流程都与 AI 协作完成。相关的四份文档：

- [`开发记录.md`](开发记录.md) — step00 到 step18，每一步做了什么、为什么改
- [`交接文档.md`](交接文档.md) — 工具链（豆包生图管线、帧渲染验证、批量回归）、引擎能力、硬规矩
- [`docs/AI工作流/AI生图提示词.md`](docs/AI工作流/AI生图提示词.md) — 统一画风前缀与逐图提示词规范
- [`docs/AI工作流/AI漫剧生产-第一阶段文本开发包.md`](docs/AI工作流/AI漫剧生产-第一阶段文本开发包.md) — 0–5 阶段生产流程图（选题 → 文本 → 视觉 → 故事板 → 静帧 → 动态）

## 版本

当前 **v1.4.2**（2026-11-15）。完整版本史见 [`交接文档.md`](交接文档.md)。

## 说明

- 剧情文字与手稿扫描页为作者童年原创内容，版权归作者所有。
- 美术图像由 AI 生成；字体 Noto Serif SC 遵循 SIL Open Font License。
