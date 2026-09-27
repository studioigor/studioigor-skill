# Godot 4 frame capture for studioigor: this is how the agent sees the game without a human.
#
# RUN WITH A WINDOW. With --headless Godot uses the dummy renderer and get_image()
# returns null. The script detects this and exits with code 2.
#
# Copy into the project as tools/capture.gd. Run from the project root
# (a window appears for a few seconds; do not minimize it):
#
#   godot --path . --resolution 1280x720 --fixed-fps 60 --script res://tools/capture.gd -- \
#       --scene res://scenes/gyms/drift_gym.tscn --out .studioigor/captures/drift \
#       --duration 8 --every 1.0 [--start 0.25] [--inputs tools/inputs/drift.json] \
#       [--seed 7] [--cols 4] [--tile 480] [--timeout 120] [--allow-errors] [--require-completed]
#
# Without --scene the project's main_scene is used. Relative paths resolve from the
# project root (res://), so the command can be called from any folder.
#
# Writes to --out: frame_000.png …, sheet.png (contact sheet), metrics.json.
# Old frame_*.png and sheet.png in --out are deleted before capturing.
#
# Exit: 0 — ok; 1 — failure: the scene did not load, no frames, engine or script
# errors (without --allow-errors), completed != true (with --require-completed),
# timeout; 2 — invalid run (headless, arguments, broken input file).
#
# The input schedule is a JSON array; t — seconds of game time since the scene appeared:
#   [{"t": 0.5, "action": "accelerate", "hold": 3.0},   press and release after 3 s
#    {"t": 1.0, "action": "jump"},                      tap (hold defaults to 0.1)
#    {"t": 2.0, "action": "fire", "pressed": true},     press only
#    {"t": 4.0, "action": "fire", "pressed": false},    release only
#    {"t": 5.0, "key": "Space", "hold": 0.2},           key by name (OS.find_keycode_from_string)
#    {"t": 6.0, "click": [640, 360]}]                   left click at window coordinates
#
# Game metrics: if there is an autoload /root/Metrics with a to_dict() method or
# completed / events / score properties, they go into metrics.json under "game".
#
# Determinism: --fixed-fps 60 fixes delta, so game time does not depend on machine
# speed; frames and input are tied to game time. --seed calls seed(); seed the
# game's own RNG singleton at the spot marked ADAPT.
#
# Engine and script errors are caught via Logger (Godot 4.5+). On older versions
# errors_supported in metrics.json is false.
#
# Alternative without the script (deterministic frame sequence + audio):
#   godot --path . res://scenes/x.tscn --write-movie .studioigor/captures/x/frame.png \
#       --fixed-fps 30 --quit-after 240 --resolution 1280x720

extends SceneTree

var scene_path := ""
var out_dir := ".studioigor/captures/capture"
var duration := 8.0
var every := 1.0
var start_at := 0.25
var inputs_path := ""
var cols := 4
var tile_w := 480
var timeout_s := 120.0
var seed_value := -1
var allow_errors := false
var require_completed := false

var _t := 0.0                      # game time since the scene appeared
var _next_shot := 0.0
var _shot_n := 0
var _shots: Array = []             # paths of saved frames
var _thumbs: Array = []            # downscaled copies for the contact sheet
var _pending := ""                 # path of the frame waiting to be drawn
var _pending_age := 0
var _events: Array = []            # expanded input schedule
var _fps: Array = []
var _last_fps_ms := 0
var _wall_start := 0
var _wait_scene := 0
var _finished := false
var _fails: Array = []
var _logger: Object = null


