extends Control
## 章节播放器：读取 story/chXX.txt 剧本并演出
## 功能：分支跳转、历史回顾、自动播放、快进(跳过已读)、立绘淡入、BGM/SFX
## 进度保存在 GameManager.current_chapter / current_line（9槽存档 + 自动存档）
## 剧本格式见 story/格式说明.txt（记事本直接改）

const DIR_BG := "res://assets/sprites/bg/"
const DIR_CHAR := "res://assets/sprites/characters/"
const DIR_CG := "res://assets/cg/"
## 立绘/背景淡入时长（秒）
const FADE := 0.25
## 快进时每步的间隔（秒）
const SKIP_INTERVAL := 0.03
## 单次演出中允许的最大跳转次数，防止剧本写成死循环跳转
const MAX_JUMPS := 2000

var steps: Array[Dictionary] = []
## 标签名 → 步骤下标（【标签】/【跳转】用）
var labels: Dictionary = {}
var idx: int = 0            # 当前步骤下标
var line_no: int = 0        # 已播放的台词行数（存档用）
var typing: bool = false
var awaiting_choice: bool = false
var auto_mode: bool = false
var skip_mode: bool = false
var _typed_chars: float = 0.0
var _auto_timer: float = 0.0
var _skip_timer: float = 0.0
## 左右立绘位各自站着的"角色身份"（去掉表情后缀），用于区分"换表情"和"新角色上场"
var _char_base_l: String = ""
var _char_base_r: String = ""
## 已读台词（历史回顾用）
var _history: Array[Dictionary] = []
## 当前选项（含跳转目标）
var _options: Array[Dictionary] = []

@onready var bg: TextureRect = $Bg
@onready var char_l: TextureRect = $CharL
@onready var char_r: TextureRect = $CharR
@onready var cg_rect: TextureRect = $CG
@onready var chapter_label: Label = $ChapterLabel
@onready var name_plate: Panel = $UILayer/VNBox/NamePlate
@onready var name_label: Label = $UILayer/VNBox/NamePlate/NameLabel
@onready var text_label: RichTextLabel = $UILayer/VNBox/Text
@onready var next_arrow: Label = $UILayer/VNBox/NextArrow
@onready var choices: VBoxContainer = $UILayer/Choices
@onready var fade_rect: ColorRect = $FadeRect

@onready var auto_btn: Button = $UILayer/CtrlBar/AutoBtn
@onready var skip_btn: Button = $UILayer/CtrlBar/SkipBtn
@onready var history_btn: Button = $UILayer/CtrlBar/HistoryBtn
@onready var settings_btn: Button = $UILayer/CtrlBar/SettingsBtn
@onready var history_panel: Panel = $UILayer/HistoryPanel
@onready var history_text: RichTextLabel = $UILayer/HistoryPanel/HistoryText
@onready var history_close: Button = $UILayer/HistoryPanel/HistoryClose
@onready var settings_panel: Panel = $UILayer/SettingsPanel
@onready var speed_slider: Slider = $UILayer/SettingsPanel/VBox/RowSpeed/SpeedSlider
@onready var auto_slider: Slider = $UILayer/SettingsPanel/VBox/RowAuto/AutoSlider
@onready var bgm_slider: Slider = $UILayer/SettingsPanel/VBox/RowBgm/BgmSlider
@onready var sfx_slider: Slider = $UILayer/SettingsPanel/VBox/RowSfx/SfxSlider
@onready var settings_close: Button = $UILayer/SettingsPanel/VBox/Buttons/SettingsClose
@onready var settings_reset: Button = $UILayer/SettingsPanel/VBox/Buttons/SettingsReset


func _ready() -> void:
	$UILayer/MenuBtn.pressed.connect(_open_save)
	auto_btn.pressed.connect(_on_auto_pressed)
	skip_btn.pressed.connect(_on_skip_pressed)
	history_btn.pressed.connect(_toggle_history)
	settings_btn.pressed.connect(_toggle_settings)
	history_close.pressed.connect(_close_history)
	settings_close.pressed.connect(_close_settings)
	settings_reset.pressed.connect(_on_settings_reset)
	speed_slider.value_changed.connect(_on_speed_changed)
	auto_slider.value_changed.connect(_on_auto_delay_changed)
	bgm_slider.value_changed.connect(_on_bgm_changed)
	sfx_slider.value_changed.connect(_on_sfx_changed)
	_sync_settings_ui()
	if not _load_chapter(GameManager.current_chapter):
		_next_chapter()


