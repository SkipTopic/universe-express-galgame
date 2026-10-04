# 项目长期笔记：《宇宙快递员》GALGAME

## 环境

- 引擎 Godot **4.7**，`D:/godot/Godot_v4.7.2-stable_win64_console.exe`（机器上还有 4.3，但项目已升级到 4.7，别混用会触发重新导入）
- 项目 `config/features` 固定 4.7；渲染 gl_compatibility；1920x1080 + stretch keep
- 全局中文字体走项目设置 `gui/theme/custom_font` → `assets/fonts/simhei.ttf`。Godot 自带字体不含中文字形，导出 Android 会变方块
- 导出：Android arm64-v8a，debug 签名 `C:/Users/admin/.android/debug.keystore`

## 三条硬规矩（踩过坑）

1. **改 `.tscn` 务必核对节点路径**。已因 `parent=""` 和 `UI/` vs `UILayer/` 前缀栽过大跟头（游戏直接崩）。
2. **运行时绝不写 `res://`**，持久化一律 `user://`。写 `res://` 在编辑器里正常、打包后必崩。
3. **切场景一律 `call_deferred`**。从 `_ready()` 调用栈里同步 `change_scene_to_file()` 会报 `Parent node is busy adding/removing children` 并静默失败。

## 自检方法

```bash
"D:/godot/Godot_v4.7.2-stable_win64_console.exe" --headless --path "<项目目录>" --quit-after 120
```

- **不能用 `--script` 模式自检**：该模式 Autoload 不注册，`GameManager` 标识符编译失败。要建临时场景 + 临时改 `run/main_scene`，跑完改回。
- 自检应覆盖：场景节点树完整性、剧本解析、素材引用存在性、真实驱动跑完 12 章。
- 跑完全程约 2~4 分钟（700+ 句富文本排版），别误判卡死。

## 结构速查

- `game.tscn`：`Game → UILayer → {MenuBtn, CtrlBar→(Auto/Skip/History/Settings)Btn, Choices→Choice1-4, VNBox→NamePlate→NameLabel, Text, NextArrow, HistoryPanel, SettingsPanel}`
- Autoload 三个：`GameManager`（进度+存档）、`Settings`（偏好，user://settings.json）、`AudioManager`（BGM/音效）
- 存档：槽位 0 自动存档，1~9 手动；`user://saves/slot_N.json`
- 加章节要同步三处：`story/chXX.txt`、`GameManager.LAST_CHAPTER`、`CHAPTER_TITLES`
- 剧本分支语法：`【选择】文本:标签` + `【标签】xxx` + `【跳转】xxx`（详见 story/格式说明.txt）

## 一个 GDScript 坑

数组常量**必须显式标注元素类型**，否则循环里用它拼接字符串会报 `Cannot infer the type`：

```gdscript
const EXTS: Array[String] = ["ogg", "mp3", "wav"]   # 对
const EXTS := ["ogg", "mp3", "wav"]                 # 错：下游 var p := dir + ext 推断失败，整个脚本编译不过
```

Autoload 脚本编译失败会导致单例加载失败，且报错只在启动时刷一行，容易漏看。