func _initialize() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("capture.gd: started with --headless — the dummy renderer produces no images. " +
			"Remove --headless (a window is required), see references/environment.md.")
		_finished = true
		quit(2)
		return
	if not _parse_args():
		_finished = true
		quit(2)
		return
	_attach_logger()

	out_dir = _abs(out_dir)
	DirAccess.make_dir_recursive_absolute(out_dir)
	_clean_out_dir()

	if scene_path == "":
		scene_path = str(ProjectSettings.get_setting("application/run/main_scene", ""))
	if scene_path == "" or not ResourceLoader.exists(scene_path):
		printerr("capture.gd: scene not found: '%s'" % scene_path)
		_finished = true
		quit(1)
		return

	if inputs_path != "" and not _load_inputs(_abs(inputs_path)):
		_finished = true
		quit(2)
		return

	if seed_value >= 0:
		seed(seed_value)
		# ADAPT: seed the game's RNG here, e.g.: root.get_node("Rng").seed = seed_value

	var err := change_scene_to_file(scene_path)
	if err != OK:
		printerr("capture.gd: failed to load %s (code %d)" % [scene_path, err])
		_finished = true
		quit(1)
		return

	RenderingServer.frame_post_draw.connect(_on_post_draw)
	_wall_start = Time.get_ticks_msec()
	_last_fps_ms = _wall_start
	_next_shot = start_at


func _process(delta: float) -> bool:
	if _finished:
		return false
	var now := Time.get_ticks_msec()
	if (now - _wall_start) / 1000.0 > timeout_s:
		_fails.append("timeout: %.0f s of real time (window minimized or game frozen?)" % timeout_s)
		_finish()
		return false

	if current_scene == null:
		_wait_scene += 1
		if _wait_scene > 600:
			_fails.append("the scene did not appear in the tree within 600 frames")
			_finish()
		return false

	if now - _last_fps_ms >= 1000:
		_fps.append(Engine.get_frames_per_second())
		_last_fps_ms = now

	_t += delta
	while not _events.is_empty() and float(_events[0]["t"]) <= _t:
		_dispatch(_events.pop_front())

	if _pending != "":
		_pending_age += 1
		if _pending_age > 30:
			_fails.append("the frame was not drawn within 30 frames (window minimized or covered?)")
			_pending = ""
	elif _t >= _next_shot and _next_shot <= duration + 0.0001:
		_pending = out_dir.path_join("frame_%03d.png" % _shot_n)
		_pending_age = 0
		_shot_n += 1
		_next_shot += every

	if _t >= duration and _pending == "":
		_finish()
	return false


func _on_post_draw() -> void:
	if _pending == "" or _finished:
		return
	var path := _pending
	_pending = ""
	var img := root.get_texture().get_image()
	if img == null or img.is_empty():
		_fails.append("empty frame: the renderer returned no image (headless or dummy driver?)")
		return
	var err := img.save_png(path)
	if err != OK:
		_fails.append("failed to save %s (code %d)" % [path, err])
		return
	_shots.append(path)
	var th := maxi(1, int(round(tile_w * img.get_height() / float(img.get_width()))))
	var thumb := img.duplicate() as Image
	thumb.convert(Image.FORMAT_RGB8)
	thumb.resize(tile_w, th, Image.INTERPOLATE_BILINEAR)
	_thumbs.append(thumb)