func _open_save() -> void:
	GameManager.open_save_mode = "save"
	get_tree().change_scene_to_file("res://scenes/save_menu.tscn")


## ── 章节装载 ──
func _load_chapter(ch: int) -> bool:
	var path := "res://story/ch%02d.txt" % ch
	if not FileAccess.file_exists(path):
		push_warning("剧本缺失: " + path)
		return false
	steps = StoryParser.parse(path)
	if steps.is_empty():
		push_warning("剧本为空: " + path)
		return false

	_scan_labels()
	idx = 0
	line_no = 0
	chapter_label.text = "第%d章 · %s" % [ch, GameManager.chapter_title(ch)]

	# 读档恢复：快进到存档行号之前（背景/立绘照常应用，台词只计数不显示）
	var target: int = GameManager.current_line
	while idx < steps.size() and line_no < target:
		var st: Dictionary = steps[idx]
		match String(st.get("type", "")):
			"bg":
				_apply_bg(String(st.get("value", "")))
			"sprite":
				_apply_sprite(String(st.get("value", "")))
			"line":
				line_no += 1
		idx += 1
	GameManager.current_line = line_no

	if idx >= steps.size():
		return false
	_advance()
	return true


## 建立 标签名→下标 的映射，供【跳转】与选项分支使用
func _scan_labels() -> void:
	labels.clear()
	for i in steps.size():
		var st: Dictionary = steps[i]
		if String(st.get("type", "")) == "label":
			labels[String(st.get("value", ""))] = i


func _next_chapter() -> void:
	while GameManager.current_chapter < GameManager.LAST_CHAPTER:
		GameManager.current_chapter += 1
		GameManager.current_line = 0
		if _load_chapter(GameManager.current_chapter):
			return
	_return_to_title()


## 切回标题画面。defer 是必须的：本函数可能处在 _ready 的调用栈里，
## 此刻 SceneTree 正在添加/删除子节点，同步切场景会报
## "Parent node is busy adding/removing children" 并静默失败。
func _return_to_title() -> void:
	GameManager.autosave()
	_goto_main.call_deferred()


func _goto_main() -> void:
	get_tree().change_scene_to_file("res://scenes/main.tscn")


## 转场演出：黑场渐入0.35s → 清立绘和CG → 渐出0.35s
## _fading 防重入：黑场期间再点击不会叠加多个转场协程（否则会连环跳句/死等）
var _fading := false

func _do_fade() -> void:
	if _fading:
		return
	_fading = true
	char_l.visible = false
	char_r.visible = false
	_char_base_l = ""
	_char_base_r = ""
	cg_rect.visible = false
	if fade_rect != null and is_instance_valid(fade_rect):
		var tr := create_tween()
		tr.tween_property(fade_rect, "modulate:a", 1.0, 0.35)
		await tr.finished
		var tr2 := create_tween()
		tr2.tween_property(fade_rect, "modulate:a", 0.0, 0.35)
		await tr2.finished
	_fading = false


## ── 推进：自动步骤连续执行，遇到对话 / 选项 / CG 停下等玩家 ──
func _advance() -> void:
	var jump_guard := 0
	while idx < steps.size():
		var st: Dictionary = steps[idx]
		match String(st.get("type", "")):
			"title":
				chapter_label.text = String(st.get("value", ""))
			"bg":
				_apply_bg(String(st.get("value", "")))
			"sprite":
				_apply_sprite(String(st.get("value", "")))
			"cg":
				# CG 是一次点击关闭的展示步骤，停下等待
				if _apply_cg(String(st.get("value", ""))):
					idx += 1
					return
			"fade":
				# 转场：黑场渐入 → 清空立绘/CG → 渐出
				await _do_fade()
			"bgm":
				AudioManager.play_bgm(String(st.get("value", "")))
			"sfx":
				AudioManager.play_sfx(String(st.get("value", "")))
			"label":
				pass  # 标签本身不演出
			"jump":
				jump_guard += 1
				if jump_guard > MAX_JUMPS:
					push_warning("跳转次数异常，疑似循环跳转，已中止本章")
					idx = steps.size()
					continue
				var dest: String = String(st.get("value", ""))
				if labels.has(dest):
					idx = int(labels[dest])
					continue
				push_warning("跳转目标不存在: " + dest)
			"line":
				_show_line(st)
				idx += 1
				return
			"choice":
				_show_choices(st.get("options", []))
				idx += 1
				return
			_:
				push_warning("未知指令类型: %s" % str(st))
		idx += 1
	_next_chapter()


