#!/usr/bin/env python3
"""References for the style board: download images into a set and write sources.json.

A set is a folder `.studioigor/refs/<set>/` (one style direction or one theme).
Every download command appends to `<set>/sources.json` (creates it if missing),
drops duplicates by sha1 and by URL, skips non-images (by byte signature),
downscales to 1600 px on the long side (`sips -Z`, else `magick`) and records w/h.
`board.py from-refs` then builds a board from the sets.

Commands:
  steam "<game or appid>" --out DIR [--n 8] [--trailer K]
      Steam screenshots (storesearch → appdetails); --trailer K — plus K trailer frames
  openverse "<query>" --out DIR [--n 8] [--license-type all|commercial] [--category …]
      CC images (photos, illustrations); without a key: 20 requests/min, 200/day
  wikimedia "<query>" --out DIR [--n 8]
      Wikimedia Commons: architecture, museums, photos, other media; license on each
  artstation "<query>" --out DIR [--n 8]
      concept art (square covers ~600 px); if blocked, says what to use instead
  arena "<query or channel slug>" --out DIR [--n 8] [--channel]
      ready-made Are.na moodboards (channels by aesthetic)
  urls <file|-> --out DIR
      lines `URL [| page | credit | license | note]`; a page URL → takes its og:image
  youtube "<url or search query>" --out DIR [--frames 6] [--at 1:20,3:05]
      video frames via yt-dlp -g + ffmpeg -ss, without downloading the whole video
  add DIR <file>… [--generated] [--prompt …] [--note …] [--credit …]
      add local files (generated concepts, user screenshots)
  meta DIR [--title …] [--text …] [--tags a,b] [--pros "a; b"] [--cons "…"] [--palette "#hex,…"]
  note DIR <file|prefix> "<what we take from it>"
  drop DIR <file|prefix>…          remove junk (and never download it again)
  palette DIR [--n 6] [--liked boards/<board>/feedback.json] [--no-accent]
      palette via ImageMagick from the set's images or from the board's likes
  lospec <slug> --out DIR           palette from Lospec (pixel art)

The images are a private moodboard: not for the build, not for publishing (they are in .gitignore).
stdlib only; external: sips, magick, yt-dlp, ffmpeg — if present.
"""
from __future__ import annotations

import argparse
import colorsys
import fcntl
import hashlib
import html
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = os.environ.get("STUDIOIGOR_UA") or \
    "studioigor-refs/1.0 (personal game-dev moodboard; low volume; python-urllib)"
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
              "(KHTML, like Gecko) Version/18.0 Safari/605.1.15 studioigor-refs/1.0")
MAX_SIDE = 1600
MAX_BYTES = 25_000_000
TIMEOUT = 25
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MOODBOARD = "moodboard only"


class FetchError(Exception):
    pass


class RateLimited(FetchError):
    def __init__(self, host: str, wait: int):
        super().__init__(f"rate limit on {host}, retry in {wait} s")
        self.host, self.wait = host, wait


# ----------------------------------------------------------------- network

def _lock_path(key: str) -> Path:
    return Path(tempfile.gettempdir()) / f"studioigor-{hashlib.sha1(key.encode()).hexdigest()[:12]}.lock"


