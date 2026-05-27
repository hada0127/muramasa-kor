"""UI 텍스처 편집 웹도구 — 경량 서버 (stdlib http.server, 외부 의존성 없음).

실행:
  python tools/ui_editor/server.py            # http://127.0.0.1:8765
  python tools/ui_editor/server.py --port 9000

3분할 편집 UI를 제공한다.
  좌  : textures/kr/ui 파일 목록 (메모 표시)
  중간: 캔버스 (원본/kr 토글, 배경색, region 박스 드래그/리사이즈)
  우  : 선택 region 속성 편집

API
  GET  /api/index                  통합 인덱스 (translations/ui_editor_index.json)
  GET  /api/image?path=<rel>       레포 내 PNG 직접 서빙
  POST /api/memo    {hash, memo}   인덱스에 메모 저장
  POST /api/regions {hash, system, regions[]}  네이티브 config 역기록 + 인덱스 갱신
  POST /api/render  {hash}         실제 렌더러 호출 → 미리보기 PNG 경로 반환
"""
import argparse
import json
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
INDEX_PATH = ROOT / "translations" / "ui_editor_index.json"
LOCALIZE_CONFIG = ROOT / "translations" / "texture_localize_config.json"
PLACE_JOBS = ROOT / "translations" / "place_texture_jobs.json"
BUTTON_VARIANTS = ROOT / "translations" / "button_variants.json"
PREVIEW_DIR = ROOT / "output" / "texture_preview"

if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from localize_region_io import color_list as _color_list  # noqa: E402
from localize_region_io import to_native_localize as _to_native_localize  # noqa: E402
from localize_region_io import upd as _upd  # noqa: E402

_LOCK = threading.Lock()

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".json": "application/json; charset=utf-8",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def update_memo(hash_id, memo):
    with _LOCK:
        idx = load_json(INDEX_PATH)
        for t in idx["textures"]:
            if t["hash"] == hash_id:
                t["memo"] = memo
                break
        save_json(INDEX_PATH, idx)
    return {"ok": True}


def _to_native_place(r):
    """편집 region → place_texture_jobs 네이티브 region."""
    x, y, w, h = [int(round(v)) for v in r["box"]]
    nr = dict(r.get("native") or {})
    nr["bbox"] = [x, y, x + w, y + h]
    _upd(nr, "ko", r.get("text", ""), "")
    _upd(nr, "text_color", r.get("text_color", "black"), "black")
    _upd(nr, "padding", float(r.get("padding", 0.08)), 0.08)
    _upd(nr, "font_ratio", float(r.get("font_ratio", 0.85)), 0.85)
    if r.get("font_px"):
        nr["font_px"] = int(r["font_px"])
    else:
        nr.pop("font_px", None)
    _upd(nr, "letter_spacing", int(r.get("letter_spacing") or 0), 0)
    _upd(nr, "align", r.get("align", "center"), "center")
    _upd(nr, "valign", r.get("valign", "center"), "center")
    _upd(nr, "rotation", int(r.get("rotation", 0) or 0), 0)
    for pk in ("pad_x", "pad_y"):
        pv = r.get(pk)
        if pv is None or pv == "":
            nr.pop(pk, None)
        else:
            nr[pk] = int(pv)
    _upd(nr, "render", bool(r.get("render", True)), True)
    ow = int(r.get("outline_width") or 0)
    oc = r.get("outline_color")
    if ow > 0:
        nr["outline_width"] = ow
        nr["outline_color"] = list(oc) if isinstance(oc, list) and len(oc) >= 3 else [0, 0, 0, 255]
    else:
        nr.pop("outline_width", None)
        nr.pop("outline_color", None)
    bg = r.get("background")
    if bg in ("red", "black"):
        nr["background"] = bg
        nr.pop("clear", None)
    elif bg == "clear_alpha":
        nr.pop("background", None)
        nr["clear"] = "alpha"
    elif bg == "clear_white":
        nr.pop("background", None)
        nr["clear"] = "white"
    else:
        nr.pop("background", None)
        nr.pop("clear", None)
    if r.get("layout"):
        nr["layout"] = r["layout"]
    else:
        nr.pop("layout", None)
    return nr


