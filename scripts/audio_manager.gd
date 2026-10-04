extends Node
## 跨场景音频服务（Autoload，名字 AudioManager）
## BGM 循环 / SFX 一次性 / 语音；素材放 assets/audio/bgm|sfx|voice
## 目录为空时全部静默跳过，不会报错——接手者丢进音频文件即可生效

const DIR_BGM := "res://assets/audio/bgm/"
const DIR_SFX := "res://assets/audio/sfx/"
const DIR_VOICE := "res://assets/audio/voice/"
## 依次尝试的音频扩展名（必须显式标注元素类型，否则循环里无法推断）
const EXTS: Array[String] = ["ogg", "mp3", "wav"]

var bgm_player: AudioStreamPlayer
var sfx_player: AudioStreamPlayer
var voice_player: AudioStreamPlayer
var _current_bgm: String = ""


func _ready() -> void:
	bgm_player = _make_player("BGM")
	sfx_player = _make_player("SFX")
	voice_player = _make_player("Voice")
	_apply_volumes()
	Settings.changed.connect(_apply_volumes)


func _make_player(pname: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.name = pname
	add_child(p)
	return p


func _apply_volumes() -> void:
	bgm_player.volume_db = linear_to_db(Settings.bgm_volume)
	sfx_player.volume_db = linear_to_db(Settings.sfx_volume)
	voice_player.volume_db = linear_to_db(Settings.sfx_volume)


## 播放背景音乐。value 为文件名（可不带扩展名）；"无" 或空 = 停止
func play_bgm(value: String) -> void:
	if value.is_empty() or value == "无":
		bgm_player.stop()
		_current_bgm = ""
		return
	if value == _current_bgm and bgm_player.playing:
		return
	var path := _resolve(DIR_BGM, value)
	if path.is_empty():
		return
	_current_bgm = value
	bgm_player.stream = load(path) as AudioStream
	bgm_player.play()


func stop_bgm() -> void:
	bgm_player.stop()
	_current_bgm = ""


## 播放音效 / 语音
func play_sfx(value: String) -> void:
	var path := _resolve(DIR_SFX, value)
	if not path.is_empty():
		sfx_player.stream = load(path) as AudioStream
		sfx_player.play()


func play_voice(value: String) -> void:
	var path := _resolve(DIR_VOICE, value)
	if not path.is_empty():
		voice_player.stream = load(path) as AudioStream
		voice_player.play()


## 文件名解析：带扩展名就直接用，否则依次尝试 ogg/mp3/wav
func _resolve(dir: String, value: String) -> String:
	if value.is_empty():
		return ""
	if value.contains("."):
		var direct := dir + value
		return direct if ResourceLoader.exists(direct) else ""
	for ext in EXTS:
		var p: String = dir + value + "." + ext
		if ResourceLoader.exists(p):
			return p
	return ""
