# 项目长期笔记：《宇宙快递员》GALGAME

## 环境

- 引擎 Godot 4.3，`D:/godot/Godot_v4.3-stable_win64_console.exe`（机器上另有 4.7.2，别用，会触发重新导入）
- 项目 `config/features` 固定 4.3；渲染 gl_compatibility；1920x1080 + stretch keep
- 导出：Android arm64-v8a，debug 签名 `C:/Users/admin/.android/debug.keystore`

## 三条硬规矩（踩过坑）

1. **改 `.tscn` 务必核对节点路径**。已因 `parent=""` 和 `UI/` vs `UILayer/` 前缀栽过大跟头（游戏直接崩）。
2. **运行时绝不写 `res://`**，持久化一律 `user://`。写 `res://` 在编辑器里正常、打包后必崩。
3. **切场景一律 `call_deferred`**。从 `_ready()` 调用栈里同步 `change_scene_to_file()` 会报 `Parent node is busy adding/removing children` 并静默失败。

## 自检方法

```bash
"D:/godot/Godot_v4.3-stable_win64_console.exe" --headless --path "<项目目录>" --quit-after 120
```

- **不能用 `--script` 模式自检**：该模式 Autoload 不注册，`GameManager` 标识符编译失败。要建临时场景 + 临时改 `run/main_scene`，跑完改回。
- 自检应覆盖：场景节点树完整性、剧本解析、素材引用存在性、真实驱动跑完 12 章。
- 跑完全程约 2~4 分钟（700+ 句富文本排版），别误判卡死。

## 结构速查

- `game.tscn`：`Game → UILayer → {MenuBtn, Choices→Choice1-4, VNBox→NamePlate→NameLabel, Text, NextArrow}`
- 存档：槽位 0 自动存档，1~9 手动；`user://saves/slot_N.json`
- 加章节要同步三处：`story/chXX.txt`、`GameManager.LAST_CHAPTER`、`CHAPTER_TITLES`