func _finish() -> void:
	if _finished:
		return
	_finished = true
	if RenderingServer.frame_post_draw.is_connected(_on_post_draw):
		RenderingServer.frame_post_draw.disconnect(_on_post_draw)

	var sheet := _make_sheet()
	var game := _game_metrics()
	var errs: Array = []
	var warns: Array = []
	if _logger:
		errs = _logger.get("errors")
		warns = _logger.get("warnings")

	if _shots.is_empty():
		_fails.append("no frames captured")
	if not errs.is_empty() and not allow_errors:
		_fails.append("engine/script errors: %d (first: %s)" % [errs.size(), errs[0]])
	if require_completed and not bool(game.get("completed", false)):
		_fails.append("the game did not set completed = true (Metrics)")

	var samples := _fps.slice(1) if _fps.size() > 1 else _fps
	var fps_mean := 0.0
	for s in samples:
		fps_mean += float(s)
	fps_mean = fps_mean / samples.size() if samples.size() > 0 else 0.0

	var vp := root.get_visible_rect().size
	var metrics := {
		"ok": _fails.is_empty(),
		"engine": "godot " + str(Engine.get_version_info()["string"]),
		"renderer": str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "")),
		"scene": scene_path,
		"viewport": [int(vp.x), int(vp.y)],
		"seed": seed_value,
		"game_time": snappedf(_t, 0.001),
		"wall_time": snappedf((Time.get_ticks_msec() - _wall_start) / 1000.0, 0.01),
		"physics_tps": Engine.physics_ticks_per_second,
		"real_fps_mean": snappedf(fps_mean, 0.1),
		"real_fps_min": samples.min() if samples.size() > 0 else 0,
		"frames": _shots.map(func(p): return p.get_file()),
		"sheet": sheet.get_file(),
		"errors_supported": _logger != null,
		"error_count": errs.size(),
		"warning_count": warns.size(),
		"errors": errs.slice(0, 20),
		"warnings": warns.slice(0, 20),
		"game": game,
		"fail_reasons": _fails,
	}
	var f := FileAccess.open(out_dir.path_join("metrics.json"), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(metrics, "  ") + "\n")
		f.close()

	if _fails.is_empty():
		print("capture ok: %d frames, %s, metrics.json -> %s" % [_shots.size(), sheet.get_file(), out_dir])
		quit(0)
	else:
		for r in _fails:
			printerr("CAPTURE FAILED: " + str(r))
		quit(1)


# ---------------------------------------------------------------- input

func _dispatch(e: Dictionary) -> void:
	var ev: InputEvent
	if e.has("action"):
		var a := InputEventAction.new()
		a.action = e["action"]
		a.pressed = e["pressed"]
		a.strength = 1.0 if e["pressed"] else 0.0
		ev = a
	elif e.has("keycode"):
		var k := InputEventKey.new()
		k.keycode = e["keycode"]
		k.physical_keycode = e["keycode"]
		k.pressed = e["pressed"]
		ev = k
	elif e.has("click"):
		var m := InputEventMouseButton.new()
		m.button_index = MOUSE_BUTTON_LEFT
		m.pressed = e["pressed"]
		m.position = e["click"]
		m.global_position = e["click"]
		ev = m
	if ev:
		Input.parse_input_event(ev)


func _load_inputs(path: String) -> bool:
	var text := FileAccess.get_file_as_string(path)
	var data = JSON.parse_string(text)
	if typeof(data) != TYPE_ARRAY:
		printerr("capture.gd: %s — a JSON array of events is required" % path)
		return false
	for raw in data:
		if typeof(raw) != TYPE_DICTIONARY or not raw.has("t"):
			printerr("capture.gd: event without t: %s" % str(raw))
			return false
		var base := {}
		if raw.has("action"):
			if not InputMap.has_action(raw["action"]):
				printerr("capture.gd: action '%s' is not in the project's InputMap" % raw["action"])
				return false
			base["action"] = StringName(raw["action"])
		elif raw.has("key"):
			var kc := OS.find_keycode_from_string(str(raw["key"]))
			if kc == KEY_NONE:
				printerr("capture.gd: unknown key '%s'" % raw["key"])
				return false
			base["keycode"] = kc
		elif raw.has("click"):
			base["click"] = Vector2(float(raw["click"][0]), float(raw["click"][1]))
		else:
			printerr("capture.gd: an event needs action, key or click: %s" % str(raw))
			return false
		var t := float(raw["t"])
		if raw.has("pressed"):
			_events.append(_merged(base, t, bool(raw["pressed"])))
		else:
			var hold := float(raw.get("hold", 0.1))
			_events.append(_merged(base, t, true))
			_events.append(_merged(base, t + hold, false))
	_events.sort_custom(func(x, y): return float(x["t"]) < float(y["t"]))
	return true


func _merged(base: Dictionary, t: float, pressed: bool) -> Dictionary:
	var d := base.duplicate()
	d["t"] = t
	d["pressed"] = pressed
	return d


# ---------------------------------------------------------------- helpers

