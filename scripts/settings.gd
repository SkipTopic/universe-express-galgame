extends Node
## 全局设置（Autoload，名字 Settings）
## 只保存玩家偏好，不含任何演出逻辑；改动即时写入 user://settings.json
## 生命周期：随进程常驻

const PATH := "user://settings.json"

## 设置项发生变化（音量滑块、速度滑块等）
signal changed

## 打字速度（字符/秒）
var text_speed: float = 45.0
## 自动播放时每句台词停留的秒数
var auto_delay: float = 1.8
## 快进时遇到"没读过的台词"是否自动停下
var stop_at_unread: bool = true
## 音量 0.0~1.0
var bgm_volume: float = 0.6
var sfx_volume: float = 0.8


func _ready() -> void:
	load_all()


func load_all() -> void:
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not (parsed is Dictionary):
		return
	var d: Dictionary = parsed
	text_speed = float(d.get("text_speed", text_speed))
	auto_delay = float(d.get("auto_delay", auto_delay))
	stop_at_unread = bool(d.get("stop_at_unread", stop_at_unread))
	bgm_volume = float(d.get("bgm_volume", bgm_volume))
	sfx_volume = float(d.get("sfx_volume", sfx_volume))


func save_all() -> void:
	var d := {
		"text_speed": text_speed,
		"auto_delay": auto_delay,
		"stop_at_unread": stop_at_unread,
		"bgm_volume": bgm_volume,
		"sfx_volume": sfx_volume,
	}
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		push_warning("设置写入失败（user:// 不可用？）")
		return
	f.store_string(JSON.stringify(d, "  "))
	f.close()
	changed.emit()


## 恢复默认设置
func reset_all() -> void:
	text_speed = 45.0
	auto_delay = 1.8
	stop_at_unread = true
	bgm_volume = 0.6
	sfx_volume = 0.8
	save_all()