func _show_line(st: Dictionary) -> void:
	var who: String = String(st.get("name", ""))
	var text: String = String(st.get("text", ""))
	name_plate.visible = who != ""
	name_label.text = who
	# 名牌宽度自适应：字数×字号 + 左右留白（28=名牌字号，52=内容边距）
	if who != "":
		var plate: Panel = name_plate
		plate.custom_minimum_size.x = who.length() * 28.0 + 52.0
	text_label.text = text
	text_label.visible_characters = 0
	_typed_chars = 0.0
	typing = true
	next_arrow.visible = false
	_history.append({"name": who, "text": text})
	line_no += 1
	GameManager.current_line = line_no
	GameManager.mark_read(GameManager.current_chapter, line_no)
	GameManager.autosave()


## ── 素材 ──
## 把剧本里的文件名解析成真实存在的资源路径；找不到返回空串
func _resolve(dir: String, file_name: String) -> String:
	var path := dir + file_name
	if ResourceLoader.exists(path):
		return path
	# 容错：剧本里写 .jpg 但实际素材导出成了 .png
	if file_name.get_extension().to_lower() in ["jpg", "jpeg"]:
		var alt := dir + file_name.get_basename() + ".png"
		if ResourceLoader.exists(alt):
			return alt
	push_warning("素材缺失: " + path)
	return ""


func _fade_in(target: CanvasItem) -> void:
	target.modulate.a = 0.0
	var tw: Tween = create_tween()
	tw.tween_property(target, "modulate:a", 1.0, FADE)


func _apply_bg(value: String) -> void:
	var path := _resolve(DIR_BG, value + ".png")
	if not path.is_empty():
		bg.texture = load(path) as Texture2D
		_fade_in(bg)


## 取立绘名的"角色身份"：char_xilang_angry -> char_xilang（表情差分不影响身份）
func _sprite_base(value: String) -> String:
	for suf in ["_normal", "_smile", "_angry", "_sad", "_shock"]:
		if value.ends_with(suf):
			return value.trim_suffix(suf)
	return value

func _apply_sprite(value: String) -> void:
	if value == "无":
		char_l.visible = false
		char_r.visible = false
		_char_base_l = ""
		_char_base_r = ""
		return
	var path := _resolve(DIR_CHAR, value + ".png")
	if path.is_empty():
		return
	var tex := load(path) as Texture2D
	var base := _sprite_base(value)
	# 同一角色换表情（同贴图或差分）：只换脸，绝不换边——否则会左右站出两个自己
	if _char_base_r == base:
		if char_r.texture != tex:
			char_r.texture = tex
		_fade_in(char_r)
		return
	if _char_base_l == base:
		if char_l.texture != tex:
			char_l.texture = tex
		_fade_in(char_l)
		return
	# 新说话的角色站右侧，上一个挪到左侧
	if char_r.visible:
		char_l.texture = char_r.texture
		_char_base_l = _char_base_r
		char_l.visible = true
	char_r.texture = tex
	_char_base_r = base
	char_r.visible = true
	_fade_in(char_r)


func _apply_cg(value: String) -> bool:
	var path := _resolve(DIR_CG, value)
	if path.is_empty():
		return false
	cg_rect.texture = load(path) as Texture2D
	cg_rect.visible = true
	return true


## ── 每帧：打字机 / 自动播放 / 快进 ──
func _process(delta: float) -> void:
	if skip_mode:
		_skip_timer += delta
		if _skip_timer >= SKIP_INTERVAL:
			_skip_timer = 0.0
			_skip_step()
		return
	if typing:
		_typed_chars += delta * Settings.text_speed
		text_label.visible_characters = int(_typed_chars)
		if text_label.visible_characters >= text_label.get_total_character_count():
			_finish_typing()
		return
	if auto_mode and not awaiting_choice and not cg_rect.visible:
		_auto_timer += delta
		if _auto_timer >= Settings.auto_delay:
			_auto_timer = 0.0
			_advance()


func _finish_typing() -> void:
	text_label.visible_characters = -1
	typing = false
	next_arrow.visible = true


## 快进：一路推到"没读过的内容"为止
func _skip_step() -> void:
	if awaiting_choice:
		_set_skip(false)
		return
	if cg_rect.visible:
		cg_rect.visible = false
	_advance()
	if typing:
		_finish_typing()
	if Settings.stop_at_unread and not GameManager.is_read(GameManager.current_chapter, line_no):
		_set_skip(false)