func _parse_args() -> bool:
	var args := OS.get_cmdline_user_args()
	var i := 0
	while i < args.size():
		var a: String = args[i]
		var val := ""
		if a.contains("="):
			val = a.get_slice("=", 1)
			a = a.get_slice("=", 0)
		elif i + 1 < args.size() and not args[i + 1].begins_with("--"):
			val = args[i + 1]
			i += 1
		match a:
			"--scene": scene_path = val
			"--out": out_dir = val
			"--duration": duration = float(val)
			"--every": every = maxf(0.02, float(val))
			"--start": start_at = float(val)
			"--inputs": inputs_path = val
			"--cols": cols = maxi(1, int(val))
			"--tile": tile_w = maxi(64, int(val))
			"--timeout": timeout_s = float(val)
			"--seed": seed_value = int(val)
			"--allow-errors": allow_errors = true
			"--require-completed": require_completed = true
			_:
				# Game arguments (--state=…, --overlay) pass through to the game; capture leaves them alone.
				print("capture.gd: argument %s left for the game" % a)
		i += 1
	if duration <= 0.0:
		printerr("capture.gd: --duration must be > 0")
		return false
	return true


func _abs(p: String) -> String:
	if p.begins_with("res://") or p.begins_with("user://"):
		return ProjectSettings.globalize_path(p)
	if p.is_absolute_path():
		return p
	return ProjectSettings.globalize_path("res://").path_join(p)


func _clean_out_dir() -> void:
	var d := DirAccess.open(out_dir)
	if d == null:
		return
	for f in d.get_files():
		if (f.begins_with("frame_") and f.ends_with(".png")) or f == "sheet.png" or f == "metrics.json":
			d.remove(f)


func _make_sheet() -> String:
	if _thumbs.is_empty():
		return ""
	var tw: int = _thumbs[0].get_width()
	var th: int = _thumbs[0].get_height()
	var c := mini(cols, _thumbs.size())
	var rows := ceili(_thumbs.size() / float(c))
	var sheet := Image.create_empty(c * tw, rows * th, false, Image.FORMAT_RGB8)
	sheet.fill(Color(0.06, 0.06, 0.07))
	for i in _thumbs.size():
		var im: Image = _thumbs[i]
		sheet.blit_rect(im, Rect2i(0, 0, tw, th), Vector2i((i % c) * tw, (i / c) * th))
	var path := out_dir.path_join("sheet.png")
	return path if sheet.save_png(path) == OK else ""


func _game_metrics() -> Dictionary:
	var m := root.get_node_or_null("Metrics")
	if m == null:
		return {}
	if m.has_method("to_dict"):
		var d = m.to_dict()
		return d if typeof(d) == TYPE_DICTIONARY else {}
	var out := {}
	for k in ["completed", "events", "score"]:
		if k in m:
			out[k] = m.get(k)
	return out


func _attach_logger() -> void:
	# Logger appeared in Godot 4.5. The script is built on the fly so that capture.gd
	# still parses on older 4.x (errors are simply not counted there).
	if not ClassDB.class_exists("Logger") or not OS.has_method("add_logger"):
		return
	var s := GDScript.new()
	s.source_code = """extends Logger
var errors: Array = []
var warnings: Array = []
var _mx := Mutex.new()
func _log_error(function: String, file: String, line: int, code: String, rationale: String, editor_notify: bool, error_type: int, script_backtraces: Array[ScriptBacktrace]) -> void:
	var where := "%s:%d" % [file.get_file(), line]
	for bt in script_backtraces:
		if bt != null and bt.get_frame_count() > 0:
			where = "%s:%d" % [bt.get_frame_file(0).get_file(), bt.get_frame_line(0)]
			break
	var msg := "%s (%s)" % [rationale if rationale != "" else code, where]
	_mx.lock()
	if error_type == 1:
		warnings.append(msg)
	else:
		errors.append(msg)
	_mx.unlock()
func _log_message(message: String, error: bool) -> void:
	pass
"""
	if s.reload() != OK:
		return
	_logger = s.new()
	OS.call("add_logger", _logger)