def save_regions(hash_id, system, regions):
    """편집된 통합 region 목록을 네이티브 config 에 역기록하고 인덱스도 갱신."""
    with _LOCK:
        if system == "localize":
            cfg = load_json(LOCALIZE_CONFIG)
            tex = next((t for t in cfg["textures"] if t["hash"] == hash_id), None)
            if tex is None:
                return {"ok": False, "error": "localize hash not found"}
            region_key = "regions" if tex.get("regions") else (
                "manual_regions" if tex.get("manual_regions") else "regions")
            tex[region_key] = [_to_native_localize(r) for r in regions]
            save_json(LOCALIZE_CONFIG, cfg)
        elif system == "place":
            doc = load_json(PLACE_JOBS)
            job = doc["textures"].get(hash_id)
            if job is None:
                return {"ok": False, "error": "place hash not found"}
            job["regions"] = [_to_native_place(r) for r in regions]
            save_json(PLACE_JOBS, doc)
        else:
            return {"ok": False, "error": f"system '{system}' 은 region 편집 미지원"}

        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_ui_index.py")],
            cwd=str(ROOT), check=False, capture_output=True,
        )
    return {"ok": True}


def _render_place_layer(img, native_regions, font, mode):
    """place: mode에 따라 clear/bg 와/또는 텍스트를 img(RGBA)에 적용. config 미변경."""
    import render_place_texture_job as PJ
    from PIL import Image as _Img
    for region in native_regions:
        if not region.get("render", True):
            continue
        bbox = region["bbox"]
        if mode in ("full", "bg"):
            background = region.get("background")
            if background in PJ.BACKGROUND_COLORS:
                if region.get("background_mode") == "fill":
                    img = PJ.fill_region(img, bbox, PJ.BACKGROUND_COLORS[background])
                else:
                    img = PJ.clear_region(img, bbox, PJ.BACKGROUND_COLORS[background])
            elif region.get("clear") == "white":
                img = PJ.kill_white_in_bbox(img, bbox)
            elif region.get("clear") == "alpha":
                img = PJ.clear_alpha_in_bbox(img, bbox)
        if mode in ("full", "text"):
            text = region.get("ko", "")
            if text:
                PJ.render_text(
                    img, bbox, text, PJ.TEXT_COLORS[region.get("text_color", "black")],
                    font, padding=float(region.get("padding", 0.08)),
                    fr=float(region.get("font_ratio", 0.85)),
                    layout=region.get("layout"),
                    letter_spacing=int(region.get("letter_spacing") or 0),
                    align=region.get("align", "center"), valign=region.get("valign", "center"),
                    pad_x=region.get("pad_x"), pad_y=region.get("pad_y"),
                    font_px=region.get("font_px"), rotation=int(region.get("rotation") or 0),
                    outline_width=int(region.get("outline_width", 0) or 0),
                    outline_fill=tuple(region["outline_color"]) if region.get("outline_color") else None,
                )
    return img


