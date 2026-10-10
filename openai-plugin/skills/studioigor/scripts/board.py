#!/usr/bin/env python3
"""Boards for showing options to the user — a local web page with feedback.

A board is how the agent SHOWS options: style directions with references,
asset packs, look-dev or gym screenshots, an engine comparison as cards. The user
still confirms the decision via AskUserQuestion; the board lets them see the
options and leave detailed feedback (like/dislike on each image, comments).

Commands:
  board.py build <board.json>
      Build index.html next to board.json (the data is embedded in the page).

  board.py from-refs --out <boarddir> --title "…" [--subtitle …] [--question …]
                     [--mode single|multi|none] <refdir> [<refdir> …]
      Build board.json + index.html from reference sets: each refdir with its
      sources.json becomes one option.

  board.py serve <boarddir> [--port 8765] [--open] [--until-feedback] [--root DIR]
      Start a local server (127.0.0.1 only). The "Send" button writes
      <boarddir>/feedback.json. With --until-feedback the server prints the feedback
      and exits after the first submission — run it in the background
      (run_in_background), and the agent gets a notification with the feedback.

stdlib only.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import socket
import subprocess
import sys
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MEDIA_VIDEO = {".mp4", ".webm", ".mov", ".m4v"}


# --------------------------------------------------------------------- build

def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"error: {path} — invalid JSON: {e}")
    spec.setdefault("title", "Board")
    spec.setdefault("mode", "single")
    spec.setdefault("options", [])
    for i, o in enumerate(spec["options"]):
        o.setdefault("id", f"opt{i + 1}")
        o.setdefault("title", o["id"])
        o.setdefault("media", o.pop("images", []) if "images" in o else [])
        norm = []
        for m in o["media"]:
            if isinstance(m, str):
                m = {"src": m}
            m.setdefault("caption", "")
            m["kind"] = "video" if Path(m["src"].split("?")[0]).suffix.lower() in MEDIA_VIDEO else "image"
            norm.append(m)
        o["media"] = norm
    return spec


def build(spec_path: Path) -> Path:
    spec = load_spec(spec_path)
    out = spec_path.parent / "index.html"
    data = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE.replace("__TITLE__", html.escape(spec["title"]))
                .replace("__DATA__", data))
    out.write_text(page, encoding="utf-8")
    missing = []
    for o in spec["options"]:
        for m in o["media"]:
            src = m["src"]
            if src.startswith(("http://", "https://", "data:")):
                continue
            if not (spec_path.parent / src).exists():
                missing.append(src)
    n_media = sum(len(o["media"]) for o in spec["options"])
    print(f"board built: {out}  (options: {len(spec['options'])}, media: {n_media})")
    if missing:
        print(f"  WARNING: {len(missing)} files not found, e.g.: {missing[:3]}")
    return out


def from_refs(args) -> Path:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    options = []
    for rd in args.refdirs:
        rd = Path(rd)
        src = rd / "sources.json"
        meta = json.loads(src.read_text(encoding="utf-8")) if src.is_file() else {}
        items = meta.get("items") or [
            {"file": p.name} for p in sorted(rd.iterdir())
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"} | MEDIA_VIDEO]
        media = []
        for it in items:
            f = rd / it["file"]
            if not f.exists():
                continue
            media.append({
                "src": os.path.relpath(f, out),
                "caption": it.get("note") or it.get("title") or "",
                "source": it.get("page") or it.get("url") or "",
                "credit": it.get("credit", ""),
                "license": it.get("license", ""),
                "generated": bool(it.get("generated")),
            })
        options.append({
            "id": rd.name,
            "title": meta.get("title") or rd.name,
            "text": meta.get("text", ""),
            "palette": meta.get("palette", []),
            "tags": meta.get("tags", []),
            "pros": meta.get("pros", []),
            "cons": meta.get("cons", []),
            "media": media,
        })
    spec = {"title": args.title, "subtitle": args.subtitle or "",
            "question": args.question or "", "mode": args.mode, "options": options}
    sp = out / "board.json"
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return build(sp)


# --------------------------------------------------------------------- serve

def find_root(board: Path) -> Path:
    for p in [board, *board.parents]:
        if p.name == ".studioigor":
            return p
        if (p / ".studioigor").is_dir():
            return p / ".studioigor"
    return board.parent


def free_port(preferred: int) -> int:
    for port in [preferred, *range(preferred + 1, preferred + 50)]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 0


def summarize(sub: dict, spec: dict) -> str:
    titles = {o["id"]: o["title"] for o in spec.get("options", [])}
    caps = {m["src"]: (m.get("caption") or "")[:60] for o in spec.get("options", []) for m in o.get("media", [])}

    def label(k: str) -> str:
        return f'{k} "{caps[k]}"' if caps.get(k) else k

    lines = [f"BOARD FEEDBACK \"{spec.get('title', '')}\" — {sub.get('ts', '')}"]
    sel = sub.get("selected") or []
    lines.append("selected: " + (", ".join(f"{s} ({titles.get(s, '?')})" for s in sel) or "nothing"))
    likes = [k for k, v in (sub.get("reactions") or {}).items() if v == "like"]
    dislikes = [k for k, v in (sub.get("reactions") or {}).items() if v == "dislike"]
    if likes:
        lines.append(f"liked ({len(likes)}): " + "; ".join(label(k) for k in likes))
    if dislikes:
        lines.append(f"not it ({len(dislikes)}): " + "; ".join(label(k) for k in dislikes))
    for oid, text in (sub.get("comments") or {}).items():
        if text.strip():
            lines.append(f"comment on {oid} ({titles.get(oid, '?')}): {text.strip()}")
    if (sub.get("comment") or "").strip():
        lines.append(f"general comment: {sub['comment'].strip()}")
    return "\n".join(lines)


def serve(args) -> int:
    board = Path(args.boarddir).resolve()
    if board.is_file():
        board = board.parent
    index = board / "index.html"
    spec_path = board / "board.json"
    if not index.is_file():
        if spec_path.is_file():
            build(spec_path)
        else:
            sys.exit(f"error: no index.html or board.json in {board}")
    spec = load_spec(spec_path) if spec_path.is_file() else {}
    root = Path(args.root).resolve() if args.root else find_root(board)
    try:
        rel = board.relative_to(root)
    except ValueError:
        root, rel = board, Path(".")
    port = free_port(args.port)
    if not port:
        sys.exit("error: no free port")
    done = threading.Event()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)

        def log_message(self, *a):  # keep the log quiet
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_POST(self):
            if self.path.split("?")[0] != "/api/feedback":
                self.send_error(404)
                return
            n = int(self.headers.get("Content-Length") or 0)
            if n > 2_000_000:
                self.send_error(413)
                return
            try:
                sub = json.loads(self.rfile.read(n).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_error(400)
                return
            sub["ts"] = datetime.now().isoformat(timespec="seconds")
            fb = board / "feedback.json"
            try:
                hist = json.loads(fb.read_text(encoding="utf-8")) if fb.is_file() else {}
            except json.JSONDecodeError:
                hist = {}
            hist.setdefault("submissions", []).append(sub)
            hist["latest"] = sub
            fb.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(summarize(sub, spec), flush=True)
            print(f"(full: {fb})", flush=True)
            if args.until_feedback:
                done.set()

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/{rel.as_posix().strip('.').strip('/')}/index.html".replace("//index", "/index")
    print(f"board: {url}", flush=True)
    print("waiting for feedback (the \"Send\" button on the page)…" if args.until_feedback
          else "server is running; Ctrl+C — stop", flush=True)
    if args.open:
        subprocess.run(["open", url], check=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        if args.until_feedback:
            done.wait(timeout=args.timeout or None)
            if not done.is_set():
                print("timeout: no feedback came", flush=True)
                return 3
        else:
            t.join()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
    return 0


# ---------------------------------------------------------------------- page

PAGE = r"""<!doctype html>
<html lang="en" style="color-scheme:dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#111214;--panel:#1a1b1f;--line:#2a2c31;--fg:#e9e9ea;--dim:#9a9ba0;--acc:#e8a33d;--ok:#57c48a;--bad:#ec6a5e;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding-bottom:7rem}
header{padding:2rem 1.25rem 1rem;max-width:88rem;margin:0 auto}
h1{margin:0 0 .3rem;font-size:1.7rem;letter-spacing:-.01em}
.sub{color:var(--dim);margin:0 0 .6rem}
.q{font-size:1.1rem;margin:.6rem 0 0;font-weight:600}
main{max-width:88rem;margin:0 auto;padding:0 1.25rem}
.opt{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.1rem 1.2rem;margin:0 0 1.2rem;transition:border-color .15s}
.opt.sel{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc) inset}
.ohd{display:flex;gap:.8rem;align-items:flex-start;flex-wrap:wrap}
.ohd h2{margin:0;font-size:1.25rem;flex:1 1 20rem}
.pick{border:1px solid var(--line);background:transparent;color:var(--fg);border-radius:999px;padding:.4rem 1rem;font:inherit;cursor:pointer}
.opt.sel .pick{background:var(--acc);border-color:var(--acc);color:#111}
.tags{margin:.35rem 0 0}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:0 .55rem;margin:0 .3rem .3rem 0;font-size:.8rem;color:var(--dim)}
.text{margin:.6rem 0 .2rem;white-space:pre-wrap;max-width:60rem}
.pal{display:flex;gap:.35rem;margin:.6rem 0 1.7rem;flex-wrap:wrap}
.sw{width:3.2rem;height:2.2rem;border-radius:6px;position:relative;border:1px solid var(--line)}
.sw span{position:absolute;bottom:-1.25rem;left:0;font-size:.68rem;color:var(--dim);font-family:ui-monospace,Menlo,monospace}
.pc{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin:.6rem 0;max-width:60rem}
.pc ul{margin:.2rem 0;padding-left:1.1rem}.pc h4{margin:0;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--dim)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.6rem;margin-top:.8rem}
.m{position:relative;border-radius:10px;overflow:hidden;background:#000;border:2px solid transparent;aspect-ratio:16/10}
.m.like{border-color:var(--ok)}.m.dislike{border-color:var(--bad);opacity:.55}
.m img,.m video{width:100%;height:100%;object-fit:cover;display:block;cursor:zoom-in}
.m .bar{position:absolute;left:0;right:0;bottom:0;display:flex;gap:.3rem;padding:.35rem;background:linear-gradient(transparent,rgba(0,0,0,.75))}
.m .bar button{flex:0 0 auto;border:0;border-radius:6px;padding:.2rem .55rem;font:600 .78rem/1.4 inherit;cursor:pointer;background:rgba(255,255,255,.14);color:#fff}
.m.like .b-like{background:var(--ok);color:#06140c}.m.dislike .b-dis{background:var(--bad);color:#1a0503}
.m .cap{flex:1;color:#ddd;font-size:.75rem;align-self:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gen{position:absolute;top:.4rem;left:.4rem;background:rgba(0,0,0,.7);color:#fff;font-size:.7rem;padding:.05rem .45rem;border-radius:4px}
textarea{width:100%;min-height:3.2rem;margin-top:.8rem;background:transparent;color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:.55rem .7rem;font:inherit;resize:vertical}
footer{position:fixed;left:0;right:0;bottom:0;background:var(--panel);border-top:1px solid var(--line);padding:.7rem 1.25rem}
.fin{max-width:88rem;margin:0 auto;display:flex;gap:.8rem;align-items:center;flex-wrap:wrap}
.fin textarea{margin:0;flex:1 1 20rem;min-height:2.6rem}
.send{background:var(--acc);color:#111;border:0;border-radius:10px;padding:.7rem 1.4rem;font:700 1rem inherit;cursor:pointer}
.stat{color:var(--dim);font-size:.85rem}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;flex-direction:column;z-index:10;padding:1rem}
#lb.on{display:flex}#lb img,#lb video{max-width:96vw;max-height:84vh;object-fit:contain}
#lb .meta{color:#ccc;font-size:.85rem;margin-top:.6rem;text-align:center;max-width:70rem}
#lb a{color:var(--acc)}
#ov{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:11;padding:1rem}
#ov.on{display:flex}#ov .box{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.4rem;max-width:44rem;width:100%}
#ov textarea{min-height:12rem;font-family:ui-monospace,Menlo,monospace;font-size:.8rem}
@media (max-width:40rem){.pc{grid-template-columns:1fr}.grid{grid-template-columns:repeat(auto-fill,minmax(10rem,1fr))}}
</style>
</head>
<body>
<header><h1 id="t"></h1><p class="sub" id="s"></p><p class="q" id="qq"></p></header>
<main id="opts"></main>
<footer><div class="fin">
  <textarea id="gc" placeholder="General comment: what to take, what to drop, what's missing…"></textarea>
  <span class="stat" id="stat"></span>
  <button class="send" id="send">Send</button>
</div></footer>
<div id="lb"></div>
<div id="ov"><div class="box" id="ovb"></div></div>
<script type="application/json" id="data">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const KEY = 'studioigor-board:' + location.pathname;
let S = {selected: [], reactions: {}, comments: {}, comment: ''};
try { const v = localStorage.getItem(KEY); if (v) S = Object.assign(S, JSON.parse(v)); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} stat(); };
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.textContent = h; return e; };
document.getElementById('t').textContent = D.title || '';
document.getElementById('s').textContent = D.subtitle || '';
document.getElementById('qq').textContent = D.question || '';
document.title = D.title || 'Board';
const flat = [];
const box = document.getElementById('opts');
(D.options || []).forEach(o => {
  const c = el('section', 'opt'); c.dataset.id = o.id;
  const hd = el('div', 'ohd'); hd.appendChild(el('h2', '', o.title));
  if (D.mode !== 'none') {
    const b = el('button', 'pick', D.mode === 'multi' ? 'Mark' : 'Choose');
    b.onclick = () => {
      if (D.mode === 'multi') S.selected = S.selected.includes(o.id) ? S.selected.filter(x => x !== o.id) : [...S.selected, o.id];
      else S.selected = S.selected.includes(o.id) ? [] : [o.id];
      paint(); save();
    };
    hd.appendChild(b);
  }
  c.appendChild(hd);
  if (o.tags && o.tags.length) { const t = el('div', 'tags'); o.tags.forEach(x => t.appendChild(el('span', 'tag', x))); c.appendChild(t); }
  if (o.text) c.appendChild(el('p', 'text', o.text));
  if (o.palette && o.palette.length) {
    const p = el('div', 'pal');
    o.palette.forEach(h => { const w = el('div', 'sw'); w.style.background = h; w.appendChild(el('span', '', h)); p.appendChild(w); });
    c.appendChild(p);
  }
  if ((o.pros && o.pros.length) || (o.cons && o.cons.length)) {
    const pc = el('div', 'pc');
    [['Pros', o.pros || []], ['Cons', o.cons || []]].forEach(([h, l]) => {
      const d = el('div'); d.appendChild(el('h4', '', h)); const u = el('ul'); l.forEach(x => u.appendChild(el('li', '', x))); d.appendChild(u); pc.appendChild(d);
    });
    c.appendChild(pc);
  }
  if (o.media && o.media.length) {
    const g = el('div', 'grid');
    o.media.forEach(m => {
      const idx = flat.length; flat.push(m);
      const key = m.src;
      const w = el('div', 'm'); w.dataset.key = key;
      const v = m.kind === 'video' ? el('video') : el('img');
      if (m.kind === 'video') { v.muted = true; v.loop = true; v.playsInline = true; v.autoplay = true; }
      else v.loading = 'lazy';
      v.src = m.src; v.alt = m.caption || ''; v.onclick = () => lb(idx);
      w.appendChild(v);
      if (m.generated) w.appendChild(el('span', 'gen', 'generated'));
      const bar = el('div', 'bar');
      const bl = el('button', 'b-like', 'Like'); bl.onclick = () => react(key, 'like');
      const bd = el('button', 'b-dis', 'Not it'); bd.onclick = () => react(key, 'dislike');
      bar.appendChild(bl); bar.appendChild(bd); bar.appendChild(el('span', 'cap', m.caption || ''));
      w.appendChild(bar); g.appendChild(w);
    });
    c.appendChild(g);
  }
  const ta = el('textarea'); ta.placeholder = 'Comment on option "' + o.title + '"';
  ta.value = S.comments[o.id] || ''; ta.oninput = () => { S.comments[o.id] = ta.value; save(); };
  c.appendChild(ta);
  box.appendChild(c);
});
const gc = document.getElementById('gc'); gc.value = S.comment || ''; gc.oninput = () => { S.comment = gc.value; save(); };
function react(k, v) { S.reactions[k] = S.reactions[k] === v ? undefined : v; if (!S.reactions[k]) delete S.reactions[k]; paint(); save(); }
function paint() {
  document.querySelectorAll('.opt').forEach(c => c.classList.toggle('sel', S.selected.includes(c.dataset.id)));
  document.querySelectorAll('.m').forEach(w => { const r = S.reactions[w.dataset.key]; w.classList.toggle('like', r === 'like'); w.classList.toggle('dislike', r === 'dislike'); });
}
function stat() {
  const r = Object.values(S.reactions);
  document.getElementById('stat').textContent = 'Selected: ' + S.selected.length + ' · liked: ' + r.filter(x => x === 'like').length + ' · not it: ' + r.filter(x => x === 'dislike').length;
}
let cur = -1;
function lb(i) {
  cur = i; const m = flat[i]; const L = document.getElementById('lb'); L.innerHTML = '';
  const v = m.kind === 'video' ? el('video') : el('img'); v.src = m.src;
  if (m.kind === 'video') { v.controls = true; v.autoplay = true; v.loop = true; }
  L.appendChild(v);
  const meta = el('div', 'meta');
  meta.appendChild(document.createTextNode([m.caption, m.credit, m.license, m.generated ? 'generated' : ''].filter(Boolean).join(' · ') + ' '));
  if (m.source) { const a = el('a', '', 'source'); a.href = m.source; a.target = '_blank'; a.rel = 'noopener'; meta.appendChild(a); }
  meta.appendChild(el('div', '', '← → browse · Esc close · L like · D not it'));
  L.appendChild(meta); L.classList.add('on');
}
document.getElementById('lb').onclick = e => { if (e.target.id === 'lb') { e.currentTarget.classList.remove('on'); cur = -1; } };
document.addEventListener('keydown', e => {
  if (cur < 0) return;
  if (e.key === 'Escape') { document.getElementById('lb').classList.remove('on'); cur = -1; }
  if (e.key === 'ArrowRight') lb((cur + 1) % flat.length);
  if (e.key === 'ArrowLeft') lb((cur - 1 + flat.length) % flat.length);
  if (e.key === 'l' || e.key === 'L' || e.key === '\u0434') react(flat[cur].src, 'like');
  if (e.key === 'd' || e.key === 'D' || e.key === '\u0432') react(flat[cur].src, 'dislike');
});
function overlay(nodes) { const b = document.getElementById('ovb'); b.innerHTML = ''; nodes.forEach(n => b.appendChild(n)); document.getElementById('ov').classList.add('on'); }
document.getElementById('ov').onclick = e => { if (e.target.id === 'ov') e.currentTarget.classList.remove('on'); };
document.getElementById('send').onclick = async () => {
  const payload = {board: D.title, selected: S.selected, reactions: S.reactions, comments: S.comments, comment: S.comment};
  try {
    const r = await fetch('/api/feedback', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    if (!r.ok) throw new Error(r.status);
    overlay([el('h2', '', 'Sent'), el('p', '', 'The agent got the feedback. You can go back to the terminal.')]);
  } catch (e) {
    const ta = el('textarea'); ta.value = JSON.stringify(payload, null, 2);
    const cp = el('button', 'send', 'Copy'); cp.onclick = () => { ta.select(); try { navigator.clipboard.writeText(ta.value); } catch (x) { document.execCommand('copy'); } cp.textContent = 'Copied'; };
    overlay([el('h2', '', 'The board server is not running'), el('p', '', 'Copy the feedback and paste it into the chat with the agent.'), ta, cp]);
  }
};
paint(); stat();
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="studioigor boards")
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("spec")
    f = sp.add_parser("from-refs")
    f.add_argument("refdirs", nargs="+")
    f.add_argument("--out", required=True)
    f.add_argument("--title", required=True)
    f.add_argument("--subtitle", default="")
    f.add_argument("--question", default="")
    f.add_argument("--mode", default="single", choices=["single", "multi", "none"])
    s = sp.add_parser("serve")
    s.add_argument("boarddir")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--open", action="store_true")
    s.add_argument("--until-feedback", action="store_true")
    s.add_argument("--timeout", type=int, default=0, help="seconds to wait for feedback (0 = no limit)")
    s.add_argument("--root", default="")
    a = ap.parse_args()
    if a.cmd == "build":
        build(Path(a.spec))
    elif a.cmd == "from-refs":
        from_refs(a)
    else:
        return serve(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