## ── 输入：点击 / 触屏 / 回车推进 ──
func _unhandled_input(event: InputEvent) -> void:
	if settings_panel.visible or history_panel.visible or _fading:
		return
	if awaiting_choice or not _is_confirm(event):
		return
	# 正片播放中点一下 = 退出自动/快进
	if auto_mode or skip_mode:
		_set_auto(false)
		_set_skip(false)
		return
	if cg_rect.visible:
		cg_rect.visible = false
		_advance()
	elif typing:
		_finish_typing()
	else:
		_advance()


func _is_confirm(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		# 手机上一次触摸会同时产生"触摸+模拟鼠标"两个事件：
		# 若都处理，一次点击=瞬间补完当前句+跳下一句，打字机效果永远看不见。
		# 因此移动端只认触摸事件。
		if OS.has_feature("mobile"):
			return false
		return event.button_index == MOUSE_BUTTON_LEFT and event.pressed
	if event is InputEventScreenTouch:
		return event.pressed
	return event.is_action_pressed("ui_accept")


## ── 选项：场景里预置4个按钮，用到几个显示几个 ──
func _show_choices(options: Array) -> void:
	_options.clear()
	for o in options:
		if o is Dictionary:
			_options.append(o)
		else:
			_options.append({"text": String(o), "target": ""})
	awaiting_choice = true
	for i in range(1, 5):
		var btn: Button = choices.get_node("Choice%d" % i)
		btn.visible = i <= _options.size()
		if i <= _options.size():
			btn.text = String(_options[i - 1].get("text", ""))
			for conn in btn.pressed.get_connections():
				btn.pressed.disconnect(conn["callable"])
			btn.pressed.connect(_on_choice.bind(i))
	choices.visible = true


func _on_choice(chosen: int) -> void:
	choices.visible = false
	awaiting_choice = false
	GameManager.choice_history.append(chosen)
	var target: String = ""
	if chosen - 1 < _options.size():
		target = String(_options[chosen - 1].get("target", ""))
	if not target.is_empty():
		if labels.has(target):
			idx = int(labels[target])
		else:
			push_warning("选项跳转目标不存在: " + target)
	_advance()


## ── 控制条 ──
func _on_auto_pressed() -> void:
	_set_auto(not auto_mode)


func _on_skip_pressed() -> void:
	_set_skip(not skip_mode)


func _set_auto(on: bool) -> void:
	auto_mode = on
	auto_btn.text = "■ 停止" if on else "▶ 自动"
	_auto_timer = 0.0
	if on:
		_set_skip(false)


func _set_skip(on: bool) -> void:
	skip_mode = on
	skip_btn.text = "■ 停止" if on else "▶▶ 快进"
	_skip_timer = 0.0
	if on:
		_set_auto(false)


## ── 历史回顾 ──
func _toggle_history() -> void:
	history_panel.visible = not history_panel.visible
	if history_panel.visible:
		_set_auto(false)
		_refresh_history()


func _close_history() -> void:
	history_panel.visible = false


func _refresh_history() -> void:
	var bb := ""
	for h in _history:
		var who: String = _escape_bbcode(String(h.get("name", "")))
		var txt: String = _escape_bbcode(String(h.get("text", "")))
		if who.is_empty():
			bb += "[color=#9a9488]%s[/color]\n\n" % txt
		else:
			bb += "[color=#d9c08a]%s[/color]：%s\n\n" % [who, txt]
	history_text.text = bb
	history_text.scroll_to_line(history_text.get_line_count() - 1)


## 台词里若含 [] 会被当成 BBCode 标签，这里转义掉
func _escape_bbcode(s: String) -> String:
	return s.replace("[", "[lb]").replace("]", "[rb]")


## ── 设置面板 ──
func _toggle_settings() -> void:
	settings_panel.visible = not settings_panel.visible
	if settings_panel.visible:
		_set_auto(false)
		_sync_settings_ui()


func _close_settings() -> void:
	settings_panel.visible = false


func _sync_settings_ui() -> void:
	speed_slider.value = Settings.text_speed
	auto_slider.value = Settings.auto_delay
	bgm_slider.value = Settings.bgm_volume
	sfx_slider.value = Settings.sfx_volume


func _on_speed_changed(v: float) -> void:
	Settings.text_speed = v
	Settings.save_all()


func _on_auto_delay_changed(v: float) -> void:
	Settings.auto_delay = v
	Settings.save_all()


func _on_bgm_changed(v: float) -> void:
	Settings.bgm_volume = v
	Settings.save_all()


func _on_sfx_changed(v: float) -> void:
	Settings.sfx_volume = v
	Settings.save_all()


func _on_settings_reset() -> void:
	Settings.reset_all()
	_sync_settings_ui()
