#!/usr/bin/env python3
"""Rank unregistered Muramasa texture hashes that look like untranslated text art.

Scans the UHD texture pack and Vita3K export directory, skips hashes already
registered in the localization configs, then scores two signatures:

* place-name textures: transparent, alpha-driven brush/calligraphy text in a
  landscape band, sometimes with a thin rectangular box.
* DLC ending textures: 1024x1024 illustrations with a "完"-like alpha cluster
  in the lower-left corner.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage


REPO = Path(__file__).resolve().parents[1]
UHD_DIR = Path("/Users/tarucy/Downloads/Muramasa Complete 2.0/PCSE00240/Best")
EXPORT_DIR = Path(
    "/Users/tarucy/Library/Application Support/Vita3K/Vita3K/textures/export/PCSE00240"
)
ENDING_REFS: list[np.ndarray] = []


@dataclass
class Candidate:
    hash: str
    path: Path
    sources: list[str]
    size: tuple[int, int]
    alpha_pct: float
    score: float
    reason: str


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def registered_hashes() -> set[str]:
    hashes: set[str] = set()

    place = load_json(REPO / "translations/place_texture_jobs.json")
    hashes.update(h.upper() for h in place.get("textures", {}).keys())

    config = load_json(REPO / "translations/texture_localize_config.json")
    for item in config.get("textures", []):
        h = item.get("hash")
        if h:
            hashes.add(h.upper())

    index = load_json(REPO / "translations/ui_editor_index.json")
    for item in index.get("textures", []):
        if item.get("system") == "manual" and item.get("hash"):
            hashes.add(item["hash"].upper())

    return hashes


def iter_pngs() -> Iterable[tuple[str, Path, str]]:
    for label, root in (("uhd", UHD_DIR), ("export", EXPORT_DIR)):
        for path in sorted(root.glob("*.png")):
            yield path.stem.upper(), path, label


def collect_inputs(skip: set[str]) -> dict[str, tuple[Path, list[str]]]:
    by_hash: dict[str, tuple[Path, list[str]]] = {}
    for h, path, source in iter_pngs():
        if h in skip:
            continue
        if h not in by_hash:
            by_hash[h] = (path, [source])
        else:
            by_hash[h][1].append(source)
    return by_hash


def span_for_mass(values: np.ndarray, mass: float = 0.80) -> float:
    total = float(values.sum())
    if total <= 0:
        return 1.0
    target = total * mass
    left = 0
    acc = 0.0
    best = len(values)
    for right, value in enumerate(values):
        acc += float(value)
        while left <= right and acc - float(values[left]) >= target:
            acc -= float(values[left])
            left += 1
        if acc >= target:
            best = min(best, right - left + 1)
    return best / max(1, len(values))


def component_stats(mask: np.ndarray) -> tuple[int, float, float]:
    if not mask.any():
        return 0, 0.0, 0.0
    labels, count = ndimage.label(mask)
    if count == 0:
        return 0, 0.0, 0.0
    areas = np.bincount(labels.ravel())[1:]
    total = float(areas.sum())
    large = int((areas >= max(8, total * 0.002)).sum())
    largest = float(areas.max() / total)
    tiny_frac = float(areas[areas < max(4, total * 0.0005)].sum() / total)
    return large, largest, tiny_frac


def rectangular_label_stats(mask: np.ndarray) -> tuple[int, float]:
    """Return count/score for solid elongated rectangular label-like components."""
    if not mask.any():
        return 0, 0.0
    labels, count = ndimage.label(mask)
    if count == 0:
        return 0, 0.0
    objects = ndimage.find_objects(labels)
    good = 0
    best = 0.0
    img_area = mask.shape[0] * mask.shape[1]
    for idx, slc in enumerate(objects, 1):
        if slc is None:
            continue
        ys, xs = slc
        bh = ys.stop - ys.start
        bw = xs.stop - xs.start
        if bw < 18 or bh < 8:
            continue
        area = int((labels[slc] == idx).sum())
        if area < img_area * 0.00035:
            continue
        fill = area / max(1, bw * bh)
        elong = max(bw / max(1, bh), bh / max(1, bw))
        if fill >= 0.28 and elong >= 2.2:
            good += 1
            best = max(best, min(1.0, fill) * min(6.0, elong) * min(1.0, area / (img_area * 0.01)))
    return good, best


def resample_mask(mask: np.ndarray, max_side: int = 384) -> np.ndarray:
    h, w = mask.shape
    scale = min(1.0, max_side / max(h, w))
    if scale >= 1.0:
        return mask
    im = Image.fromarray(mask.astype("uint8") * 255)
    im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.NEAREST)
    return np.array(im) > 0


def load_rgba_for_scoring(path: Path, max_side: int = 1024) -> tuple[Image.Image, tuple[int, int]] | None:
    try:
        img = Image.open(path)
    except Exception:
        return None
    original_size = img.size
    img = img.convert("RGBA")
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.Resampling.BOX)
    return img, original_size


def place_score(path: Path) -> Candidate | None:
    loaded = load_rgba_for_scoring(path, 1024)
    if loaded is None:
        return None
    img, original_size = loaded
    w, h = img.size
    if w < 128 or h < 64:
        return None

    arr = np.asarray(img)
    alpha = arr[..., 3]
    mask = alpha > 8
    alpha_pct = float(mask.mean() * 100)
    if alpha_pct < 4 or alpha_pct > 78:
        return None

    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    bw, bh = x1 - x0, y1 - y0
    aspect = w / h
    bbox_aspect = bw / max(1, bh)
    bbox_area = (bw * bh) / (w * h)

    row_span80 = span_for_mass(alpha.sum(axis=1), 0.80)
    col_span80 = span_for_mass(alpha.sum(axis=0), 0.80)
    visible = arr[mask][..., :3].astype(np.int16)
    mean_rgb = visible.mean(axis=1)
    channel_spread = visible.max(axis=1) - visible.min(axis=1)
    white_frac = float(((mean_rgb > 170) & (channel_spread < 55)).mean())
    red_frac = float(((visible[:, 0] > 105) & (visible[:, 1] < 105) & (visible[:, 2] < 105)).mean())
    dark_frac = float((mean_rgb < 60).mean())

    red_mask = mask & (arr[..., 0] > 105) & (arr[..., 1] < 105) & (arr[..., 2] < 105)
    dark_mask = mask & (arr[..., :3].mean(axis=2) < 60)
    red_rects, red_rect_score = rectangular_label_stats(red_mask)
    dark_rects, dark_rect_score = rectangular_label_stats(dark_mask)
    rect_score = red_rect_score + dark_rect_score

    sample_mask = resample_mask(mask, 384)
    large_components, largest_component, tiny_frac = component_stats(sample_mask)

    score = 0.0
    reasons: list[str] = []

    if aspect >= 1.45:
        score += min(24.0, 10.0 + (aspect - 1.45) * 7.0)
        reasons.append("landscape")
    elif aspect >= 0.90 and w >= 1024:
        score += 6.0
        reasons.append("large atlas")
    else:
        score -= 14.0

    if 12 <= alpha_pct <= 55:
        score += 22.0 - abs(alpha_pct - 30.0) * 0.35
        reasons.append(f"alpha {alpha_pct:.1f}%")
    elif 6 <= alpha_pct < 12 or 55 < alpha_pct <= 70:
        score += 5.0
        reasons.append(f"borderline alpha {alpha_pct:.1f}%")
    else:
        score -= 8.0

    if 0.18 <= row_span80 <= 0.68:
        score += 18.0 - abs(row_span80 - 0.38) * 20.0
        reasons.append("horizontal band")
    elif row_span80 < 0.18:
        score += 4.0
    else:
        score -= 8.0

    if bbox_aspect >= 1.25:
        score += min(16.0, bbox_aspect * 4.0)
        reasons.append("wide content")
    else:
        score -= 4.0

    if 0.15 <= bbox_area <= 0.82:
        score += 8.0
    elif bbox_area > 0.90:
        score -= 10.0

    if white_frac >= 0.45:
        score += min(10.0, white_frac * 14.0)
        reasons.append("mostly white strokes")
    elif dark_frac >= 0.40 and white_frac < 0.15:
        score -= 10.0

    if red_frac >= 0.08 and dark_frac >= 0.12:
        score += 38.0
        reasons.append("red/black place-label colors")
    elif red_frac >= 0.08:
        score += 18.0
        reasons.append("red label color")
    elif red_frac < 0.01 and dark_frac < 0.04 and white_frac > 0.70:
        score -= 50.0
        reasons.append("white effect-like alpha")

    if red_rects and dark_rects:
        score += 55.0 + min(20.0, rect_score * 6.0)
        reasons.append(f"solid red/black label boxes ({red_rects}+{dark_rects})")
    elif red_rects:
        score += 18.0 + min(12.0, red_rect_score * 4.0)
        reasons.append(f"solid red label box ({red_rects})")
    elif dark_rects:
        score += 12.0 + min(10.0, dark_rect_score * 4.0)
        reasons.append(f"solid black label box ({dark_rects})")
    else:
        score -= 70.0
        reasons.append("no solid label rectangle")

    if 1 <= large_components <= 18 and largest_component >= 0.05:
        score += 10.0
        reasons.append(f"{large_components} major alpha components")
    elif large_components > 45:
        score -= 22.0
        reasons.append("many atlas-like components")
    elif tiny_frac > 0.45:
        score -= 12.0

    # Sprite/effect atlases commonly spread content evenly across both axes.
    if row_span80 > 0.78 and col_span80 > 0.78 and large_components > 18:
        score -= 28.0
        reasons.append("diffuse sprite/effect atlas")

    reason = ", ".join(reasons[:6])
    return Candidate(path.stem.upper(), path, [], original_size, alpha_pct, score, reason)


def load_ending_reference_masks() -> list[np.ndarray]:
    masks: list[np.ndarray] = []
    for ref in sorted((REPO / "temp/dlc_ftx_png").glob("pack*/GUI/Ending_P*.png")):
        img = Image.open(ref).convert("RGBA")
        arr = np.asarray(img)
        # The 完 mark is in the lower-left quadrant; derive a loose dark/bright
        # stroke mask and crop to the left/lower region for correlation.
        crop = arr[430:900, 0:360, :]
        rgb = crop[..., :3].astype(np.int16)
        a = crop[..., 3]
        mean = rgb.mean(axis=2)
        spread = rgb.max(axis=2) - rgb.min(axis=2)
        mask = (a > 20) & (((mean < 80) | (mean > 175)) & (spread < 95))
        mask = ndimage.binary_opening(mask, iterations=1)
        if mask.any():
            im = Image.fromarray(mask.astype("uint8") * 255).resize((96, 128), Image.Resampling.BILINEAR)
            masks.append(np.asarray(im) > 80)
    return masks


def init_worker(refs: list[np.ndarray]) -> None:
    global ENDING_REFS
    ENDING_REFS = refs


def score_one(item: tuple[str, str, list[str]]) -> tuple[Candidate | None, Candidate | None]:
    _hash, path_str, sources = item
    path = Path(path_str)
    place = place_score(path)
    if place:
        place.sources = sources
    ending = ending_score(path, ENDING_REFS)
    if ending:
        ending.sources = sources
    return place, ending


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 0.0


def ending_score(path: Path, refs: list[np.ndarray]) -> Candidate | None:
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None
    if img.size != (1024, 1024):
        return None

    arr = np.asarray(img)
    alpha = arr[..., 3]
    alpha_pct = float((alpha > 8).mean() * 100)
    crop = arr[430:900, 0:360, :]
    rgb = crop[..., :3].astype(np.int16)
    a = crop[..., 3]
    mean = rgb.mean(axis=2)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    mask = (a > 20) & (((mean < 85) | (mean > 175)) & (spread < 110))
    mask = ndimage.binary_opening(mask, iterations=1)
    cov = float(mask.mean())
    if cov < 0.012 or cov > 0.42:
        return None

    labels, count = ndimage.label(mask)
    areas = np.bincount(labels.ravel())[1:] if count else np.array([])
    largest = float(areas.max() / mask.size) if len(areas) else 0.0
    compact_count = int((areas >= mask.size * 0.006).sum()) if len(areas) else 0

    im = Image.fromarray(mask.astype("uint8") * 255).resize((96, 128), Image.Resampling.BILINEAR)
    small = np.asarray(im) > 80
    corr = max((jaccard(small, ref) for ref in refs), default=0.0)

    score = corr * 70.0
    score += min(16.0, cov * 80.0)
    if 1 <= compact_count <= 8:
        score += 10.0
    if largest > 0.025:
        score += 8.0

    if score < 70.0:
        return None
    reason = f"1024x1024, lower-left stroke cluster cov {cov*100:.1f}%, ref overlap {corr:.2f}"
    return Candidate(path.stem.upper(), path, [], img.size, alpha_pct, score, reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    skip = registered_hashes()
    inputs = collect_inputs(skip)
    refs = load_ending_reference_masks()

    work = [(h, str(path), sources) for h, (path, sources) in sorted(inputs.items())]
    place_candidates: list[Candidate] = []
    ending_candidates: list[Candidate] = []
    workers = max(1, min(8, (os.cpu_count() or 2) - 1))
    with ProcessPoolExecutor(max_workers=workers, initializer=init_worker, initargs=(refs,)) as pool:
        for place, ending in pool.map(score_one, work, chunksize=16):
            if place:
                place_candidates.append(place)
            if ending:
                ending_candidates.append(ending)

    place_candidates.sort(key=lambda c: c.score, reverse=True)
    ending_candidates.sort(key=lambda c: c.score, reverse=True)

    print(f"Scanned non-registered PNG hashes: {len(inputs)}")
    print(f"Registered hashes skipped: {len(skip)}")
    print()
    print(f"TOP {args.top} PLACE-NAME CANDIDATES")
    print("rank  hash              size        alpha%  source      score  reason")
    for i, c in enumerate(place_candidates[: args.top], 1):
        source = "+".join(c.sources)
        print(
            f"{i:>2}.   {c.hash:<16}  {c.size[0]}x{c.size[1]:<5}  "
            f"{c.alpha_pct:>6.2f}  {source:<10}  {c.score:>5.1f}  {c.reason}"
        )

    print()
    print("DLC ENDING CANDIDATES")
    if not ending_candidates:
        print("none found in UHD/export")
    else:
        print("rank  hash              size        alpha%  source      score  reason")
        for i, c in enumerate(ending_candidates, 1):
            source = "+".join(c.sources)
            print(
                f"{i:>2}.   {c.hash:<16}  {c.size[0]}x{c.size[1]:<5}  "
                f"{c.alpha_pct:>6.2f}  {source:<10}  {c.score:>5.1f}  {c.reason}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
