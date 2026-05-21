"use strict";

// ===== 상태 =====
let INDEX = null;            // 전체 인덱스
let CUR = null;              // 현재 선택 텍스처 entry (작업 사본)
let SEL = -1;                // 선택된 region 인덱스
let SCALE = 1;               // 텍스처좌표→화면픽셀 배율
let NAT = [1, 1];            // 텍스처 원본 크기 [w,h]

const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

function toast(msg, err) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "show" + (err ? " err" : "");
  setTimeout(() => (t.className = ""), 1800);
}

async function api(path, body) {
  const opt = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opt);
  return r.json();
}

// ===== 좌측 목록 =====
function renderList() {
  const q = $("#search").value.trim().toLowerCase();
  const sys = new Set($$(".sysfilter:checked").map((c) => c.value));
  const ul = $("#files");
  ul.innerHTML = "";
  let shown = 0;
  for (const t of INDEX.textures) {
    if (!sys.has(t.system)) continue;
    const hay = (t.hash + " " + (t.memo || "") + " " + (t.description || "")).toLowerCase();
    if (q && !hay.includes(q)) continue;
    shown++;
    const li = document.createElement("li");
    li.className = "file-row" + (CUR && CUR.hash === t.hash ? " active" : "");
    li.innerHTML = `
      <img loading="lazy" src="/api/image?path=${encodeURIComponent(t.png)}">
      <div class="file-meta">
        <div class="file-hash">${t.hash}<span class="sys-badge sys-${t.system}">${t.system}</span></div>
        <div class="file-memo">${escapeHtml(t.memo || "")}</div>
        <div class="file-desc">${escapeHtml(t.description || "")}</div>
      </div>`;
    li.onclick = () => selectTexture(t.hash);
    ul.appendChild(li);
  }
  $("#liststat").textContent = `${shown} / ${INDEX.textures.length} 표시`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ===== 텍스처 선택 / 캔버스 =====
function selectTexture(hash) {
  CUR = JSON.parse(JSON.stringify(INDEX.textures.find((t) => t.hash === hash)));
  SEL = -1;
  $("#cur-hash").textContent = `${CUR.hash}  ·  ${CUR.system}  ·  ${(CUR.size || []).join("×")}`;
  $("#memo-input").value = CUR.memo || "";
  $("#btn-render").disabled = CUR.system === "manual";
  $("#btn-add").disabled = CUR.system === "manual";
  renderList();
  loadImage();
  renderProps();
}

function loadImage() {
  const img = $("#tex-img");
  $("#show-original").checked = false;
  img.onload = () => {
    NAT = [img.naturalWidth, img.naturalHeight];
    applyZoom();
  };
  img.src = `/api/image?path=${encodeURIComponent(CUR.png)}`;
}

function curImagePath() {
  if ($("#show-original").checked && CUR.source) return CUR.source;
  return CUR.png;
}

function applyZoom() {
  const z = $("#zoom").value;
  const wrap = $("#canvas-wrap");
  let scale;
  if (z === "fit") {
    const avail = wrap.clientWidth - 40;
    scale = Math.min(1, avail / NAT[0]);
  } else {
    scale = parseFloat(z);
  }
  SCALE = scale;
  const img = $("#tex-img");
  img.style.width = NAT[0] * scale + "px";
  img.style.height = NAT[1] * scale + "px";
  $("#stage").style.width = NAT[0] * scale + "px";
  $("#stage").style.height = NAT[1] * scale + "px";
  drawRegions();
}

function drawRegions() {
  const ov = $("#overlay");
  ov.innerHTML = "";
  if (!CUR) return;
  CUR.regions.forEach((r, i) => {
    const [x, y, w, h] = r.box;
    const el = document.createElement("div");
    el.className = "region" + (i === SEL ? " selected" : "");
    el.style.left = x * SCALE + "px";
    el.style.top = y * SCALE + "px";
    el.style.width = w * SCALE + "px";
    el.style.height = h * SCALE + "px";
    const label = r.text || r.id || "(빈 텍스트)";
    el.innerHTML = `<span class="rlabel">${escapeHtml(label.slice(0, 16))}</span>`;
    if (i === SEL) {
      for (const hp of ["nw", "ne", "sw", "se", "n", "s", "w", "e"]) {
        const hd = document.createElement("div");
        hd.className = "handle " + hp;
        hd.dataset.handle = hp;
        el.appendChild(hd);
      }
    }
    el.onmousedown = (e) => startDrag(e, i);
    ov.appendChild(el);
  });
}

// ===== 드래그/리사이즈 =====
function startDrag(e, i) {
  e.preventDefault();
  e.stopPropagation();
  if (SEL !== i) { SEL = i; drawRegions(); renderProps(); }
  const handle = e.target.dataset.handle || "move";
  const start = { mx: e.clientX, my: e.clientY, box: [...CUR.regions[i].box] };
  const onMove = (ev) => {
    const dx = (ev.clientX - start.mx) / SCALE;
    const dy = (ev.clientY - start.my) / SCALE;
    let [x, y, w, h] = start.box;
    if (handle === "move") { x += dx; y += dy; }
    if (handle.includes("w")) { x += dx; w -= dx; }
    if (handle.includes("e")) { w += dx; }
    if (handle.includes("n")) { y += dy; h -= dy; }
    if (handle.includes("s")) { h += dy; }
    w = Math.max(4, w); h = Math.max(4, h);
    CUR.regions[i].box = [Math.round(x), Math.round(y), Math.round(w), Math.round(h)];
    drawRegions();
    updateBoxFields();
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

// ===== 우측 속성 =====
function renderProps() {
  const form = $("#props-form");
  const empty = $("#props-empty");
  const actions = $("#props-actions");
  if (SEL < 0 || !CUR || !CUR.regions[SEL]) {
    form.hidden = true; actions.hidden = true; empty.hidden = false;
    return;
  }
  empty.hidden = true; form.hidden = false; actions.hidden = false;
  const r = CUR.regions[SEL];
  let html = "";
  if (CUR.system === "place" && r.ja) {
    html += `<div class="field"><label>일본어 원문</label><div class="muted">${escapeHtml(r.ja)}</div></div>`;
  }
  html += field("text", "번역 텍스트", `<textarea data-k="text">${escapeHtml(r.text || "")}</textarea>`);
  html += `<div class="field"><label>박스 (x, y, w, h)</label><div class="field-row">
    ${boxInput("bx", r.box[0])}${boxInput("by", r.box[1])}${boxInput("bw", r.box[2])}${boxInput("bh", r.box[3])}</div></div>`;

  if (CUR.system === "localize") {
    html += field("font_size", "글씨 크기 (px)", `<input type="number" data-k="font_size" value="${r.font_size || 24}">`);
    html += selField("colorPick", "글씨 색", colorToName(r.color), [["white", "화이트"], ["black", "블랙"]]);
    html += selField("align", "가로 정렬", r.align || "left", [["left", "왼쪽"], ["center", "가운데"], ["right", "오른쪽"]]);
    html += selField("v_align", "세로 정렬", r.v_align || "top", [["top", "위"], ["center", "가운데"], ["bottom", "아래"]]);
    html += checkField("fit_to_box", "박스에 맞춰 축소", r.fit_to_box);
    html += selField("bgLoc", "배경 처리", r.clear ? "clear" : "transparent",
      [["transparent", "투명(원본 유지)"], ["clear", "기존 영역 삭제"]]);
  } else if (CUR.system === "place") {
    html += selField("text_color", "글씨 색", r.text_color || "black", [["black", "블랙"], ["white", "화이트"]]);
    html += selField("background", "배경 색", r.background || "transparent",
      [["transparent", "투명"], ["black", "블랙"], ["red", "지명 레드"],
       ["clear_alpha", "기존 영역 삭제"], ["clear_white", "흰 글자 제거"]]);
    html += selField("layout", "쓰기 방향", r.layout || "auto",
      [["auto", "자동"], ["horizontal", "가로쓰기"], ["vertical_columns", "세로쓰기(열)"], ["rotated", "회전 90°(세로배너)"]]);
    html += field("font_ratio", "글씨 비율", `<input type="number" step="0.01" data-k="font_ratio" value="${r.font_ratio ?? 0.85}">`);
    html += field("padding", "안쪽 여백", `<input type="number" step="0.01" data-k="padding" value="${r.padding ?? 0.08}">`);
    html += checkField("render", "이 영역 렌더링", r.render !== false);
  }
  form.innerHTML = html;
  form.oninput = readProps;
  form.onchange = readProps;
}

function field(k, label, inner) {
  return `<div class="field"><label>${label}</label>${inner}</div>`;
}
function boxInput(k, v) {
  return `<div><input type="number" data-box="${k}" value="${v}"></div>`;
}
function selField(k, label, val, opts) {
  const o = opts.map(([v, t]) => `<option value="${v}"${v === val ? " selected" : ""}>${t}</option>`).join("");
  return field(k, label, `<select data-k="${k}">${o}</select>`);
}
function checkField(k, label, checked) {
  return `<div class="field"><label><input type="checkbox" data-k="${k}"${checked ? " checked" : ""}> ${label}</label></div>`;
}
function colorToName(c) {
  if (Array.isArray(c) && c[0] < 128 && c[1] < 128 && c[2] < 128) return "black";
  return "white";
}

function updateBoxFields() {
  if (SEL < 0) return;
  const b = CUR.regions[SEL].box;
  const map = { bx: 0, by: 1, bw: 2, bh: 3 };
  $$("[data-box]").forEach((el) => (el.value = b[map[el.dataset.box]]));
}

function readProps() {
  if (SEL < 0) return;
  const r = CUR.regions[SEL];
  // box
  const map = { bx: 0, by: 1, bw: 2, bh: 3 };
  $$("[data-box]").forEach((el) => (r.box[map[el.dataset.box]] = Math.round(+el.value || 0)));
  // fields
  $$("[data-k]").forEach((el) => {
    const k = el.dataset.k;
    const v = el.type === "checkbox" ? el.checked : el.value;
    if (k === "colorPick") {
      r.color = v === "black" ? [0, 0, 0, 255] : [255, 255, 255, 255];
    } else if (k === "bgLoc") {
      r.clear = v === "clear";
    } else if (k === "font_size") {
      r.font_size = parseInt(v) || 24;
    } else if (k === "font_ratio" || k === "padding") {
      r[k] = parseFloat(v) || 0;
    } else if (k === "background") {
      r.background = v;
    } else {
      r[k] = v;
    }
  });
  drawRegions();
}

// ===== 액션 =====
function addRegion() {
  if (!CUR || CUR.system === "manual") return;
  const cx = Math.round(NAT[0] / 4), cy = Math.round(NAT[1] / 4);
  const base = { box: [cx, cy, Math.round(NAT[0] / 4), Math.round(NAT[1] / 8)], text: "텍스트" };
  if (CUR.system === "localize") {
    Object.assign(base, { font_size: 24, color: [255, 255, 255, 255], align: "center", v_align: "center", clear: true, fit_to_box: true });
  } else {
    Object.assign(base, { text_color: "black", background: "red", layout: "rotated", padding: 0.08, font_ratio: 0.74, render: true });
  }
  CUR.regions.push(base);
  SEL = CUR.regions.length - 1;
  drawRegions();
  renderProps();
}

async function applyRegions() {
  readProps();
  const res = await api("/api/regions", { hash: CUR.hash, system: CUR.system, regions: CUR.regions });
  if (res.ok) {
    toast("config에 저장됨");
    INDEX = await api("/api/index");
    // 작업본 갱신 (native 동기화)
    const fresh = INDEX.textures.find((t) => t.hash === CUR.hash);
    if (fresh) { CUR = JSON.parse(JSON.stringify(fresh)); SEL = Math.min(SEL, CUR.regions.length - 1); }
    drawRegions(); renderProps(); renderList();
  } else {
    toast(res.error || "저장 실패", true);
  }
}

function delRegion() {
  if (SEL < 0) return;
  CUR.regions.splice(SEL, 1);
  SEL = -1;
  drawRegions(); renderProps();
  toast("영역 삭제됨 (반영 눌러야 config 저장)");
}

async function saveMemo() {
  const memo = $("#memo-input").value;
  const res = await api("/api/memo", { hash: CUR.hash, memo });
  if (res.ok) {
    CUR.memo = memo;
    INDEX.textures.find((t) => t.hash === CUR.hash).memo = memo;
    renderList();
    toast("메모 저장됨");
  } else toast("메모 저장 실패", true);
}

async function renderPreview() {
  toast("렌더링 중…");
  // 먼저 현재 편집 내용을 저장해야 실제 렌더에 반영됨
  await applyRegions();
  const res = await api("/api/render", { hash: CUR.hash, system: CUR.system });
  if (res.ok) {
    $("#modal-img").src = `/api/image?path=${encodeURIComponent(res.path)}&t=${Date.now()}`;
    $("#modal-log").textContent = res.log || "";
    $("#modal").hidden = false;
  } else {
    toast(res.error || "렌더 실패", true);
    $("#modal-log").textContent = res.error || "";
  }
}

// ===== 초기화 =====
async function init() {
  INDEX = await api("/api/index");
  renderList();
  $("#search").oninput = renderList;
  $$(".sysfilter").forEach((c) => (c.onchange = renderList));
  $("#bg-color").onchange = () => {
    $("#stage").className = "bg-" + $("#bg-color").value;
  };
  $("#bg-color").onchange();
  $("#zoom").onchange = applyZoom;
  $("#show-original").onchange = () => { $("#tex-img").src = `/api/image?path=${encodeURIComponent(curImagePath())}`; };
  $("#btn-add").onclick = addRegion;
  $("#btn-apply").onclick = applyRegions;
  $("#btn-del").onclick = delRegion;
  $("#btn-memo").onclick = saveMemo;
  $("#btn-render").onclick = renderPreview;
  $("#modal-close").onclick = () => ($("#modal").hidden = true);
  $("#modal").onclick = (e) => { if (e.target.id === "modal") $("#modal").hidden = true; };
  $$(".modal-bgsel button").forEach((b) => (b.onclick = () => {
    $$(".modal-bgsel button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("#modal-imgwrap").className = "bg-" + b.dataset.bg;
  }));
  window.addEventListener("resize", () => { if (CUR) applyZoom(); });
  $("#overlay").onmousedown = (e) => { if (e.target.id === "overlay") { SEL = -1; drawRegions(); renderProps(); } };
}

init();
