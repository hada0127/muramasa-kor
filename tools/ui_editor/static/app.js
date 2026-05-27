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
  const found = INDEX.textures.find((t) => t.hash === hash);
  if (!found) return;
  CUR = JSON.parse(JSON.stringify(found));
  SEL = -1;
  history.replaceState(null, "", "#" + hash);  // 새로고침해도 이어보기

  $("#cur-hash").textContent = `${CUR.hash}  ·  ${CUR.system}  ·  ${(CUR.size || []).join("×")}`;
  $("#memo-input").value = CUR.memo || "";
  $("#btn-render").disabled = CUR.system === "manual";
  $("#btn-add").disabled = CUR.system === "manual";
  renderList();
  loadImage();
  renderProps();
  refreshVariantPanel();
}

function loadImage() {
  // NAT = region 좌표 기준 공간
  NAT = CUR.coord_size || CUR.size || [1, 1];
  // 베이스 = 원본 아트 (투명도 슬라이더). 한글은 SVG 오버레이로 표시.
  const tex = $("#tex-img");
  tex.onload = () => applyZoom();
  tex.src = `/api/image?path=${encodeURIComponent(CUR.source || CUR.png)}`;
  applyOrigOpacity();
}

function applyOrigOpacity() {
  const v = $("#orig-opacity").value;
  $("#tex-img").style.opacity = v / 100;
  $("#orig-opacity-val").textContent = v + "%";
}
function scheduleLive() { /* SVG 오버레이는 즉시 그려져 서버 렌더 불필요 */ }