def render_live(hash_id, system, regions, mode="full"):
    """현재 편집중 region(미저장)으로 실제 렌더 → 캔버스 표시용 PNG. config 미변경.
    mode: full=전체, text=한글 텍스트만(투명), bg=배경(원본+clear/bg, 텍스트 제외)."""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    from PIL import Image
    live = PREVIEW_DIR / f"{hash_id}_live_{mode}.png"
    try:
        if system == "place":
            import render_place_texture_job as PJ
            doc = load_json(PLACE_JOBS)
            base = doc["textures"].get(hash_id, {})
            source = PJ.repo_path(base.get("source"), PJ.DEFAULT_SOURCE_DIR / f"{hash_id}.png")
            font = PJ.repo_path(doc.get("font"), PJ.DEFAULT_FONT)
            src_img = Image.open(source).convert("RGBA")
            img = Image.new("RGBA", src_img.size, (0, 0, 0, 0)) if mode == "text" else src_img
            img = _render_place_layer(img, [_to_native_place(r) for r in regions], font, mode)
            scale = int(base.get("output_scale", 1))
            if scale > 1:
                img = img.resize((img.width * scale, img.height * scale), Image.Resampling.LANCZOS)
            img.save(live)
        elif system == "localize":
            import texture_localize as TL
            cfg = load_json(LOCALIZE_CONFIG)
            tex = next((t for t in cfg["textures"] if t["hash"] == hash_id), None)
            if tex is None:
                return {"ok": False, "error": "not found"}
            tmp = dict(tex)
            tmp["regions"] = [_to_native_localize(r) for r in regions]
            if not tmp["regions"]:
                return {"ok": False, "error": "no regions"}
            # bg 모드: clear만, text 모드: clear 끄고 텍스트만. (텍스처별 단순화)
            if mode == "bg":
                tmp["regions"] = [{**r, "text": ""} for r in tmp["regions"]]
            elif mode == "text":
                tmp["regions"] = [{**r, "clear": False} for r in tmp["regions"]]
            orig_imp, orig_repo = TL.IMPORT_DIR, TL.REPO_KR_DIR
            TL.IMPORT_DIR = PREVIEW_DIR
            TL.REPO_KR_DIR = PREVIEW_DIR / "_live_repo"
            try:
                TL.process_texture(hash_id, tmp, preview=False)
            finally:
                TL.IMPORT_DIR, TL.REPO_KR_DIR = orig_imp, orig_repo
            out = PREVIEW_DIR / f"{hash_id}.png"
            if out.exists():
                out.replace(live)
        else:
            return {"ok": False, "error": "unsupported"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": repr(e)}
    if not live.exists():
        return {"ok": False, "error": "render 실패"}
    return {"ok": True, "path": str(live.relative_to(ROOT))}


def render_preview(hash_id, system):
    """실제 textures/kr/ui 이미지를 생성하고 그 경로를 반환 (저장 및 미리보기)."""
    out = ROOT / "textures/kr" / "ui" / f"{hash_id}.png"
    if system == "localize":
        cfg = load_json(LOCALIZE_CONFIG)
        tex = next((t for t in cfg["textures"] if t["hash"] == hash_id), None)
        # manual_regions만 있고 사용자가 render를 요청 → regions로 승격 (자동 render 대상)
        if tex is not None and not tex.get("regions") and tex.get("manual_regions"):
            tex["regions"] = tex.pop("manual_regions")
            save_json(LOCALIZE_CONFIG, cfg)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "texture_localize.py"), hash_id],
            cwd=str(ROOT), capture_output=True, text=True,
        )
    elif system == "place":
        # 기본 출력 경로가 textures/kr/ui (render_place_texture_job.DEFAULT_OUT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "render_place_texture_job.py"),
             hash_id, "--include-needs-review"],
            cwd=str(ROOT), capture_output=True, text=True,
        )
    else:
        return {"ok": False, "error": "manual 텍스처는 렌더러가 없습니다 (kr png 직접 편집)"}

    if not out.exists():
        return {"ok": False, "error": (proc.stdout + proc.stderr)[-800:] or "출력 없음"}
    rel = str(out.relative_to(ROOT))
    return {"ok": True, "path": rel, "log": (proc.stdout + proc.stderr)[-800:]}


# ===== ✕ 버튼 변형팩 (이슈 #12) =====
def button_variants_info(hash_id=None):
    """변형 레지스트리 + 각 항목의 ✕ PNG 존재 여부. hash_id 주면 해당 항목만."""
    import build_button_variant as BV
    cfg = BV.load_config()
    out_dir = ROOT / cfg["out_dir"]
    items = []
    for v in cfg.get("variants", []):
        png = out_dir / f"{v['hash']}.png"
        items.append({
            "hash": v["hash"],
            "label": v.get("label", ""),
            "memo": v.get("memo", ""),
            "has_ops": bool(v.get("ops")),
            "system": v.get("system", ""),
            "editable": v.get("exclude_region_ids") is not None or v.get("system") == "localize",
            "excluded": v.get("exclude_region_ids", []) or [],
            "variant_png": str(png.relative_to(ROOT)) if png.exists() else None,
            "base_png": f"{cfg['base_dir']}/{v['hash']}.png",
        })
    info = {"caveat": cfg.get("_caveat", ""), "out_dir": cfg["out_dir"], "variants": items}
    if hash_id is not None:
        info["selected"] = next((i for i in items if i["hash"] == hash_id), None)
    return info


def button_variant_build(hash_id=None):
    import build_button_variant as BV
    with _LOCK:
        prefix = hash_id.upper() if hash_id else None
        try:
            BV.build(prefix=prefix)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": repr(e)}
    return {"ok": True, **button_variants_info(hash_id)}


def variant_regions_get(hash_id):
    """✕ 편집 모드용: 기본(○) region 전체(UI 포맷) + 현재 ✕에서 빼둔(excluded) region _id 목록."""
    import build_button_variant as BV
    idx = load_json(INDEX_PATH)
    tex = next((t for t in idx["textures"] if t["hash"] == hash_id), None)
    if tex is None:
        return {"ok": False, "error": "인덱스에 없음"}
    v = BV.find_variant(BV.load_config(), hash_id)
    excluded = (v or {}).get("exclude_region_ids", []) or []
    return {"ok": True, "hash": hash_id, "regions": tex.get("regions", []),
            "excluded": excluded, "system": tex.get("system", "")}