def throttle(name: str, limit: int, window: float) -> None:
    """Machine-wide request counter (parallel subagents are counted too)."""
    state = Path(tempfile.gettempdir()) / f"studioigor-throttle-{name}.json"
    with open(_lock_path("throttle-" + name), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            stamps = json.loads(state.read_text())
        except (OSError, ValueError):
            stamps = []
        now = time.time()
        stamps = [t for t in stamps if now - t < window]
        if len(stamps) >= limit:
            wait = window - (now - stamps[0]) + 0.5
            print(f"  {name}: local limit {limit}/{int(window)} s — waiting {wait:.0f} s…", flush=True)
            time.sleep(wait)
            now = time.time()
            stamps = [t for t in stamps if now - t < window]
        stamps.append(now)
        state.write_text(json.dumps(stamps))


def http_get(url: str, *, max_bytes: int = MAX_BYTES, timeout: int = TIMEOUT,
             headers: dict | None = None, tries: int = 2) -> tuple[bytes, dict, str]:
    host = urllib.parse.urlsplit(url).hostname or url
    ua, last = UA, None
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                cl = r.headers.get("Content-Length")
                if cl and cl.isdigit() and int(cl) > max_bytes:
                    raise FetchError(f"file too large ({int(cl) // 1_000_000} MB)")
                data = r.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise FetchError("file too large")
                return data, {k.lower(): v for k, v in r.headers.items()}, r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                ra = e.headers.get("Retry-After", "")
                wait = int(ra) if ra.isdigit() else 30
                if attempt + 1 < tries and wait <= 65:
                    print(f"  {host}: rate limited, waiting {wait} s…", flush=True)
                    time.sleep(wait)
                    continue
                raise RateLimited(host, wait)
            if e.code == 403 and ua == UA and attempt + 1 < tries:
                ua = BROWSER_UA  # some CDNs block a non-standard UA
                continue
            raise FetchError(f"HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as e:
            last = e
            time.sleep(1.5)
    raise FetchError(f"network: {getattr(last, 'reason', last)}")


def get_json(url: str, **kw):
    data, hdr, _ = http_get(url, **kw)
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise FetchError(f"not JSON (content-type {hdr.get('content-type', '?')})")


# ----------------------------------------------------------------- images

def sniff(b: bytes) -> str | None:
    if b[:3] == b"\xff\xd8\xff":
        return "jpg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp"
    if b[4:8] == b"ftyp" and b[8:12] in (b"avif", b"avis", b"heic", b"heix", b"mif1"):
        return "avif"
    return None


def img_size(p: Path) -> tuple[int, int]:
    b = p.read_bytes()
    be = lambda s: int.from_bytes(s, "big")
    le = lambda s: int.from_bytes(s, "little")
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return be(b[16:20]), be(b[20:24])
        if b[:6] in (b"GIF87a", b"GIF89a"):
            return le(b[6:8]), le(b[8:10])
        if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
            ch = b[12:16]
            if ch == b"VP8 ":
                return le(b[26:28]) & 0x3FFF, le(b[28:30]) & 0x3FFF
            if ch == b"VP8L":
                bits = le(b[21:25])
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if ch == b"VP8X":
                return 1 + le(b[24:27]), 1 + le(b[27:30])
        if b[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(b):
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m == 0xFF:
                    i += 1
                    continue
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    i += 2
                    continue
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    return be(b[i + 7:i + 9]), be(b[i + 5:i + 7])
                i += 2 + be(b[i + 2:i + 4])
    except IndexError:
        pass
    if shutil.which("sips"):
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(p)],
                             capture_output=True, text=True).stdout
        w = re.search(r"pixelWidth:\s*(\d+)", out)
        h = re.search(r"pixelHeight:\s*(\d+)", out)
        if w and h:
            return int(w.group(1)), int(h.group(1))
    return 0, 0


def _run(cmd: list[str], timeout: int = 120) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def to_jpeg(p: Path, max_side: int | None) -> Path:
    q = p.with_suffix(".jpg")
    if shutil.which("sips"):
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88"]
        if max_side:
            cmd += ["-Z", str(max_side)]
        ok = _run(cmd + [str(p), "--out", str(q)])
    elif shutil.which("magick"):
        cmd = ["magick", f"{p}[0]"] + (["-resize", f"{max_side}x{max_side}>"] if max_side else [])
        ok = _run(cmd + ["-quality", "88", str(q)])
    else:
        ok = False
    if ok and q.is_file() and q.stat().st_size > 0:
        if q != p:
            p.unlink(missing_ok=True)
        return q
    return p


def normalize(p: Path, kind: str) -> tuple[Path, int, int]:
    """Downscale to MAX_SIDE; exotic formats (avif/heic, large webp) → jpeg."""
    w, h = img_size(p)
    big = max(w, h) > MAX_SIDE
    if kind == "avif" or (kind == "webp" and big):
        p = to_jpeg(p, MAX_SIDE)
    elif kind in ("jpg", "png") and big:
        if shutil.which("sips"):
            _run(["sips", "-Z", str(MAX_SIDE), str(p)])
        elif shutil.which("magick"):
            _run(["magick", str(p), "-resize", f"{MAX_SIDE}x{MAX_SIDE}>", str(p)])
        if kind == "png" and p.stat().st_size > 3_000_000:  # a photo saved as PNG → jpeg; pixel art is small
            p = to_jpeg(p, None)
    w, h = img_size(p)
    return p, w, h


# ----------------------------------------------------------------- set

class RefSet:
    def __init__(self, d: str | Path, create: bool = True):
        self.dir = Path(d).expanduser()
        if create:
            self.dir.mkdir(parents=True, exist_ok=True)
        elif not self.dir.is_dir():
            sys.exit(f"error: no set folder {self.dir}")
        self.path = self.dir / "sources.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.is_file():
            try:
                d = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                sys.exit(f"error: {self.path} — invalid JSON: {e}")
        else:
            d = {}
        for k, v in (("title", ""), ("text", ""), ("palette", []), ("tags", []), ("items", [])):
            d.setdefault(k, v)
        return d

    def known(self) -> tuple[set, set]:
        urls, shas = set(), set()
        for it in self.data["items"] + self.data.get("dropped", []):
            if it.get("url"):
                urls.add(it["url"])
            if it.get("sha1"):
                shas.add(it["sha1"])
        return urls, shas

    def save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def update(self, fn) -> None:
        """Re-read → modify → save under a lock (parallel runs into the same set)."""
        with open(_lock_path(str(self.path.resolve())), "w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            self.data = self._load()
            fn(self.data)
            self.save()

    def commit(self, new: list[dict]) -> list[dict]:
        kept: list[dict] = []

        def add(d):
            urls, shas = self.known()
            for it in new:
                if it["sha1"] in shas or (it.get("url") and it["url"] in urls):
                    (self.dir / it["file"]).unlink(missing_ok=True)
                    continue
                d["items"].append(it)
                shas.add(it["sha1"])
                kept.append(it)
        self.update(add)
        return kept

    def present(self) -> list[dict]:
        return [it for it in self.data["items"] if (self.dir / it.get("file", "")).is_file()]

    def find(self, key: str) -> dict:
        items = self.data["items"]
        exact = [it for it in items if it.get("file") == key or it.get("file") == Path(key).name]
        if exact:
            return exact[0]
        pre = [it for it in items if it.get("file", "").startswith(key)] or \
              [it for it in items if key in it.get("file", "")]
        if len(pre) == 1:
            return pre[0]
        sys.exit(f"error: '{key}' — {'not found' if not pre else f'ambiguous ({len(pre)} files)'} in {self.path}")


def rel(p: Path) -> str:
    try:
        return os.path.relpath(p)
    except ValueError:
        return str(p)


def store_bytes(rs: RefSet, data: bytes, stem: str | None, api: str) -> tuple[Path, int, int, str] | None:
    kind = sniff(data)
    if not kind:
        return None
    sha = hashlib.sha1(data).hexdigest()
    p = rs.dir / f"{stem or f'{api}-{sha[:8]}'}.{kind}"
    p.write_bytes(data)
    p, w, h = normalize(p, kind)
    return p, w, h, sha


def item(p: Path, w: int, h: int, sha: str, api: str, query: str, c: dict) -> dict:
    it = {"file": p.name, "url": c.get("url", ""), "page": c.get("page", ""),
          "title": html.unescape(c.get("title") or ""), "credit": html.unescape(c.get("credit") or ""),
          "license": c.get("license", ""), "api": api, "query": query,
          "generated": bool(c.get("generated")), "note": c.get("note", ""),
          "w": w, "h": h, "sha1": sha}
    for k in ("source", "attribution", "prompt", "t"):
        if c.get(k) not in (None, ""):
            it[k] = c[k]
    return it


def download_all(rs: RefSet, cands: list[dict], n: int, api: str, query: str,
                 pre_fetch=None) -> tuple[list[dict], dict]:
    """Download up to n images from the candidates (url + alt URLs in case of failure)."""
    urls, shas = rs.known()
    new, st = [], {"dup": 0, "bad": 0, "err": 0, "why": []}
    for c in cands:
        if len(new) >= n:
            break
        if c["url"] in urls:
            st["dup"] += 1
            continue
        got = None
        for u in [c["url"], *c.get("alt", [])]:
            if not u:
                continue
            try:
                if pre_fetch:
                    pre_fetch(u)
                data, _, _ = http_get(u)
            except RateLimited as e:
                st["why"].append(str(e))
                return new, st
            except FetchError as e:
                st["why"].append(f"{u[:70]}: {e}")
                continue
            if not sniff(data):
                st["why"].append(f"{u[:70]}: not an image")
                continue
            got = data
            break
        if got is None:
            st["err"] += 1
            continue
        sha = hashlib.sha1(got).hexdigest()
        if sha in shas:
            st["dup"] += 1
            continue
        stored = store_bytes(rs, got, None, api)
        if not stored:
            st["bad"] += 1
            continue
        p, w, h, sha = stored
        new.append(item(p, w, h, sha, api, query, c))
        shas.add(sha)
        urls.add(c["url"])
        time.sleep(0.15)
    return new, st


def report(label: str, rs: RefSet, kept: list[dict], st: dict | None = None) -> int:
    total = len(rs.present())
    extra = ""
    if st:
        names = {"dup": "duplicates", "bad": "non-images", "err": "errors"}
        bits = [f"{names[k]} {st[k]}" for k in ("dup", "bad", "err") if st.get(k)]
        extra = ("; skipped: " + ", ".join(bits)) if bits else ""
    print(f"{label}: +{len(kept)} → {rel(rs.dir)} ({total} in set){extra}")
    for it in kept:
        print(f"  {it['file']}  {it['w']}×{it['h']}  {(it.get('title') or '')[:70]}")
    if st and st.get("why") and not kept:
        for w in st["why"][:3]:
            print(f"  reason: {w}")
    if not kept:
        print("  nothing new: everything is already in the set" if st and st.get("dup") and not st.get("err")
              else "  nothing added — refine the query or try another source")
    return 0 if kept or (st and st.get("dup")) else 1


# ----------------------------------------------------------------- sources

def norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def cmd_steam(a) -> int:
    rs = RefSet(a.out)
    term = a.game.strip()
    if term.isdigit():
        appid, name = int(term), ""
    else:
        q = urllib.parse.urlencode({"term": term, "l": "english", "cc": "us"})
        try:
            d = get_json(f"https://store.steampowered.com/api/storesearch/?{q}")
        except FetchError as e:
            print(f"Steam: search failed ({e})")
            return 1
        apps = [i for i in d.get("items", []) if i.get("type") == "app"]
        if not apps:
            print(f"Steam: \"{term}\" not found. Give the English title or the appid: refs.py steam 367520 --out …")
            return 1
        exact = [i for i in apps if norm_name(i["name"]) == norm_name(term)]
        pick = exact[0] if exact else apps[0]
        appid, name = pick["id"], pick["name"]
        if not exact and len(apps) > 1:
            print("  no exact match; others: " + "; ".join(f"{i['name']} ({i['id']})" for i in apps[1:5]))
    try:
        det = get_json(f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us")
    except FetchError as e:
        print(f"Steam: appdetails {appid} failed ({e})")
        return 1
    data = {}
    for v in det.values():  # the response key is sometimes a different appid — match by steam_appid
        if v.get("success") and v.get("data"):
            data = v["data"]
            if data.get("steam_appid") == appid:
                break
    if not data:
        print(f"Steam: no data for appid {appid} (region lock or removed)")
        return 1
    name = data.get("name") or name
    dev = ", ".join(data.get("developers") or []) or name
    page = f"https://store.steampowered.com/app/{appid}/"
    shots = data.get("screenshots") or []
    cands = [{"url": s["path_full"], "alt": [s.get("path_thumbnail", "")], "page": page,
              "title": f"{name} — screenshot {i + 1}", "credit": dev,
              "license": f"© {dev} — {MOODBOARD}"} for i, s in enumerate(shots)]
    new, st = download_all(rs, cands, a.n, "steam", name)
    kept = rs.commit(new)
    code = report(f"steam \"{name}\" (appid {appid}, {len(shots)} screenshots)", rs, kept, st)
    if a.trailer:
        movies = [m for m in data.get("movies") or [] if m.get("hls_h264")]
        if not movies:
            print("  no HLS trailers")
        else:
            m = movies[0]
            meta = {"page": page, "url": m["hls_h264"] + "#t={t}", "credit": dev,
                    "license": f"© {dev} — {MOODBOARD}", "title": f"{name} — trailer"}
            k = video_frames(rs, m["hls_h264"], None, a.trailer, None, "steam", name,
                             f"steamtr-{appid}", meta)
            code = min(code, k)
    return code


def cc_license(r: dict) -> str:
    lic, ver = (r.get("license") or "").lower(), r.get("license_version") or ""
    if lic == "cc0":
        return "CC0"
    if lic == "pdm":
        return "Public Domain Mark"
    return f"CC {lic.upper()} {ver}".strip()


def cmd_openverse(a) -> int:
    rs = RefSet(a.out)
    p = {"q": a.query, "page_size": min(20, max(a.n * 2, 10)), "mature": "false"}
    if a.license_type == "commercial":
        p["license_type"] = "commercial"
    if a.category:
        p["category"] = a.category
    throttle("openverse", 18, 60)
    try:
        d = get_json("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(p))
    except RateLimited as e:
        print(f"openverse: keyless limit (20 requests/min, 200/day) — retry in ~{e.wait} s. "
              f"Meanwhile use wikimedia / arena / urls.")
        return 1
    except FetchError as e:
        print(f"openverse: request failed ({e})")
        return 1
    res = d.get("results") or []
    cands = []
    for r in res:
        if (r.get("filetype") or "").lower() in ("svg", "tif", "tiff"):
            order = [r.get("thumbnail", "")]
        else:
            order = [r.get("url", ""), r.get("thumbnail", "")]
        cands.append({"url": order[0], "alt": order[1:], "page": r.get("foreign_landing_url", ""),
                      "title": r.get("title") or "", "credit": r.get("creator") or r.get("source", ""),
                      "license": cc_license(r), "attribution": r.get("attribution", ""),
                      "source": r.get("source", "")})

    def pre(u):
        if "api.openverse.org" in u:
            throttle("openverse", 18, 60)
    new, st = download_all(rs, cands, a.n, "openverse", a.query, pre_fetch=pre)
    kept = rs.commit(new)
    return report(f"openverse \"{a.query}\" ({d.get('result_count', len(res))} found)", rs, kept, st)


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def cmd_wikimedia(a) -> int:
    rs = RefSet(a.out)
    p = {"action": "query", "format": "json", "formatversion": "2", "generator": "search",
         "gsrsearch": f"filetype:bitmap {a.query}", "gsrnamespace": "6", "gsrlimit": str(min(50, a.n * 3)),
         "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": "1280",
         "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName"}
    try:
        d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p))
    except FetchError as e:
        print(f"wikimedia: request failed ({e})")
        return 1
    pages = sorted((d.get("query") or {}).get("pages") or [], key=lambda x: x.get("index", 0))
    cands = []
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        if not ii.get("url"):
            continue
        em = ii.get("extmetadata") or {}
        val = lambda k: strip_tags((em.get(k) or {}).get("value", ""))
        name = val("ObjectName") or re.sub(r"\.\w+$", "", pg.get("title", "").replace("File:", ""))
        small = ii.get("width", 0) <= 1600 and ii.get("mime") in ("image/jpeg", "image/png", "image/gif", "image/webp")
        cands.append({"url": ii.get("thumburl") or ii["url"], "alt": [ii["url"]] if small else [],
                      "page": ii.get("descriptionurl", ""), "title": name,
                      "credit": val("Artist")[:120], "license": val("LicenseShortName") or "see the page"})
    new, st = download_all(rs, cands, a.n, "wikimedia", a.query)
    kept = rs.commit(new)
    return report(f"wikimedia \"{a.query}\" ({len(pages)} found)", rs, kept, st)


def cmd_artstation(a) -> int:
    rs = RefSet(a.out)
    q = urllib.parse.urlencode({"query": a.query, "page": 1, "per_page": min(50, a.n * 2)})
    fallback = (f"ArtStation is not reachable by script right now. Instead: "
                f"refs.py arena \"{a.query}\" --out {a.out}  or find works via WebSearch and "
                f"download the direct image URLs: refs.py urls <file> --out {a.out}")
    try:
        d = get_json(f"https://www.artstation.com/api/v2/search/projects.json?{q}")
    except FetchError as e:
        print(f"artstation: {e}. {fallback}")
        return 2
    rows = d.get("data") if isinstance(d, dict) else None
    if rows is None:
        print(f"artstation: the response format has changed. {fallback}")
        return 2
    cands = []
    for x in rows:
        if x.get("hide_as_adult") or x.get("is_adult_content"):
            continue
        cov = x.get("smaller_square_cover_url") or ""
        if "/smaller_square/" not in cov:
            continue
        u = x.get("user") or {}
        cands.append({"url": cov.replace("/smaller_square/", "/original/"),
                      "alt": [cov.replace("/smaller_square/", "/large/")],
                      "page": x.get("url", ""), "title": x.get("title", ""),
                      "credit": u.get("full_name") or u.get("username", ""),
                      "license": f"© the author — {MOODBOARD}"})
    new, st = download_all(rs, cands, a.n, "artstation", a.query)
    kept = rs.commit(new)
    code = report(f"artstation \"{a.query}\" ({d.get('total_count', len(rows))} found; covers are square)",
                  rs, kept, st)
    if not kept and not st.get("dup"):
        print(f"  {fallback}")
    return code


SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")
JUNK_TITLE = re.compile(r"\.(jpe?g|png|webp|gif|avif)\b|^[\w.-]{24,}$|^https?://", re.I)


def clean_title(t: str, fallback: str) -> str:
    """Are.na often names a block after its file name — that is not a caption."""
    t = (t or "").strip()
    return fallback if not t or JUNK_TITLE.search(t) else t


def arena_contents(slug: str, per: int = 100) -> list[dict]:
    """Channel images: v2 (has large 1800px), on failure — v3."""
    out = []
    try:
        d = get_json(f"https://api.are.na/v2/channels/{slug}/contents?per={per}")
        for b in d.get("contents") or []:
            im = b.get("image") or {}
            if b.get("class") != "Image" or not im:
                continue
            u = lambda k: (im.get(k) or {}).get("url", "")
            out.append({"url": u("large") or u("display") or u("original"),
                        "alt": [x for x in (u("display"), u("original")) if x],
                        "page": f"https://www.are.na/block/{b['id']}",
                        "title": clean_title(b.get("title") or b.get("generated_title"), f"Are.na/{slug}"),
                        "credit": ((b.get("user") or {}).get("full_name") or "") + f" · Are.na/{slug}",
                        "source": (b.get("source") or {}).get("url", "") if isinstance(b.get("source"), dict) else ""})
        return out
    except FetchError:
        pass
    d = get_json(f"https://api.are.na/v3/channels/{slug}/contents?per={min(per, 100)}")
    for b in d.get("data") or []:
        im = b.get("image") or {}
        if b.get("type") != "Image" or not im.get("src"):
            continue
        large = (im.get("large") or {}).get("src", "")
        out.append({"url": large or im["src"], "alt": [im["src"]] if large else [],
                    "page": f"https://www.are.na/block/{b['id']}",
                    "title": clean_title(b.get("title"), f"Are.na/{slug}"),
                    "credit": ((b.get("user") or {}).get("name") or "") + f" · Are.na/{slug}"})
    return out


def cmd_arena(a) -> int:
    rs = RefSet(a.out)
    arg = a.query.strip()
    lic = f"unknown (repost) — {MOODBOARD}"
    cands, used = [], []
    try:
        if a.channel or SLUG.fullmatch(arg):
            c = arena_contents(arg)
            used.append(f"{arg} ({len(c)})")
            cands = c
        else:
            d = get_json("https://api.are.na/v2/search?" + urllib.parse.urlencode({"q": arg, "per": 20}))
            for b in d.get("blocks") or []:
                im = b.get("image") or {}
                if b.get("class") == "Image" and im:
                    cands.append({"url": (im.get("large") or im.get("display") or {}).get("url", ""),
                                  "alt": [(im.get("original") or {}).get("url", "")],
                                  "page": f"https://www.are.na/block/{b['id']}",
                                  "title": clean_title(b.get("title"), "Are.na"),
                                  "credit": (b.get("user") or {}).get("full_name", "") + " · Are.na"})
            chans = [c for c in d.get("channels") or [] if (c.get("length") or 0) >= 6]
            cap = max(3, math.ceil(a.n / 2))
            for ch in chans[:4]:
                if len(cands) >= a.n * 2:
                    break
                try:
                    c = arena_contents(ch["slug"])
                except FetchError:
                    continue
                used.append(f"{ch['slug']} ({ch.get('length')})")
                cands += c[:cap]
    except FetchError as e:
        print(f"arena: request failed ({e})")
        return 1
    for c in cands:
        c["license"] = lic
    new, st = download_all(rs, [c for c in cands if c["url"]], a.n, "arena", arg)
    kept = rs.commit(new)
    code = report(f"arena \"{arg}\"", rs, kept, st)
    if used:
        print("  channels: " + "; ".join(used) + "  (whole channel: refs.py arena <slug> --out …)")
    return code


OG = re.compile(r"<meta\b[^>]*>", re.I)
ATTR = re.compile(r'([\w:-]+)\s*=\s*["\']([^"\']*)["\']')


def og_image(page_html: str, base: str) -> str:
    for tag in OG.findall(page_html):
        at = {k.lower(): v for k, v in ATTR.findall(tag)}
        if (at.get("property") or at.get("name") or "").lower() in ("og:image", "og:image:url",
                                                                     "twitter:image", "twitter:image:src"):
            if at.get("content"):
                return urllib.parse.urljoin(base, html.unescape(at["content"]))
    return ""


def cmd_urls(a) -> int:
    rs = RefSet(a.out)
    text = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    urls, shas = rs.known()
    new, st = [], {"dup": 0, "bad": 0, "err": 0, "why": []}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")] + [""] * 4
        u, page, credit, lic, note = parts[:5]
        if u in urls:
            st["dup"] += 1
            continue
        try:
            data, hdr, final = http_get(u)
            if not sniff(data) and "html" in hdr.get("content-type", ""):
                img = og_image(data[:400_000].decode("utf-8", "replace"), final)
                if img:
                    page = page or u
                    data, _, _ = http_get(img)
        except FetchError as e:
            st["err"] += 1
            st["why"].append(f"{u[:70]}: {e}")
            print(f"  error: {u[:80]} — {e}")
            continue
        sha = hashlib.sha1(data).hexdigest()
        if sha in shas:
            st["dup"] += 1
            continue
        stored = store_bytes(rs, data, None, "url")
        if not stored:
            st["bad"] += 1
            print(f"  not an image: {u[:80]}")
            continue
        p, w, h, sha = stored
        host = urllib.parse.urlsplit(page or u).hostname or ""
        new.append(item(p, w, h, sha, "url", "", {
            "url": u, "page": page or u, "title": note or host, "credit": credit or host,
            "license": lic or f"not specified — {MOODBOARD}", "note": note}))
        shas.add(sha)
        urls.add(u)
    kept = rs.commit(new)
    return report("urls", rs, kept, st)


def cmd_add(a) -> int:
    rs = RefSet(a.dir)
    urls, shas = rs.known()
    new, st = [], {"dup": 0, "bad": 0, "err": 0, "why": []}
    api = "generated" if a.generated else "local"
    for f in a.files:
        src = Path(f).expanduser()
        if not src.is_file():
            st["err"] += 1
            print(f"  no such file: {f}")
            continue
        data = src.read_bytes()
        sha = hashlib.sha1(data).hexdigest()
        if sha in shas:
            st["dup"] += 1
            continue
        stored = store_bytes(rs, data, f"{'gen' if a.generated else 'local'}-{sha[:8]}", api)
        if not stored:
            st["bad"] += 1
            print(f"  not an image: {f}")
            continue
        p, w, h, sha = stored
        new.append(item(p, w, h, sha, api, "", {
            "title": a.title or src.stem, "credit": a.credit or ("image generation" if a.generated else ""),
            "license": "generated for the project" if a.generated else (a.license or ""),
            "generated": a.generated, "note": a.note, "prompt": a.prompt}))
        shas.add(sha)
    kept = rs.commit(new)
    return report("add" + (" (generated)" if a.generated else ""), rs, kept, st)


# ----------------------------------------------------------------- video

def parse_ts(s: str) -> float:
    s = s.strip()
    if ":" in s:
        sec = 0.0
        for part in s.split(":"):
            sec = sec * 60 + float(part)
        return sec
    return float(s)


def probe_duration(src: str) -> float:
    if not shutil.which("ffprobe"):
        return 0.0
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", src], capture_output=True, text=True, timeout=60).stdout
        return float(out.strip() or 0)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return 0.0


def video_frames(rs: RefSet, src: str, duration: float | None, frames: int, at: list[float] | None,
                 api: str, query: str, stem: str, meta: dict) -> int:
    """Frames from a stream (direct URL/HLS) via ffmpeg -ss, 3 in parallel.
    meta["url"] / meta["page"] may contain `{t}` — replaced with the frame's second."""
    if not shutil.which("ffmpeg"):
        print("ffmpeg is required: brew install ffmpeg")
        return 1
    if at:
        times = at
    else:
        dur = duration or probe_duration(src)
        if dur <= 0:
            print("  could not get the duration — set the moments: --at 0:30,1:15")
            return 1
        a0, a1 = max(3.0, dur * 0.06), dur * 0.94
        times = [a0 + (a1 - a0) * (i + 0.5) / frames for i in range(frames)]
    tmp = Path(tempfile.mkdtemp(prefix="studioigor-frames-"))

    def grab(t: float):
        out = tmp / f"{int(t):06d}.jpg"
        ok = _run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1",
                   "-q:v", "2", "-y", str(out)], timeout=150)
        return t, out if ok and out.is_file() and out.stat().st_size > 0 else None

    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(grab, times))
    new, st = [], {"dup": 0, "bad": 0, "err": 0, "why": []}
    _, shas = rs.known()
    for t, f in res:
        if not f:
            st["err"] += 1
            continue
        data = f.read_bytes()
        sha = hashlib.sha1(data).hexdigest()
        if sha in shas:
            st["dup"] += 1
            continue
        mm = f"{int(t) // 60}:{int(t) % 60:02d}"
        stored = store_bytes(rs, data, f"{stem}-{int(t):05d}", api)
        if not stored:
            st["bad"] += 1
            continue
        p, w, h, sha = stored
        c = dict(meta, url=meta.get("url", "").replace("{t}", str(int(t))),
                 page=meta.get("page", "").replace("{t}", str(int(t))),
                 title=f"{meta.get('title', '')} @ {mm}", t=round(t, 1))
        new.append(item(p, w, h, sha, api, query, c))
        shas.add(sha)
    shutil.rmtree(tmp, ignore_errors=True)
    kept = rs.commit(new)
    return report(f"{api} frames \"{query}\"", rs, kept, st)


YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def cmd_youtube(a) -> int:
    rs = RefSet(a.out)
    if not shutil.which("yt-dlp"):
        print("yt-dlp is required: brew install yt-dlp")
        return 1
    arg = a.video.strip()
    if YT_ID.match(arg):
        arg = f"https://www.youtube.com/watch?v={arg}"
    if not arg.startswith("http"):
        r = subprocess.run(["yt-dlp", "--no-warnings", "--flat-playlist", "--print",
                            "%(id)s\t%(title)s\t%(duration)s\t%(channel)s", f"ytsearch8:{arg}"],
                           capture_output=True, text=True, timeout=90)
        rows = [ln.split("\t") for ln in r.stdout.splitlines() if ln.count("\t") >= 3]
        good = [x for x in rows if x[2].replace(".", "").isdigit() and float(x[2]) >= 90] or rows
        if not good:
            print(f"youtube: search \"{arg}\" found nothing. {r.stderr.strip()[:200]}")
            return 1
        vid = good[0][0]
        print(f"  picked: {good[0][1][:80]} ({good[0][3]}, {int(float(good[0][2] or 0)) // 60} min)")
        others = [f"{x[0]} {x[1][:50]}" for x in good[1:4]]
        if others:
            print("  others: " + " | ".join(others))
        query, arg = a.video, f"https://www.youtube.com/watch?v={vid}"
    else:
        query = arg
    fmt = f"bv*[height<={a.height}][ext=mp4]/bv*[height<={a.height}]/b[height<={a.height}]/b"
    r = subprocess.run(["yt-dlp", "--no-warnings", "--no-playlist", "-f", fmt, "--print", "%(id)s",
                        "--print", "%(title)s", "--print", "%(duration)s", "--print", "%(channel)s",
                        "--print", "urls", arg], capture_output=True, text=True, timeout=120)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    at = [parse_ts(x) for x in a.at.split(",")] if a.at else None
    if r.returncode != 0 or len(lines) < 5:
        err = (r.stderr.strip().splitlines() or ["?"])[-1][:200]
        print(f"youtube: no stream ({err}). Update yt-dlp (`yt-dlp -U` or brew/conda); "
              f"on \"JS runtime\" — with the user's consent, `brew install deno`. Taking the video thumbnail.")
        m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", arg)
        if not m:
            return 1
        vid = m.group(1)
        cands = [{"url": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                  "alt": [f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
                  "page": arg, "title": "video thumbnail", "credit": "YouTube",
                  "license": f"© the video author — {MOODBOARD}"}]
        new, st = download_all(rs, cands, 1, "youtube", query)
        return report("youtube thumbnail", rs, rs.commit(new), st)
    vid, title, dur, chan, stream = lines[0], lines[1], lines[2], lines[3], lines[4]
    try:
        duration = float(dur)
    except ValueError:
        duration = 0.0
    watch = f"https://www.youtube.com/watch?v={vid}&t={{t}}s"
    meta = {"page": watch, "url": watch, "title": title[:80],
            "credit": chan, "license": f"© {chan} — {MOODBOARD}"}
    return video_frames(rs, stream, duration, a.frames, at, "youtube", query, f"yt-{vid}", meta)


# ----------------------------------------------------------------- metadata

def split_list(vals: list[str] | None, sep: str) -> list[str]:
    out = []
    for v in vals or []:
        out += [x.strip() for x in v.split(sep) if x.strip()]
    return out


def cmd_meta(a) -> int:
    rs = RefSet(a.dir)

    def upd(d):
        if a.title is not None:
            d["title"] = a.title
        if a.text is not None:
            d["text"] = a.text
        if a.tags is not None:
            d["tags"] = split_list(a.tags, ",")
        if a.pros is not None:
            d["pros"] = split_list(a.pros, ";")
        if a.cons is not None:
            d["cons"] = split_list(a.cons, ";")
        if a.palette is not None:
            d["palette"] = [hexnorm(x) for x in split_list([a.palette], ",")]
    rs.update(upd)
    d = rs.data
    print(f"meta {rel(rs.dir)}: \"{d.get('title') or rs.dir.name}\"; tags {len(d.get('tags', []))}, "
          f"pros {len(d.get('pros', []))}, cons {len(d.get('cons', []))}, "
          f"palette {len(d.get('palette', []))}, images {len(rs.present())}")
    return 0


def cmd_note(a) -> int:
    rs = RefSet(a.dir, create=False)
    target = rs.find(a.file)["file"]

    def upd(d):
        for it in d["items"]:
            if it.get("file") == target:
                it["note"] = a.text
    rs.update(upd)
    print(f"note {target}: {a.text}")
    return 0


def cmd_drop(a) -> int:
    rs = RefSet(a.dir, create=False)
    targets = {rs.find(k)["file"] for k in a.files}

    def upd(d):
        keep, gone = [], d.setdefault("dropped", [])
        for it in d["items"]:
            if it.get("file") in targets:
                gone.append({k: it.get(k, "") for k in ("file", "url", "sha1")})
                (rs.dir / it["file"]).unlink(missing_ok=True)
            else:
                keep.append(it)
        d["items"] = keep
    rs.update(upd)
    print(f"drop: removed {len(targets)} from {rel(rs.dir)} ({len(rs.present())} left in set); they will not be downloaded again")
    return 0


def hexnorm(s: str) -> str:
    s = s.strip().lstrip("#").lower()
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if not re.fullmatch(r"[0-9a-f]{6}", s):
        sys.exit(f"error: '{s}' — not a hex color")
    return "#" + s


# ----------------------------------------------------------------- palette

def liked_files(fb_path: Path) -> list[Path]:
    fb = json.loads(fb_path.read_text(encoding="utf-8"))
    if "latest" in fb or "submissions" in fb:  # board.py serve format
        sub = fb.get("latest") or (fb.get("submissions") or [{}])[-1]
    else:  # bare payload the user pasted from the board's "Copy" window
        sub = fb
    out = []
    for key, v in (sub.get("reactions") or {}).items():
        if v != "like":
            continue
        p = (fb_path.parent / urllib.parse.unquote(key)).resolve()
        if p.is_file():
            out.append(p)
    return out


def histogram(files: list[Path], k: int, tmp: Path) -> list[tuple[int, tuple[int, int, int]]]:
    strip = tmp / "strip.png"
    if not strip.exists():
        smalls = []
        for i, f in enumerate(files):
            s = tmp / f"s{i:03d}.png"
            if _run(["magick", f"{f}[0]", "-alpha", "off", "-resize", "x120", str(s)]):
                smalls.append(str(s))
        if not smalls:
            return []
        if not _run(["magick", *smalls, "+append", str(strip)], timeout=180):
            return []
    r = subprocess.run(["magick", str(strip), "+dither", "-colors", str(k), "-depth", "8",
                        "-format", "%c", "histogram:info:-"], capture_output=True, text=True, timeout=180)
    rows = []
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*(\d+):\s*\(\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)", ln)
        if m:
            rows.append((int(m.group(1)), tuple(int(round(float(m.group(i)))) for i in (2, 3, 4))))
    return sorted(rows, reverse=True)


def cmd_palette(a) -> int:
    rs = RefSet(a.dir)
    if not shutil.which("magick"):
        print("ImageMagick is required: brew install imagemagick")
        return 1
    if a.liked:
        files = liked_files(Path(a.liked))
        src = f"likes from the board ({len(files)})"
        if not files:
            print(f"palette: {a.liked} has no likes on existing images")
            return 1
    else:
        files = [rs.dir / it["file"] for it in rs.present()]
        files += [p for p in sorted(rs.dir.iterdir()) if p.suffix.lower() in IMG_EXT and p not in files]
        src = f"all images in the set ({len(files)})"
    if not files:
        print(f"palette: no images in {rs.dir}")
        return 1
    tmp = Path(tempfile.mkdtemp(prefix="studioigor-pal-"))
    try:
        main = histogram(files, a.n, tmp)
        wide = histogram(files, 16, tmp) if not a.no_accent else []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not main:
        print("palette: ImageMagick could not read the images")
        return 1
    total = sum(c for c, _ in main) or 1
    hx = lambda rgb: "#%02x%02x%02x" % rgb
    accent = None
    if wide:
        tot_w = sum(c for c, _ in wide) or 1
        best = 0.0
        for c, rgb in wide:
            h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in rgb))
            share = c / tot_w
            far = min(math.dist(rgb, m) for _, m in main[: a.n - 1]) if main else 255
            score = s * v * math.sqrt(share) if share >= 0.003 and far > 60 and s > 0.45 and v > 0.35 else 0
            if score > best:
                best, accent = score, rgb
    chosen = [rgb for _, rgb in main[: a.n - 1 if accent else a.n]]
    pal = [hx(x) for x in chosen] + ([hx(accent)] if accent else [])

    def upd(d):
        d["palette"] = pal
        d["palette_from"] = src
    rs.update(upd)
    shares = {rgb: c / total for c, rgb in main}
    print(f"palette {rel(rs.dir)} ← {src}:")
    roles = ["dominant", "secondary"] + ["support"] * 10
    for i, rgb in enumerate(chosen):
        print(f"  {hx(rgb)}  {roles[i]:<10} {shares.get(rgb, 0) * 100:4.1f}%")
    if accent:
        print(f"  {hx(accent)}  accent candidate (rare, saturated; reserve it for one meaning)")
    return 0