function applyZoom() {
  const z = $("#zoom").value;
  const wrap = $("#canvas-wrap");
  let scale;
  if (z === "fit") {
    // 창에 맞춤 (가로·세로 모두). 이미지가 작으면 키워서 채움.
    const aw = wrap.clientWidth - 40;
    const ah = wrap.clientHeight - 40;
    scale = Math.max(0.05, Math.min(aw / NAT[0], ah / NAT[1]));
  } else {
    scale = parseFloat(z);
  }
  SCALE = scale;
  const wpx = NAT[0] * scale + "px", hpx = NAT[1] * scale + "px";
  for (const id of ["#tex-img", "#orig-img"]) {
    $(id).style.width = wpx; $(id).style.height = hpx;
  }
  $("#stage").style.width = wpx;
  $("#stage").style.height = hpx;
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
    el.innerHTML = `<span class="rlabel">${escapeHtml(r.id || "#" + i)}</span>`;
    el.appendChild(makeTextLayer(r, w, h));  // PIL 알고리즘 복제 캔버스 오버레이
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

// 그리운 경찰감성체 웹폰트로 region 텍스트를 캔버스에 근사 렌더 (정확한 출력은 생성 미리보기)
// place 레이아웃 → 캔버스 표시 방향:
//   horizontal=가로, vertical_columns/세로 박스=세로쌓기, rotated/넓은박스=글자 90° 눕혀 가로배열
function cssTextColor(r) {
  if (CUR.system === "place") return r.text_color === "white" ? "#fff" : "#000";
  const c = r.color || [255, 255, 255, 255];
  return `rgba(${c[0]},${c[1]},${c[2]},${(c[3] ?? 255) / 255})`;
}
function _measCtx() {
  return (window.__mc ||= document.createElement("canvas").getContext("2d"));
}
function _offNum(mode, avail, size) {  // 렌더러 _off와 동일 (넘침 음수 허용)
  if (mode === "left" || mode === "top") return 0;
  if (mode === "right" || mode === "bottom") return avail - size;
  return (avail - size) / 2;
}
function _rotateCanvas(src, deg) {  // PIL rotate(CCW 양수) 동일
  const d = ((deg % 360) + 360) % 360;
  const swap = d === 90 || d === 270;
  const out = document.createElement("canvas");
  out.width = Math.max(1, swap ? src.height : src.width);
  out.height = Math.max(1, swap ? src.width : src.height);
  const c = out.getContext("2d");
  c.translate(out.width / 2, out.height / 2);
  c.rotate(-deg * Math.PI / 180);  // canvas는 CW(+) → PIL CCW에 맞춰 -deg
  c.drawImage(src, -src.width / 2, -src.height / 2);
  return out;
}

// 캔버스로 PIL 렌더러(_render_aligned) 알고리즘을 그대로 복제 → 생성 결과와 거의 동일.
// 텍스트를 타이트 캔버스에 잉크 기준 렌더 → 회전 → 박스 안에 정렬 배치.
function makeTextLayer(r, w, h) {
  // blur region 은 글로우가 박스 밖으로 번지므로 캔버스를 대칭 패딩만큼 키우고 -pad 로 위치(위치 불변).
  const blur = parseFloat(r.blur) || 0;
  const pad = blur > 0 ? Math.ceil(blur * 3) + 8 : 0;
  const cw = Math.round(w + 2 * pad), ch = Math.round(h + 2 * pad);
  const cv = document.createElement("canvas");
  cv.width = Math.max(1, cw);
  cv.height = Math.max(1, ch);
  cv.className = "region-text";
  if (pad) {
    cv.style.inset = "auto";
    cv.style.left = (-pad * SCALE) + "px";
    cv.style.top = (-pad * SCALE) + "px";
    cv.style.overflow = "visible";
  }
  cv.style.width = cw * SCALE + "px";
  cv.style.height = ch * SCALE + "px";
  drawRegionTextCanvas(cv.getContext("2d"), r, w, h, pad);
  return cv;
}

function drawRegionTextCanvas(ctx, r, w, h, pad = 0) {
  const isLoc = CUR.system === "localize";
  let rot = parseInt(r.rotation) || 0;
  let layout = r.layout;
  if (layout === "rotated") { layout = "vertical"; if (!rot) rot = 90; }
  const align = isLoc ? (r.align || "left") : (r.align || "center");
  const valign = isLoc ? (r.v_align || "top") : (r.valign || "center");
  const isHoriz = (!layout || layout === "auto") ? (w >= h) : (layout === "horizontal");
  const padR = isLoc ? 0 : (r.padding ?? 0.08);
  const pxl = r.pad_x ?? w * padR, pyl = r.pad_y ?? h * padR;
  const innerW = Math.max(1, w - 2 * pxl), innerH = Math.max(1, h - 2 * pyl);
  const swap = Math.abs(rot) === 90;
  const lenBox = isHoriz ? (swap ? innerH : innerW) : (swap ? innerW : innerH);
  const crossBox = isHoriz ? (swap ? innerW : innerH) : (swap ? innerH : innerW);
  const txt = r.text || "";
  if (!txt) return;
  const cells = [...txt];
  const n = Math.max(1, cells.length);
  const ls = r.letter_spacing || 0;
  const fr = r.font_ratio || 0.85;
  const color = cssTextColor(r);
  // 외곽선
  const sw = Math.max(0, parseInt(r.outline_width) || 0);
  const oc = r.outline_color || [0, 0, 0, 255];
  const sCol = `rgba(${oc[0]|0},${oc[1]|0},${oc[2]|0},${((oc[3]??255)/255).toFixed(3)})`;
  // 외곽선이 잉크 박스 밖으로 sw만큼 확장됨 → 캔버스도 키워야 잘림 방지
  const sx2 = 2 * sw;

  const mc = _measCtx();
  // 절대 폰트 크기 (localize=font_size, place=font_px). 없으면 font_ratio 자동.
  const absSize = isLoc ? r.font_size : r.font_px;
  let temp;  // 타이트 텍스트 캔버스
  if (isHoriz) {
    let fs;
    if (absSize) fs = absSize;
    else {  // PIL: 폭·높이 둘 다 박스 안에 들어올 때까지 축소
      fs = Math.max(8, Math.round(crossBox * fr));
      while (fs > 8) {
        mc.font = `${fs}px Griun`; mc.letterSpacing = ls + "px";
        const m = mc.measureText(txt);
        const tw = ls ? m.width : (m.actualBoundingBoxLeft + m.actualBoundingBoxRight);
        const th = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
        if (tw <= lenBox && th <= crossBox) break;
        fs--;
      }
    }
    fs = Math.max(4, Math.round(fs));
    mc.font = `${fs}px Griun`; mc.letterSpacing = ls + "px";
    const m = mc.measureText(txt);
    const inkL = m.actualBoundingBoxLeft, inkA = m.actualBoundingBoxAscent, inkD = m.actualBoundingBoxDescent;
    // PIL: 타이트 캔버스 = 잉크 폭×높이. (자간 시엔 advance 폭 사용)
    const tw = Math.max(1, Math.ceil(ls ? m.width : (inkL + m.actualBoundingBoxRight)));
    const th = Math.max(1, Math.ceil(inkA + inkD));
    temp = document.createElement("canvas"); temp.width = tw + sx2; temp.height = th + sx2;
    const tc = temp.getContext("2d");
    tc.font = `${fs}px Griun`; tc.letterSpacing = ls + "px";
    tc.textBaseline = "alphabetic"; tc.textAlign = "left";
    const tx = (ls ? 0 : inkL) + sw, ty = inkA + sw;
    if (sw) {
      tc.strokeStyle = sCol; tc.lineWidth = sw * 2; tc.lineJoin = "round"; tc.miterLimit = 2;
      tc.strokeText(txt, tx, ty);
    }
    tc.fillStyle = color;
    tc.fillText(txt, tx, ty);
  } else {
    const cell0 = Math.max(1, Math.floor(lenBox / n));
    let fs = absSize || Math.max(8, Math.round(Math.min(crossBox, cell0) * fr));
    fs = Math.max(4, Math.round(fs));
    mc.font = `${fs}px Griun`; mc.letterSpacing = "0px";
    // 각 글자 잉크 메트릭 (PIL getbbox 대응)
    const met = {};
    let gw = 1;
    for (const ch of cells) {
      if (ch === " ") continue;
      const m = mc.measureText(ch);
      const il = m.actualBoundingBoxLeft, ir = m.actualBoundingBoxRight;
      met[ch] = { il, ir, ia: m.actualBoundingBoxAscent, id: m.actualBoundingBoxDescent };
      gw = Math.max(gw, il + ir);
    }
    gw = Math.ceil(gw);
    const pitch = cell0 + ls;  // PIL: pitch = cell0 + ls
    const offs = []; let acc = 0;
    for (const ch of cells) { offs.push(acc); acc += pitch * (ch === " " ? 0.5 : 1); }
    const blockLen = Math.max(cell0, Math.round(acc - ls));
    // fs>cell0(font_ratio>1) 일 때 첫/마지막 글자 잉크가 셀 밖으로 나감 → 캔버스 확장
    // 외곽선이 있으면 잉크 박스를 sw만큼 더 키워서 잘림 방지
    let iyMin = 0, iyMax = blockLen;
    cells.forEach((ch, i) => {
      if (ch === " ") return;
      const g = met[ch]; if (!g) return;
      const chh = g.ia + g.id;
      const top = offs[i] + cell0 / 2 - chh / 2 - sw;
      const bot = top + chh + sx2;
      if (top < iyMin) iyMin = top;
      if (bot > iyMax) iyMax = bot;
    });
    const yShift = -iyMin;
    const canvH = Math.max(blockLen, Math.ceil(iyMax - iyMin));
    temp = document.createElement("canvas"); temp.width = gw + sx2; temp.height = Math.max(1, canvH);
    const tc = temp.getContext("2d");
    tc.font = `${fs}px Griun`;
    tc.textBaseline = "alphabetic"; tc.textAlign = "left";
    if (sw) { tc.strokeStyle = sCol; tc.lineWidth = sw * 2; tc.lineJoin = "round"; tc.miterLimit = 2; }
    cells.forEach((ch, i) => {
      if (ch === " ") return;
      const g = met[ch]; if (!g) return;
      const cw = g.il + g.ir, chh = g.ia + g.id;
      // 잉크를 칸 중앙에 정렬 (PIL cx/cy 식과 동일)
      const x = (gw + sx2) / 2 - cw / 2 + g.il;
      const inkTop = offs[i] + cell0 / 2 - chh / 2 + yShift;
      const py = inkTop + g.ia;
      if (sw) tc.strokeText(ch, x, py);
      tc.fillStyle = color;
      tc.fillText(ch, x, py);
    });
  }

  const layer = rot ? _rotateCanvas(temp, rot) : temp;
  // pad(대칭) 만큼 밀어 캔버스 안에서 그리되 위치는 박스 기준 정렬 그대로 유지.
  const bx = pad + pxl + _offNum(align, innerW, layer.width);
  const by = pad + pyl + _offNum(valign, innerH, layer.height);
  const blurPx = parseFloat(r.blur) || 0;  // 캔버스가 native 해상도라 그대로 px
  if (blurPx > 0) ctx.filter = `blur(${blurPx}px)`;
  ctx.drawImage(layer, Math.round(bx), Math.round(by));
  if (blurPx > 0) ctx.filter = "none";
}

// 박스를 텍스처 범위 안으로 클램프 (영역 밖 이탈 방지)
function clampBox(b) {
  b[2] = Math.max(4, Math.min(b[2], NAT[0]));
  b[3] = Math.max(4, Math.min(b[3], NAT[1]));
  b[0] = Math.max(0, Math.min(b[0], NAT[0] - b[2]));
  b[1] = Math.max(0, Math.min(b[1], NAT[1] - b[3]));
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
    const nb = [Math.round(x), Math.round(y), Math.round(w), Math.round(h)];
    clampBox(nb);
    CUR.regions[i].box = nb;
    drawRegions();
    updateBoxFields();
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
    scheduleLive();  // 드래그 끝 → 실제 렌더 갱신
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

  // 시스템 공통 속성 패널 — localize 와 place 가 같은 항목을 보이도록 통일.
  // 시스템별 키 차이는 readProps 에서 매핑 (localize: color/v_align/font_size, place: text_color/valign/font_px).
  const isLoc = CUR.system === "localize";
  // 글씨 색 — 양쪽 모두 화이트/블랙 enum (단순화). localize 의 RGBA 는 자동 매핑.
  const colorVal = isLoc ? colorToName(r.color) : (r.text_color || "black");
  html += selField("text_color", "글씨 색", colorVal, [["black", "블랙"], ["white", "화이트"]]);
  if (isLoc) html += sliderField("text_alpha", "글씨 투명도 %", rgbaAlphaPct(r.color || [255, 255, 255, 255]), 0, 100, 1);
  // 배경 색 / 처리 — 같은 enum 으로 통합. localize 는 clear=true ↔ clear_alpha 로 매핑.
  let bgVal;
  if (isLoc) bgVal = r.clear ? "clear_alpha" : "transparent";
  else bgVal = r.background || "transparent";
  html += selField("background", "배경 색", bgVal,
    [["transparent", "투명"], ["black", "블랙"], ["red", "지명 레드"],
     ["clear_alpha", "기존 영역 삭제"], ["clear_white", "흰 글자 제거"]]);
  // 쓰기 방향 — localize 도 layout 지원 (default horizontal)
  html += selField("layout", "쓰기 방향", r.layout || (isLoc ? "horizontal" : "auto"),
    [["auto", "자동"], ["horizontal", "가로쓰기"], ["vertical", "세로쓰기"], ["vertical_columns", "세로쓰기(열)"], ["rotated", "회전 90°(세로배너)"]]);
  html += selField("rotation", "회전", String(r.rotation || 0),
    [["0", "0°"], ["90", "90°"], ["-90", "-90°"], ["180", "180°"]]);
  // 정렬 — localize 는 v_align 키 사용. UI 는 valign 으로 통일하고 readProps 에서 둘 다 기록.
  const valignVal = isLoc ? (r.v_align || "center") : (r.valign || "center");
  html += `<div class="field-row">
    <div>${selField("align", "가로 정렬", r.align || "center", [["left", "왼쪽"], ["center", "가운데"], ["right", "오른쪽"]])}</div>
    <div>${selField("valign", "세로 정렬", valignVal, [["top", "위"], ["center", "가운데"], ["bottom", "아래"]])}</div></div>`;
  html += sliderField("font_ratio", "글씨 비율", r.font_ratio ?? 0.85, 0.1, 1.5, 0.01);
  // 글씨 크기 — localize 는 font_size (절대값 권장), place 는 font_px (0=비율)
  const fsVal = isLoc ? (r.font_size || 0) : (r.font_px || 0);
  html += field("font_px", "글씨 크기(px, 0=비율 사용)", `<input type="number" data-k="font_px" value="${fsVal}">`);
  html += sliderField("letter_spacing", "자간 (px)", r.letter_spacing || 0, -20, 120, 1);
  html += `<div class="field-row">
    <div>${sliderField("pad_x", "좌우 여백(px)", r.pad_x ?? 0, 0, 200, 1)}</div>
    <div>${sliderField("pad_y", "상하 여백(px)", r.pad_y ?? 0, 0, 200, 1)}</div></div>`;
  html += outlineFields(r);
  html += sliderField("blur", "블러 (px, 0=없음)", r.blur || 0, 0, 80, 1);
  if (isLoc) html += checkField("fit_to_box", "박스에 맞춰 축소", r.fit_to_box);
  html += checkField("render", "이 영역 렌더링", r.render !== false);
  form.innerHTML = html;
  form.oninput = onFormInput;
  form.onchange = onFormInput;
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
function sliderField(k, label, val, min, max, step) {
  return `<div class="field"><label>${label} <span class="muted" data-out="${k}">${val}</span></label>
    <div class="slider-row">
      <input type="range" min="${min}" max="${max}" step="${step}" value="${val}" data-slider="${k}">
      <input type="number" step="${step}" value="${val}" data-k="${k}" data-num="${k}">
    </div></div>`;
}
function colorToName(c) {
  if (Array.isArray(c) && c[0] < 128 && c[1] < 128 && c[2] < 128) return "black";
  return "white";
}
function rgbaToHex(c) {
  if (!Array.isArray(c) || c.length < 3) return "#000000";
  const h = (n) => Math.max(0, Math.min(255, n|0)).toString(16).padStart(2, "0");
  return "#" + h(c[0]) + h(c[1]) + h(c[2]);
}
function rgbaAlphaPct(c) {
  if (!Array.isArray(c) || c.length < 4) return 100;
  return Math.round((c[3] / 255) * 100);
}
function hexAlphaToRgba(hex, alphaPct) {
  const h = (hex || "#000000").replace("#", "");
  const r = parseInt(h.slice(0, 2), 16) || 0;
  const g = parseInt(h.slice(2, 4), 16) || 0;
  const b = parseInt(h.slice(4, 6), 16) || 0;
  const a = Math.round(Math.max(0, Math.min(100, +alphaPct || 0)) * 2.55);
  return [r, g, b, a];
}
// 외곽선 속성 (색 + 투명도 + 두께). 두께=0이면 외곽선 없음.
function outlineFields(r) {
  const hex = rgbaToHex(r.outline_color || [0, 0, 0, 255]);
  const ap = rgbaAlphaPct(r.outline_color || [0, 0, 0, 255]);
  const w = r.outline_width || 0;
  return `<div class="outline-box">
    <label style="color:#b8bcc6; font-size:11px; display:block; margin-bottom:6px;">외곽선</label>
    <div class="outline-row">
      <div class="color-cell">
        <label>색</label>
        <input type="color" data-k="outline_hex" value="${hex}" title="외곽선 색">
      </div>
      <div class="alpha-cell">${sliderField("outline_alpha", "투명도 %", ap, 0, 100, 1)}</div>
    </div>
    ${sliderField("outline_width", "두께 (px, 0=없음)", w, 0, 20, 1)}
  </div>`;
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
  clampBox(r.box);  // 영역 밖 이탈 방지
  // fields — 시스템별 키 매핑 (UI 는 통일, 데이터는 native 키로 변환)
  const isLoc = CUR.system === "localize";
  $$("[data-k]").forEach((el) => {
    const k = el.dataset.k;
    const v = el.type === "checkbox" ? el.checked : el.value;
    if (k === "text_color") {
      if (isLoc) {
        const a = (Array.isArray(r.color) && r.color.length > 3) ? r.color[3] : 255;
        r.color = v === "black" ? [0, 0, 0, a] : [255, 255, 255, a];  // 알파 보존
      } else r.text_color = v;
    } else if (k === "text_alpha") {
      if (isLoc) {
        const c = Array.isArray(r.color) ? r.color.slice() : [255, 255, 255, 255];
        c[3] = Math.round(Math.max(0, Math.min(100, parseFloat(v) || 0)) * 2.55);
        r.color = c;
      }
    } else if (k === "background") {
      if (isLoc) {
        // localize 는 clear true/false 만 표현 가능 → clear_alpha/clear_white 는 clear=true 로 매핑
        r.clear = (v === "clear_alpha" || v === "clear_white");
        r.background = v;  // place 호환용도 같이 기록
      } else {
        r.background = v;
      }
    } else if (k === "valign") {
      if (isLoc) r.v_align = v;
      else r.valign = v;
    } else if (k === "letter_spacing") {
      r.letter_spacing = parseInt(v) || 0;
    } else if (k === "rotation") {
      r.rotation = parseInt(v) || 0;
    } else if (k === "font_px") {
      const n = parseInt(v);
      // 0 = 비율 사용 (font_ratio 모드). localize 는 font_size, place 는 font_px 키
      if (isLoc) r.font_size = n > 0 ? n : null;
      else r.font_px = n > 0 ? n : null;
    } else if (k === "pad_x" || k === "pad_y") {
      const n = parseInt(v);
      r[k] = n > 0 ? n : null;
    } else if (k === "font_ratio" || k === "padding") {
      r[k] = parseFloat(v) || 0;
    } else if (k === "blur") {
      r.blur = parseFloat(v) || 0;
    } else if (k === "outline_width") {
      r.outline_width = parseInt(v) || 0;
    } else if (k === "outline_alpha" || k === "outline_hex") {
      // 색·투명도는 한 RGBA로 합쳐 저장
      const form = $("#props-form");
      const hex = form.querySelector('[data-k="outline_hex"]')?.value || "#000000";
      const ap = form.querySelector('[data-k="outline_alpha"]')?.value ?? 100;
      r.outline_color = hexAlphaToRgba(hex, ap);
    } else {
      r[k] = v;
    }
  });
  drawRegions();
  scheduleLive();  // 속성 변경 → 실제 렌더 갱신(디바운스)
}

// 슬라이더↔숫자 동기화 + 출력 라벨 갱신
function onFormInput(e) {
  const t = e.target;
  const form = $("#props-form");
  if (t.dataset.slider) {
    const num = form.querySelector(`[data-num="${t.dataset.slider}"]`);
    if (num) num.value = t.value;
  } else if (t.dataset.num) {
    const sl = form.querySelector(`[data-slider="${t.dataset.num}"]`);
    if (sl) sl.value = t.value;
  }
  const key = t.dataset.slider || t.dataset.num || t.dataset.k;
  if (key) {
    const out = form.querySelector(`[data-out="${key}"]`);
    if (out) out.textContent = t.value;
  }
  // 글씨 비율을 조정하면 글씨 크기(px) 오버라이드 해제 → 비율 적용
  if (key === "font_ratio") {
    const fpx = form.querySelector('[data-k="font_px"]');
    if (fpx) fpx.value = 0;
  }
  readProps();
}

// ===== 액션 =====
function addRegion() {
  if (!CUR || CUR.system === "manual") return;
  const cx = Math.round(NAT[0] / 4), cy = Math.round(NAT[1] / 4);
  const base = { box: [cx, cy, Math.round(NAT[0] / 4), Math.round(NAT[1] / 8)], text: "텍스트" };
  // 흔한 패턴으로 default 통일 (전체 region 빈도 분석 기반):
  // localize는 4AEC2546 기준(흰글씨+검정외곽선, clear/fit_to_box=false)
  // place는 528 region 다수결(horizontal/white/0.85/center, transparent bg)
  if (CUR.system === "localize") {
    Object.assign(base, {
      font_size: 48,
      color: [255, 255, 255, 255],
      align: "center",
      v_align: "center",
      clear: false,
      fit_to_box: false,
      letter_spacing: 0,
      outline_width: 3,
      outline_color: [0, 0, 0, 255],
    });
  } else {
    Object.assign(base, {
      text_color: "white",
      background: "transparent",
      layout: "horizontal",
      padding: 0.08,
      font_ratio: 0.85,
      letter_spacing: 0,
      align: "center",
      valign: "center",
      rotation: 0,
      outline_width: 0,
      outline_color: [0, 0, 0, 255],
      render: true,
    });
  }
  CUR.regions.push(base);
  SEL = CUR.regions.length - 1;
  drawRegions();
  renderProps();
}

async function applyRegions() {
  if (SEL >= 0) readProps();
  const res = await api("/api/regions", { hash: CUR.hash, system: CUR.system, regions: CUR.regions });
  if (!res.ok) { toast(res.error || "저장 실패", true); return false; }
  INDEX = await api("/api/index");
  const fresh = INDEX.textures.find((t) => t.hash === CUR.hash);
  if (fresh) { CUR = JSON.parse(JSON.stringify(fresh)); SEL = Math.min(SEL, CUR.regions.length - 1); }
  renderList();
  return true;
}

// 스타일 복사/붙여넣기 (글씨색·배경색·쓰기방향·정렬·비율·자간·여백만; 텍스트·박스 제외)
let STYLE_CLIP = null;
const STYLE_FIELDS = ["text_color", "background", "layout", "rotation", "align", "valign",
  "font_ratio", "letter_spacing", "pad_x", "pad_y", "font_px",  // place
  "color", "v_align", "clear", "fit_to_box", "font_size",       // localize 대응
  "outline_width", "outline_color"];                            // 외곽선 (공통)
function copyStyle() {
  if (SEL < 0 || !CUR.regions[SEL]) return;
  const r = CUR.regions[SEL];
  STYLE_CLIP = {};
  for (const k of STYLE_FIELDS) if (k in r) STYLE_CLIP[k] = r[k];
  toast("스타일 복사됨");
}
function pasteStyle() {
  if (SEL < 0 || !CUR.regions[SEL]) return;
  if (!STYLE_CLIP) { toast("복사된 스타일이 없습니다", true); return; }
  Object.assign(CUR.regions[SEL], JSON.parse(JSON.stringify(STYLE_CLIP)));
  drawRegions();
  renderProps();
  toast("스타일 붙여넣기 완료");
}

function delRegion() {
  if (SEL < 0) return;
  CUR.regions.splice(SEL, 1);
  SEL = -1;
  drawRegions(); renderProps();
  toast("영역 삭제됨 (저장 및 미리보기로 반영)");
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
  $("#spinner").hidden = false;  // 생성 중 스피너
  try {
    // 1) 전체 영역을 config에 저장 → 2) 실제 textures/kr 이미지 생성
    if (!(await applyRegions())) return;
    const res = await api("/api/render", { hash: CUR.hash, system: CUR.system });
    if (res.ok) {
      $("#modal-title").textContent = `생성 완료: ${res.path}`;
      $("#modal-img").src = `/api/image?path=${encodeURIComponent(res.path)}&t=${Date.now()}`;
      $("#modal-log").textContent = res.log || "";
      $("#modal").hidden = false;
      // 배경 레이어(원본)와 목록 썸네일도 갱신
      renderList();
    } else {
      toast(res.error || "생성 실패", true);
      $("#modal-log").textContent = res.error || "";
    }
  } finally {
    $("#spinner").hidden = true;
  }
}

// ===== ✕ 버튼 변형 (이슈 #12) =====
let VT_CAVEAT = "";
async function refreshVariantPanel() {
  if (!CUR) { $("#variant-panel").hidden = true; return; }
  $("#variant-panel").hidden = false;
  const info = await api(`/api/button_variants?hash=${encodeURIComponent(CUR.hash)}`);
  VT_CAVEAT = info.caveat || "";
  $("#vt-caveat").textContent = VT_CAVEAT;
  const sel = info.selected;
  const included = !!sel;
  $("#vt-include").checked = included;
  $("#vt-body").hidden = !included;
  if (included) {
    $("#vt-memo").value = sel.memo || "";
    $("#vt-noop").hidden = sel.has_ops;
    const bust = "&t=" + Date.now();
    $("#vt-base").src = `/api/image?path=${encodeURIComponent(sel.base_png)}${bust}`;
    $("#vt-variant").src = sel.variant_png
      ? `/api/image?path=${encodeURIComponent(sel.variant_png)}${bust}`
      : "";
  }
}
async function vtToggle() {
  const include = $("#vt-include").checked;
  const res = await api("/api/button_variant_toggle",
    { hash: CUR.hash, include, label: (CUR.memo || CUR.hash) });
  if (!res.ok) { toast(res.error || "실패", true); return; }
  if (include) await api("/api/button_variant_build", { hash: CUR.hash });
  toast(include ? "✕ 변형 대상에 추가" : "✕ 변형 대상에서 제거");
  refreshVariantPanel();
}
async function vtSaveMemo() {
  const res = await api("/api/button_variant_memo", { hash: CUR.hash, memo: $("#vt-memo").value });
  toast(res.ok ? "✕ 변형 메모 저장됨" : (res.error || "실패"), !res.ok);
}
async function vtRebuild() {
  $("#spinner").hidden = false;
  try {
    const res = await api("/api/button_variant_build", { hash: CUR.hash });
    if (res.ok) { toast("✕판 재생성 완료"); refreshVariantPanel(); }
    else toast(res.error || "재생성 실패", true);
  } finally { $("#spinner").hidden = true; }
}
async function vtExport() {
  $("#spinner").hidden = false;
  try {
    const res = await api("/api/button_variant_export", {});
    $("#modal-title").textContent = res.ok ? `✕ 추가팩 생성: ${res.zip}` : "✕ 추가팩 내보내기 실패";
    $("#modal-img").src = "";
    $("#modal-log").textContent = res.log || "";
    $("#modal").hidden = false;
    toast(res.ok ? "✕ 추가팩 zip 생성됨 (dist/)" : "내보내기 실패", !res.ok);
  } finally { $("#spinner").hidden = true; }
}

// ===== 초기화 =====
async function init() {
  // 캔버스 measureText/fillText 가 폴백 폰트를 쓰지 않도록 Griun 선로딩
  try { await document.fonts.load('100px Griun'); } catch (e) {}
  document.fonts.ready.then(() => { if (CUR) drawRegions(); });  // 늦게 로드돼도 재그림
  INDEX = await api("/api/index");
  renderList();
  $("#search").oninput = renderList;
  $$(".sysfilter").forEach((c) => (c.onchange = renderList));
  $("#bg-color").onchange = () => {
    $("#stage").className = "bg-" + $("#bg-color").value;
  };
  $("#bg-color").onchange();
  $("#zoom").onchange = applyZoom;
  // 원본 투명도 슬라이더 = 배경 레이어(원본 아트) opacity만. 텍스트 오버레이는 그대로
  $("#orig-opacity").oninput = applyOrigOpacity;
  $("#btn-add").onclick = addRegion;
  $("#btn-del").onclick = delRegion;
  $("#btn-copy-style").onclick = copyStyle;
  $("#btn-paste-style").onclick = pasteStyle;
  $("#btn-memo").onclick = saveMemo;
  $("#btn-render").onclick = renderPreview;
  $("#vt-include").onchange = vtToggle;
  $("#vt-memo-save").onclick = vtSaveMemo;
  $("#vt-rebuild").onclick = vtRebuild;
  $("#vt-export").onclick = vtExport;
  $("#modal-close").onclick = () => ($("#modal").hidden = true);
  $("#modal").onclick = (e) => { if (e.target.id === "modal") $("#modal").hidden = true; };
  $$(".modal-bgsel button").forEach((b) => (b.onclick = () => {
    $$(".modal-bgsel button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("#modal-imgwrap").className = "bg-" + b.dataset.bg;
  }));
  // 방향키로 선택된 영역 이동 (Shift = 크게). 입력창 포커스 시엔 제외.
  document.addEventListener("keydown", (e) => {
    if (SEL < 0 || !CUR || !CUR.regions[SEL]) return;
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    const step = e.shiftKey ? 10 : 1;
    let dx = 0, dy = 0;
    if (e.key === "ArrowLeft") dx = -step;
    else if (e.key === "ArrowRight") dx = step;
    else if (e.key === "ArrowUp") dy = -step;
    else if (e.key === "ArrowDown") dy = step;
    else return;
    e.preventDefault();
    const b = CUR.regions[SEL].box;
    b[0] += dx; b[1] += dy;
    clampBox(b);
    drawRegions();
    updateBoxFields();
  });
  window.addEventListener("resize", () => { if (CUR) applyZoom(); });
  $("#overlay").onmousedown = (e) => { if (e.target.id === "overlay") { SEL = -1; drawRegions(); renderProps(); } };
  // URL 해시(#hash)로 마지막 편집 텍스처 복원 (핸들러 준비 후)
  const h = decodeURIComponent(location.hash.slice(1));
  if (h && INDEX.textures.some((t) => t.hash === h)) selectTexture(h);
}

init();