def save_variant_regions(hash_id, kept_ids):
    """편집기에서 남긴(kept) region _id 목록으로 exclude를 계산·저장하고 ui_xbutton에 렌더.

    kept_ids = ✕ 편집 모드에서 삭제하지 않고 남긴 region들의 _id. 나머지(=삭제한 것)가 exclude.
    """
    import build_button_variant as BV
    with _LOCK:
        all_regs = BV.localize_regions(hash_id)
        all_ids = [r.get("_id") for r in all_regs if r.get("_id")]
        kept = set(kept_ids or [])
        exclude = [rid for rid in all_ids if rid not in kept]
        BV.set_variant_exclude(hash_id, exclude, "localize")
        try:
            out = BV.render_localize_variant(hash_id, exclude)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": repr(e)}
    return {"ok": True, "path": str(out.relative_to(ROOT)), "excluded": exclude}


def button_variant_export():
    """✕ 추가팩 zip을 dist/에 빌드(본편 CPK 패치 생략)."""
    version = "0.0.0"
    vf = ROOT / "release" / "version.json"
    if vf.exists():
        version = str(load_json(vf).get("version", version))
    with _LOCK:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_release.py"),
             "--xbutton-only", "--keep-dist", "--version", version],
            cwd=str(ROOT), capture_output=True, text=True,
        )
    zip_rel = f"dist/muramasa-kor-xbutton-v{version}.zip"
    ok = (ROOT / zip_rel).exists() and proc.returncode == 0
    return {"ok": ok, "zip": zip_rel if ok else None,
            "log": (proc.stdout + proc.stderr)[-1200:]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 콘솔 조용히

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self._send(404, {"error": "not found"})
            return
        data = path.read_bytes()
        self._send(200, data, MIME.get(path.suffix.lower(), "application/octet-stream"))

    def _safe_repo_path(self, rel):
        """레포 밖 접근 차단."""
        p = (ROOT / rel).resolve()
        if ROOT not in p.parents and p != ROOT:
            return None
        return p

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path

        if route == "/" or route == "/index.html":
            self._send_file(STATIC / "index.html")
        elif route.startswith("/static/"):
            self._send_file(STATIC / route[len("/static/"):])
        elif route == "/api/index":
            self._send(200, load_json(INDEX_PATH))
        elif route == "/api/button_variants":
            qs = urllib.parse.parse_qs(parsed.query)
            self._send(200, button_variants_info(qs.get("hash", [None])[0]))
        elif route == "/api/variant_regions":
            qs = urllib.parse.parse_qs(parsed.query)
            self._send(200, variant_regions_get(qs.get("hash", [""])[0]))
        elif route == "/api/image":
            qs = urllib.parse.parse_qs(parsed.query)
            rel = qs.get("path", [""])[0]
            p = self._safe_repo_path(rel)
            if p is None:
                self._send(403, {"error": "forbidden"})
            else:
                self._send_file(p)
        else:
            self._send(404, {"error": "unknown route"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "bad json"})
            return

        route = urllib.parse.urlparse(self.path).path
        try:
            if route == "/api/memo":
                self._send(200, update_memo(data["hash"], data.get("memo", "")))
            elif route == "/api/regions":
                self._send(200, save_regions(
                    data["hash"], data["system"], data.get("regions", [])))
            elif route == "/api/render":
                self._send(200, render_preview(data["hash"], data["system"]))
            elif route == "/api/render_live":
                self._send(200, render_live(
                    data["hash"], data["system"], data.get("regions", []),
                    data.get("mode", "full")))
            elif route == "/api/button_variant_memo":
                import build_button_variant as BV
                with _LOCK:
                    self._send(200, BV.set_memo(data["hash"], data.get("memo", "")))
            elif route == "/api/button_variant_toggle":
                import build_button_variant as BV
                with _LOCK:
                    self._send(200, BV.toggle(
                        data["hash"], bool(data.get("include")), data.get("label", "")))
            elif route == "/api/button_variant_build":
                self._send(200, button_variant_build(data.get("hash")))
            elif route == "/api/button_variant_export":
                self._send(200, button_variant_export())
            elif route == "/api/save_variant_regions":
                self._send(200, save_variant_regions(data["hash"], data.get("kept_ids", [])))
            else:
                self._send(404, {"error": "unknown route"})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": repr(e)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        print("인덱스가 없습니다. tools/build_ui_index.py 를 먼저 실행하세요.")
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_ui_index.py")],
                       cwd=str(ROOT))

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"UI 텍스처 편집기: http://{args.host}:{args.port}")
    print("  Ctrl+C 로 종료")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n종료")
        srv.shutdown()


if __name__ == "__main__":
    main()