def cmd_lospec(a) -> int:
    rs = RefSet(a.out)
    slug = a.slug.strip().lower().rstrip("/").split("/")[-1].removesuffix(".json")
    try:
        d = get_json(f"https://lospec.com/palette-list/{slug}.json")
    except FetchError as e:
        print(f"lospec: palette \"{slug}\" not fetched ({e}). The slug comes from the URL lospec.com/palette-list/<slug>")
        return 1
    cols = ["#" + c.lower() for c in d.get("colors") or []]
    if not cols:
        print(f"lospec: \"{slug}\" has no colors")
        return 1

    def upd(x):
        x["palette"] = cols
        x["palette_from"] = f"lospec:{slug}"
    rs.update(upd)
    print(f"lospec \"{d.get('name', slug)}\", colors: {len(cols)} → {rel(rs.path)}: {' '.join(cols)}")
    print(f"  palette PNG for `magick in.png -dither None -remap pal.png out.png`: "
          f"https://lospec.com/palette-list/{slug}-1x.png")
    return 0


# ----------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="studioigor references → refs/<set>/sources.json")
    sp = ap.add_subparsers(dest="cmd", required=True)

    def src(name, arg, hlp, n=8):
        p = sp.add_parser(name, help=hlp)
        p.add_argument(arg)
        p.add_argument("--out", required=True, help="set folder, e.g. .studioigor/refs/neon")
        p.add_argument("--n", type=int, default=n, help="how many images to add")
        return p

    p = src("steam", "game", "game screenshots from Steam")
    p.add_argument("--trailer", type=int, default=0, help="plus K frames from the trailer")
    p = src("openverse", "query", "Openverse CC images")
    p.add_argument("--license-type", choices=["all", "commercial"], default="all")
    p.add_argument("--category", choices=["photograph", "illustration", "digitized_artwork"])
    src("wikimedia", "query", "Wikimedia Commons")
    src("artstation", "query", "ArtStation covers")
    p = src("arena", "query", "Are.na moodboards: a query or a channel slug")
    p.add_argument("--channel", action="store_true", help="the argument is a channel slug")
    p = sp.add_parser("urls", help="download a list of URLs")
    p.add_argument("file", help="file with lines `URL [| page | credit | license | note]`, or -")
    p.add_argument("--out", required=True)
    p = sp.add_parser("youtube", help="video frames (URL, id or search query)")
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--frames", type=int, default=6)
    p.add_argument("--at", default="", help="comma-separated moments: 0:45,2:10,300")
    p.add_argument("--height", type=int, default=720)
    p = sp.add_parser("add", help="add local images (concepts, screenshots)")
    p.add_argument("dir")
    p.add_argument("files", nargs="+")
    p.add_argument("--generated", action="store_true", help="made with an image-generation tool (generated:true)")
    p.add_argument("--prompt", default="")
    p.add_argument("--note", default="")
    p.add_argument("--title", default="")
    p.add_argument("--credit", default="")
    p.add_argument("--license", default="")
    p = sp.add_parser("meta", help="title, description, tags, pros/cons of the direction")
    p.add_argument("dir")
    p.add_argument("--title")
    p.add_argument("--text")
    p.add_argument("--tags", action="append", help="comma-separated")
    p.add_argument("--pros", action="append", help="separated by ';', or repeat the flag")
    p.add_argument("--cons", action="append")
    p.add_argument("--palette", help="comma-separated hex")
    p = sp.add_parser("note", help="what we take from the image (caption on the board)")
    p.add_argument("dir")
    p.add_argument("file")
    p.add_argument("text")
    p = sp.add_parser("drop", help="remove images from the set")
    p.add_argument("dir")
    p.add_argument("files", nargs="+")
    p = sp.add_parser("palette", help="ImageMagick palette from the set or from the likes")
    p.add_argument("dir")
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--liked", help="boards/<board>/feedback.json — liked images only")
    p.add_argument("--no-accent", action="store_true")
    p = sp.add_parser("lospec", help="Lospec palette by slug")
    p.add_argument("slug")
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    fn = {"steam": cmd_steam, "openverse": cmd_openverse, "wikimedia": cmd_wikimedia,
          "artstation": cmd_artstation, "arena": cmd_arena, "urls": cmd_urls, "youtube": cmd_youtube,
          "add": cmd_add, "meta": cmd_meta, "note": cmd_note, "drop": cmd_drop,
          "palette": cmd_palette, "lospec": cmd_lospec}[a.cmd]
    try:
        return fn(a)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
