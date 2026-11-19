#!/usr/bin/env python3
"""Moteur T3 — master silencieux 30 s, 720×1280, 30 i/s, 900 images.

Le moteur reconstruit de manière originale toutes les familles observées dans
les références CapCut 2 et 4. Il ne copie aucun média de ces références. Les
seuls médias d'entrée sont quatre rushes Pexels documentés et vérifiés.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from engine.text_motion import normalize_payload, render_text_motion, typography_audit, validate_text_config, visible_text_contract
except ModuleNotFoundError:  # exécution directe: python engine/render_silent.py
    from text_motion import normalize_payload, render_text_motion, typography_audit, validate_text_config, visible_text_contract

W, H, FPS, TOTAL = 720, 1280, 30, 900
ENGINE_VERSION = "1.2.0-borderless-panels"
ORANGE = (37, 82, 236)  # BGR #EC5225
AMBER = (59, 181, 247)
CREAM = (236, 247, 255)
DARK = (10, 8, 7)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ffmpeg_binary() -> str:
    if os.environ.get("FFMPEG_BIN"):
        return os.environ["FFMPEG_BIN"]
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - message for runtime setup
        raise SystemExit("FFmpeg introuvable. Installez ffmpeg ou imageio-ffmpeg.") from exc


def run(command: list[str]) -> None:
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def preprocess_scene(ffmpeg: str, source: Path, destination: Path, scene: dict[str, Any]) -> None:
    frames = int(scene["duration_seconds"] * FPS)
    bias = float(scene.get("crop_x_bias", 0.0))
    x_expr = f"(iw-ow)/2+({bias:.6f})*(iw-ow)/2"
    vf = (
        "scale=-2:1280:flags=lanczos,"
        f"crop=720:1280:{x_expr}:(ih-oh)/2,"
        "fps=30,"
        "eq=contrast=1.045:saturation=1.09:brightness=0.008,"
        "unsharp=5:5:0.32:5:5:0.0,"
        "setpts=PTS-STARTPTS"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source),
        "-ss", f"{float(scene['trim_start_seconds']):.6f}",
        "-vf", vf,
        "-frames:v", str(frames),
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
        "-pix_fmt", "yuv420p", str(destination),
    ])
    cap = cv2.VideoCapture(str(destination))
    actual = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if (actual, width, height) != (frames, W, H):
        raise RuntimeError(f"Intermédiaire invalide {destination}: {(actual, width, height)}")


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def smooth(x: float) -> float:
    x = clamp01(x)
    return x * x * (3.0 - 2.0 * x)


def ease_out(x: float) -> float:
    x = clamp01(x)
    return 1.0 - (1.0 - x) ** 3


def mix(a: np.ndarray, b: np.ndarray, alpha: float) -> np.ndarray:
    alpha = clamp01(alpha)
    return cv2.addWeighted(a, 1.0 - alpha, b, alpha, 0.0)


def tint(frame: np.ndarray, bgr: tuple[int, int, int], alpha: float) -> np.ndarray:
    color = np.empty_like(frame)
    color[:, :] = bgr
    return mix(frame, color, alpha)


def transform(frame: np.ndarray, scale: float = 1.0, angle: float = 0.0, dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    matrix = cv2.getRotationMatrix2D((W / 2, H / 2), angle, scale)
    matrix[0, 2] += dx
    matrix[1, 2] += dy
    return cv2.warpAffine(frame, matrix, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)


def radial_zoom_blur(frame: np.ndarray, amount: float, samples: int = 10) -> np.ndarray:
    if amount <= 0.001:
        return frame
    accumulator = frame.astype(np.float32)
    for index in range(1, samples):
        scale = 1.0 + amount * (index / (samples - 1))
        accumulator += transform(frame, scale=scale).astype(np.float32)
    return np.clip(accumulator / samples, 0, 255).astype(np.uint8)


def horizontal_blur(frame: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 1:
        return frame
    size = max(3, radius | 1)
    kernel = np.zeros((1, size), np.float32)
    kernel[0, :] = 1.0 / size
    return cv2.filter2D(frame, -1, kernel)


def tile_grid(frame: np.ndarray, p: float) -> np.ndarray:
    rows, cols, gap = 4, 3, 4
    cell_w = (W - (cols - 1) * gap) // cols
    cell_h = (H - (rows - 1) * gap) // rows
    grid = np.zeros_like(frame)
    for row in range(rows):
        for col in range(cols):
            scale = 1.06 + 0.025 * ((row + col) % 3)
            tile = transform(frame, scale=scale, dx=(col - 1) * 12, dy=(row - 1.5) * 8)
            if (row + col) % 2:
                tile = cv2.flip(tile, 1)
            thumb = cv2.resize(tile, (cell_w, cell_h), interpolation=cv2.INTER_AREA)
            x = col * (cell_w + gap)
            y = row * (cell_h + gap)
            grid[y:y + cell_h, x:x + cell_w] = thumb
    scale = 1.22 - 0.22 * ease_out(p)
    grid = transform(grid, scale=scale)
    return tint(grid, (12, 22, 32), 0.22 * (1.0 - p))


def x_grid_background(frame: np.ndarray) -> np.ndarray:
    small = cv2.resize(frame, (W // 3, H // 5), interpolation=cv2.INTER_AREA)
    canvas = np.zeros_like(frame)
    for row in range(5):
        for col in range(3):
            tile = small if (row + col) % 2 == 0 else cv2.flip(small, 1)
            y0, y1 = row * H // 5, (row + 1) * H // 5
            x0, x1 = col * W // 3, (col + 1) * W // 3
            tile2 = cv2.resize(tile, (x1 - x0, y1 - y0))
            canvas[y0:y1, x0:x1] = tile2
    dark = tint(canvas, (8, 7, 6), 0.55)
    # X clair répété, inspiré de la famille géométrique sans copier la référence.
    overlay = dark.copy()
    for row in range(5):
        for col in range(3):
            x0, x1 = col * W // 3, (col + 1) * W // 3
            y0, y1 = row * H // 5, (row + 1) * H // 5
            cv2.line(overlay, (x0, y0), (x1, y1), (74, 105, 150), 5, cv2.LINE_AA)
            cv2.line(overlay, (x1, y0), (x0, y1), (74, 105, 150), 5, cv2.LINE_AA)
    return mix(dark, overlay, 0.34)


def geometric_arrow(frame: np.ndarray, p: float) -> np.ndarray:
    bg = x_grid_background(frame)
    yy, xx = np.mgrid[0:H, 0:W]
    metric = xx + 0.45 * yy
    threshold = (-0.18 + 1.36 * smooth(p)) * (W + 0.45 * H)
    mask = (metric <= threshold).astype(np.float32)
    # Pointe de flèche au centre.
    arrow = np.maximum(0.0, 1.0 - np.abs(yy - H * 0.5) / (H * 0.19))
    mask = np.maximum(mask, ((metric <= threshold + arrow * W * 0.16) & (metric > threshold)).astype(np.float32))
    mask = cv2.GaussianBlur(mask, (0, 0), 2.0)
    incoming = transform(frame, scale=1.14 - 0.12 * ease_out(p), angle=-2.0 * (1.0 - p))
    out = (bg.astype(np.float32) * (1 - mask[..., None]) + incoming.astype(np.float32) * mask[..., None]).astype(np.uint8)
    ribbon = np.abs(metric - threshold) < W * 0.045
    out[ribbon] = np.array((123, 211, 245), dtype=np.uint8)
    return out


def radial_zoom(frame: np.ndarray, p: float) -> np.ndarray:
    pulse = math.sin(math.pi * p)
    scale = 1.0 + 0.14 * pulse - 0.02 * p
    base = transform(frame, scale=scale)
    return radial_zoom_blur(base, 0.035 * pulse, samples=10)


def orange_flash(outgoing: np.ndarray, incoming: np.ndarray, p: float) -> np.ndarray:
    base = mix(outgoing, incoming, smooth(p))
    orange_alpha = 0.86 * math.sin(math.pi * p)
    base = tint(base, (45, 107, 240), orange_alpha * 0.72)
    white = math.exp(-((p - 0.48) / 0.14) ** 2) * 0.92
    return tint(base, (245, 249, 255), white)


def hard_action_cut(frame: np.ndarray, p: float) -> np.ndarray:
    if p < 0.5:
        return transform(frame, scale=1.08, angle=-1.5, dx=-10)
    sharpened = cv2.addWeighted(frame, 1.25, cv2.GaussianBlur(frame, (0, 0), 2), -0.25, 0)
    return transform(sharpened, scale=1.0, angle=0.8, dx=8)


def selective_color(frame: np.ndarray, p: float) -> np.ndarray:
    gray = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    yy, xx = np.mgrid[0:H, 0:W]
    metric = xx + 0.29 * yy
    threshold = (-0.1 + 1.2 * smooth(p)) * (W + 0.29 * H)
    mask = (metric <= threshold).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), 2.0)
    color = transform(frame, scale=1.05 - 0.05 * p)
    out = (gray.astype(np.float32) * (1 - mask[..., None]) + color.astype(np.float32) * mask[..., None]).astype(np.uint8)
    stripe = np.abs(metric - threshold) < 32
    orange = tint(out, (36, 122, 244), 0.45)
    out[stripe] = orange[stripe]
    return out


def electric_flash(frame: np.ndarray, p: float) -> np.ndarray:
    pulse = math.sin(math.pi * p)
    out = transform(frame, scale=1.0 + 0.025 * pulse)
    glow = np.zeros_like(out)
    shift = int((p - 0.5) * 170)
    for index, offset in enumerate((-150, 0, 150)):
        x0 = -120 + shift + offset
        cv2.line(glow, (x0, H), (x0 + 520, 0), (255, 248, 232), 10 - index * 2, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 18)
    out = cv2.addWeighted(out, 1.0, glow, 0.85 * pulse, 0)
    white = math.exp(-((p - 0.55) / 0.12) ** 2) * 0.72
    return tint(out, (255, 255, 255), white)


def soft_overlay(frame: np.ndarray, p: float) -> np.ndarray:
    overlay = cv2.flip(transform(frame, scale=1.04, dx=int((p - 0.5) * 54)), 1)
    overlay = cv2.GaussianBlur(overlay, (0, 0), 4 * math.sin(math.pi * p) + 0.1)
    alpha = 0.62 * math.sin(math.pi * p)
    screened = 255 - ((255 - frame.astype(np.uint16)) * (255 - overlay.astype(np.uint16)) // 255)
    return mix(frame, screened.astype(np.uint8), alpha)


def strobe(frame: np.ndarray, local_index: int, p: float) -> np.ndarray:
    colors = [(47, 59, 227), (255, 105, 53), (60, 178, 255)]
    color = colors[(local_index // 2) % len(colors)]
    pulse = 0.36 + 0.46 * (0.5 + 0.5 * math.sin(local_index * math.pi * 0.92))
    out = tint(transform(frame, scale=1.02 + 0.05 * math.sin(math.pi * p)), color, pulse)
    if local_index in (2, 5, 8):
        out = tint(out, (255, 255, 255), 0.48)
    return out


def kaleidoscope(outgoing: np.ndarray, incoming: np.ndarray, p: float) -> np.ndarray:
    source = mix(outgoing, incoming, smooth(p))
    widths = [0.16, 0.18, 0.32, 0.18, 0.16]
    canvas = np.zeros_like(source)
    x = 0
    for index, fraction in enumerate(widths):
        width = W - x if index == len(widths) - 1 else int(round(W * fraction))
        # Chaque bande réinterprète le centre; les bandes impaires sont miroir.
        crop_w = max(48, int(W * (0.22 + 0.04 * abs(index - 2))))
        cx = W // 2 + int((index - 2) * W * 0.055)
        x0 = max(0, min(W - crop_w, cx - crop_w // 2))
        strip = source[:, x0:x0 + crop_w]
        strip = cv2.resize(strip, (width, H), interpolation=cv2.INTER_CUBIC)
        if index % 2:
            strip = cv2.flip(strip, 1)
        angle = (index - 2) * 3.0 * math.sin(math.pi * p)
        strip = transform(cv2.copyMakeBorder(strip, 0, 0, x, W - x - width, cv2.BORDER_CONSTANT), angle=angle)[:, x:x + width]
        shade = 1.0 - 0.11 * abs(index - 2)
        canvas[:, x:x + width] = np.clip(strip.astype(np.float32) * shade, 0, 255).astype(np.uint8)
        x += width
    if p > 0.72:
        canvas = mix(canvas, incoming, smooth((p - 0.72) / 0.28))
    return canvas


def multi_panel(frame: np.ndarray, p: float) -> np.ndarray:
    background = tint(cv2.GaussianBlur(frame, (0, 0), 18), DARK, 0.62)
    canvas = background.copy()
    progress = ease_out(min(1.0, p / 0.65))
    layouts = [
        (90, 110, 540, 820),
        (24, 50, 230, 300),
        (466, 64, 230, 300),
        (28, 932, 230, 300),
        (462, 918, 230, 300),
    ]
    for index, (x, y, width, height) in enumerate(layouts):
        tile = transform(frame, scale=1.02 + index * 0.018, dx=(index - 2) * 8)
        tile = cv2.resize(tile, (width, height), interpolation=cv2.INTER_AREA)
        scale = max(0.05, progress - index * 0.06)
        tw, th = max(1, int(width * scale)), max(1, int(height * scale))
        small = cv2.resize(tile, (tw, th), interpolation=cv2.INTER_AREA)
        xx, yy = x + (width - tw) // 2, y + (height - th) // 2
        x1, y1 = min(W, xx + tw), min(H, yy + th)
        if x1 > xx and y1 > yy:
            canvas[yy:y1, xx:x1] = small[:y1 - yy, :x1 - xx]
            cv2.rectangle(canvas, (xx, yy), (x1 - 1, y1 - 1), (207, 233, 248), 3, cv2.LINE_AA)
    if p > 0.75:
        canvas = mix(canvas, frame, smooth((p - 0.75) / 0.25))
    return canvas


def rotating_mask(frame: np.ndarray, p: float) -> np.ndarray:
    outgoing = transform(frame, scale=1.0 + 0.08 * p, angle=8 * p)
    incoming = transform(frame, scale=0.88 + 0.12 * ease_out(p), angle=110 * (1.0 - p))
    radius = int((0.18 + 0.60 * smooth(p)) * min(W, H))
    mask = np.zeros((H, W), np.uint8)
    center = (W // 2, int(H * 0.56))
    cv2.circle(mask, center, radius, 255, -1, cv2.LINE_AA)
    mask = cv2.GaussianBlur(mask, (0, 0), 2.0).astype(np.float32) / 255.0
    out = (outgoing.astype(np.float32) * (1 - mask[..., None]) + incoming.astype(np.float32) * mask[..., None]).astype(np.uint8)
    cv2.ellipse(out, center, (radius, radius), -110 * (1.0 - p), 15, 245, (70, 184, 247), 7, cv2.LINE_AA)
    return out


def radial_cross(outgoing: np.ndarray, incoming: np.ndarray, p: float) -> np.ndarray:
    pulse = math.sin(math.pi * p)
    base = mix(transform(outgoing, scale=1.0 + 0.24 * p, angle=12 * pulse), transform(incoming, scale=0.84 + 0.16 * p, angle=-12 * (1 - p)), smooth(p))
    return radial_zoom_blur(base, 0.055 * pulse, samples=12)


def whip_zoom(frame: np.ndarray, p: float) -> np.ndarray:
    if p < 0.5:
        q = p / 0.5
        out = transform(frame, scale=1.0 + 0.48 * ease_out(q), angle=-6 * q, dx=-32 * q)
        return horizontal_blur(out, int(3 + 29 * math.sin(math.pi * q / 2)))
    q = (p - 0.5) / 0.5
    out = transform(frame, scale=1.48 - 0.48 * ease_out(q), angle=-6 * (1 - q), dx=32 * (1 - q))
    return horizontal_blur(out, int(31 * (1 - ease_out(q))) | 1)


def panel_match(frame: np.ndarray, p: float, profile: dict[str, Any]) -> np.ndarray:
    """Animate rows/columns without leaking editing guides into the ad.

    The owner rejected the former cyan separators. Their visibility is now
    controlled by the canonical transition JSON; the active T3 contract sets
    ``separator_lines=false`` and ``border_px=0``.
    """
    canvas = np.zeros_like(frame)
    border_px = int(profile.get("border_px", 0))
    draw_separators = bool(profile.get("separator_lines", False)) and border_px > 0
    separator_color = profile.get("separator_color")
    if draw_separators and not separator_color:
        raise ValueError("separator_color requis lorsque separator_lines=true")
    color_bgr = (0, 0, 0)
    if separator_color:
        clean = str(separator_color).lstrip("#")
        if len(clean) != 6:
            raise ValueError("separator_color invalide")
        color_bgr = (int(clean[4:6], 16), int(clean[2:4], 16), int(clean[0:2], 16))

    if p < 0.5:
        q = smooth(p / 0.5)
        for row in range(3):
            y0, y1 = row * H // 3, (row + 1) * H // 3
            shift = int((row - 1) * 64 * (1 - q))
            segment = np.roll(frame[y0:y1], shift, axis=1)
            canvas[y0:y1] = segment
            if row and draw_separators:
                cv2.line(canvas, (0, y0), (W, y0), color_bgr, border_px, cv2.LINE_AA)
    else:
        q = smooth((p - 0.5) / 0.5)
        for col in range(3):
            x0, x1 = col * W // 3, (col + 1) * W // 3
            shift = int((1 - col) * 72 * (1 - q))
            segment = np.roll(frame[:, x0:x1], shift, axis=0)
            canvas[:, x0:x1] = segment
            if col and draw_separators:
                cv2.line(canvas, (x0, 0), (x0, H), color_bgr, border_px, cv2.LINE_AA)
    return transform(canvas, scale=1.08 - 0.08 * p)


def diagonal_rotating_wipe(frame: np.ndarray, p: float) -> np.ndarray:
    hero = transform(frame, scale=1.06, angle=1.2)
    yy, xx = np.mgrid[0:H, 0:W]
    diagonal = xx + 0.46 * yy
    period = (W + int(0.46 * H)) / 6.0
    phase = (diagonal / period) % 1.0
    if p < 0.52:
        q = smooth(p / 0.52)
        covered = phase < q
        out = frame.copy()
        out[covered] = np.array(DARK, dtype=np.uint8)
        out = transform(out, angle=24 * q)
    else:
        q = smooth((p - 0.52) / 0.48)
        revealed = phase < q
        out = np.empty_like(frame)
        out[:] = DARK
        out[revealed] = hero[revealed]
        out = transform(out, angle=24 * (1 - q))
    return out


def background_fade(frame: np.ndarray, p: float) -> np.ndarray:
    q = smooth(p)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy, rx, ry = W * 0.5, H * 0.47, W * 0.43, H * 0.39
    subject = 1.0 - np.clip(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2, 0, 1)
    subject = cv2.GaussianBlur(subject.astype(np.float32), (0, 0), 18)
    darkened = np.clip(frame.astype(np.float32) * (1.0 - 0.76 * q), 0, 255).astype(np.uint8)
    darkened = cv2.GaussianBlur(darkened, (0, 0), 7 * q + 0.1)
    protection = (subject * q)[..., None]
    return np.clip(darkened.astype(np.float32) * (1 - protection) + frame.astype(np.float32) * protection, 0, 255).astype(np.uint8)


def vignette_mask() -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    nx = (xx - W / 2) / (W / 2)
    ny = (yy - H / 2) / (H / 2)
    radius = np.sqrt(nx * nx + ny * ny)
    return np.clip(1.02 - 0.18 * np.maximum(0, radius - 0.38), 0.78, 1.0).astype(np.float32)[..., None]


def apply_vignette(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.clip(frame.astype(np.float32) * mask, 0, 255).astype(np.uint8)


def font_path(bold: bool = True) -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("Police DejaVu Sans introuvable")


def event_progress(event: dict[str, Any], frame_number: int) -> tuple[int, float]:
    start, end = event["frames"]
    local = frame_number - start
    length = end - start + 1
    return local, 0.0 if length <= 1 else local / (length - 1)


def make_contact_sheet(video: Path, destination: Path, samples: list[int]) -> None:
    cap = cv2.VideoCapture(str(video))
    thumbs = []
    font = ImageFont.truetype(font_path(True), 18)
    for frame_number in samples:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"Impossible de lire l’image {frame_number}")
        thumb = cv2.resize(frame, (180, 320), interpolation=cv2.INTER_AREA)
        thumb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(thumb)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 178, 28), fill=(0, 0, 0))
        draw.text((7, 4), f"f{frame_number} · {frame_number/FPS:.2f}s", font=font, fill="white")
        thumbs.append(image)
    cols = 5
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 180, rows * 320), (18, 14, 12))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * 180, (index // cols) * 320))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=92)
    cap.release()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("rushes/manifest.json"))
    parser.add_argument("--contract", type=Path, default=Path("reverse-engineering/T3_TRANSITIONS_30S.json"))
    parser.add_argument("--render-job", type=Path, default=Path("demo/render_job_silent_demo_v0_4.json"))
    parser.add_argument("--text-config", type=Path, default=Path("config/T3_TEXT_MOTION_V0_4_0.json"))
    parser.add_argument("--cache", type=Path, default=Path("rushes/cache"))
    parser.add_argument("--work", type=Path, default=Path(".tmp/t3-silent"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/t3-silent-v0.4.0"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    render_job = json.loads(args.render_job.read_text(encoding="utf-8"))
    text_config = json.loads(args.text_config.read_text(encoding="utf-8"))
    validate_text_config(text_config)
    fields = normalize_payload(render_job["merchant_payload"])
    resolved_visible_texts = visible_text_contract(fields, text_config)
    resolved_typography_audit = typography_audit(text_config)
    transition_profiles = contract["transition_parameter_profiles"]
    panel_profile = transition_profiles["R4_MULTI_PANEL_MATCH_CUT"]
    panel_separators_enabled = bool(panel_profile.get("separator_lines", False)) and int(panel_profile.get("border_px", 0)) > 0
    if contract.get("owner_constraints", {}).get("visible_transition_guides_allowed") is False and panel_separators_enabled:
        raise ValueError("Le JSON interdit les traits séparateurs visibles")
    scenes = manifest["scenes"]
    if [int(scene["duration_seconds"]) for scene in scenes] != [6, 8, 7, 9]:
        raise SystemExit("Durées de scènes non conformes")
    if len(contract["timeline_events"]) != 17:
        raise SystemExit("Le contrat doit contenir exactement 17 événements")

    args.work.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_binary()

    intermediates: dict[str, Path] = {}
    for scene in scenes:
        source = args.cache / scene["cache_filename"]
        if not source.exists():
            raise SystemExit(f"Rush manquant: {source}. Exécuter tools/fetch_rushes.py.")
        if sha256(source) != scene["sha256"]:
            raise SystemExit(f"SHA-256 du rush invalide: {source}")
        destination = args.work / f"{scene['scene']}_base.mp4"
        preprocess_scene(ffmpeg, source, destination, scene)
        intermediates[scene["scene"]] = destination

    output = args.output_dir / text_config["output"]["video_filename"]
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s:v", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-frames:v", str(TOTAL), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    if encoder.stdin is None:
        raise RuntimeError("Tube FFmpeg indisponible")

    caps = {key: cv2.VideoCapture(str(path)) for key, path in intermediates.items()}
    cross_caps = {
        4: cv2.VideoCapture(str(intermediates["S2"])),
        10: cv2.VideoCapture(str(intermediates["S3"])),
        13: cv2.VideoCapture(str(intermediates["S4"])),
    }
    event_for_frame: list[dict[str, Any] | None] = [None] * TOTAL
    for event in contract["timeline_events"]:
        for index in range(event["frames"][0], event["frames"][1] + 1):
            if event_for_frame[index] is not None:
                raise RuntimeError(f"Chevauchement d’événements à l’image {index}")
            event_for_frame[index] = event

    scene_ranges = [(0, 179, "S1"), (180, 419, "S2"), (420, 629, "S3"), (630, 899, "S4")]
    vmask = vignette_mask()
    graphic_counts = {item["id"]: 0 for item in text_config["graphics"]}
    applied_counts = {event["event"]: 0 for event in contract["timeline_events"]}
    sample_hashes: dict[int, dict[str, str]] = {event["event"]: {} for event in contract["timeline_events"]}

    try:
        current_scene = None
        for frame_number in range(TOTAL):
            scene_id = next(scene for start, end, scene in scene_ranges if start <= frame_number <= end)
            if scene_id != current_scene:
                current_scene = scene_id
            ok, base = caps[scene_id].read()
            if not ok:
                raise RuntimeError(f"Lecture impossible {scene_id} à l’image {frame_number}")
            if base.shape[:2] != (H, W):
                base = cv2.resize(base, (W, H), interpolation=cv2.INTER_CUBIC)

            event = event_for_frame[frame_number]
            frame = base
            if event is not None:
                local, p = event_progress(event, frame_number)
                number = int(event["event"])
                transition = event["transition_id"]
                incoming = None
                if number in cross_caps:
                    ok2, incoming = cross_caps[number].read()
                    if not ok2:
                        raise RuntimeError(f"Lecture incoming impossible pour événement {number}")
                if transition == "R4_TILED_GRID_INTRO":
                    frame = tile_grid(base, p)
                elif transition == "R2_GEOMETRIC_ARROW_MASK":
                    frame = geometric_arrow(base, p)
                elif transition == "R2_RADIAL_ZOOM":
                    frame = radial_zoom(base, p)
                elif transition == "R4_ORANGE_FLASH":
                    frame = orange_flash(base, incoming, p)  # type: ignore[arg-type]
                elif transition == "R2_HARD_ACTION_MATCH_CUT":
                    frame = hard_action_cut(base, p)
                elif transition == "R2_SELECTIVE_COLOR_REVEAL":
                    frame = selective_color(base, p)
                elif transition == "R2_FLASH_TRANSITION" and number == 7:
                    frame = electric_flash(base, p)
                elif transition == "R4_SOFT_OVERLAY_BLEND":
                    frame = soft_overlay(base, p)
                elif transition == "R2_FLASH_TRANSITION" and number == 9:
                    frame = strobe(base, local, p)
                elif transition == "R4_KALEIDOSCOPE_MOSAIC":
                    frame = kaleidoscope(base, incoming, p)  # type: ignore[arg-type]
                elif transition == "R2_MULTI_PANEL_SPLIT":
                    frame = multi_panel(base, p)
                elif transition == "R4_ROTATING_MASK":
                    frame = rotating_mask(base, p)
                elif transition == "R4_RADIAL_BLUR":
                    frame = radial_cross(base, incoming, p)  # type: ignore[arg-type]
                elif transition == "R4_WHIP_ZOOM":
                    frame = whip_zoom(base, p)
                elif transition == "R4_MULTI_PANEL_MATCH_CUT":
                    frame = panel_match(base, p, transition_profiles[event["parameter_profile"]])
                elif transition == "R2_DIAGONAL_ROTATING_WIPE":
                    frame = diagonal_rotating_wipe(base, p)
                elif transition == "R4_BACKGROUND_FADE_TO_BLACK":
                    frame = background_fade(base, p)
                else:
                    raise RuntimeError(f"Transition non implémentée: {transition} événement {number}")
                applied_counts[number] += 1

            frame = apply_vignette(frame, vmask)
            # T1/T2 : les graphismes commerçant sont composités après les effets.
            frame, active_graphic_ids = render_text_motion(frame, frame_number, fields, text_config)
            for graphic_id in active_graphic_ids:
                graphic_counts[graphic_id] += 1

            if event is not None:
                start, end = event["frames"]
                markers = {start: "start", (start + end) // 2: "middle", end: "end"}
                if frame_number in markers:
                    sample_hashes[int(event["event"])][markers[frame_number]] = hashlib.sha256(frame.tobytes()).hexdigest()

            encoder.stdin.write(np.ascontiguousarray(frame).tobytes())
            if frame_number % 90 == 0:
                print(f"RENDER {frame_number}/{TOTAL}", flush=True)
    finally:
        encoder.stdin.close()
        return_code = encoder.wait()
        for cap in list(caps.values()) + list(cross_caps.values()):
            cap.release()
    if return_code != 0:
        raise RuntimeError(f"FFmpeg a échoué avec le code {return_code}")

    expected_counts = {event["event"]: event["frames"][1] - event["frames"][0] + 1 for event in contract["timeline_events"]}
    if applied_counts != expected_counts:
        raise RuntimeError(f"Couverture événements invalide: {applied_counts} != {expected_counts}")

    output_hash = sha256(output)
    report = {
        "schema_version": "1.0.0",
        "template_id": "RESTAURATION-T3",
        "engine_version": ENGINE_VERSION,
        "status": "silent_candidate_v0_4_no_blue_guides_pending_owner_validation",
        "rendered_on": os.environ.get("GITHUB_ACTIONS") == "true" and "github_actions" or "local_preflight",
        "output": {
            "file": output.name,
            "bytes": output.stat().st_size,
            "sha256": output_hash,
            "width": W,
            "height": H,
            "fps": FPS,
            "total_frames": TOTAL,
            "duration_seconds": 30,
            "audio_streams_expected": 0,
        },
        "source_manifest_sha256": sha256(args.manifest),
        "transition_contract_sha256": sha256(args.contract),
        "render_job_sha256": sha256(args.render_job),
        "text_motion_config_id": text_config["id"],
        "text_motion_config_sha256": sha256(args.text_config),
        "typography_audit": resolved_typography_audit,
        "owner_feedback_legibility_corrected": True,
        "owner_feedback_blue_lines_corrected": True,
        "transition_visibility_audit": {
            "visible_transition_guides_rendered": panel_separators_enabled,
            "R4_MULTI_PANEL_MATCH_CUT": {
                "gap_px": int(panel_profile.get("gap_px", 0)),
                "border_px": int(panel_profile.get("border_px", 0)),
                "separator_lines": bool(panel_profile.get("separator_lines", False)),
                "separator_color": panel_profile.get("separator_color"),
                "separator_policy": panel_profile.get("separator_policy"),
                "proof_frames": [771, 778],
            },
        },
        "contact_sheet_file": text_config["output"]["contact_sheet_filename"],
        "merchant_payload_fields": list(fields.keys()),
        "visible_text_contract": resolved_visible_texts,
        "forbidden_visible_strings": text_config["forbidden_visible_strings"],
        "technical_labels_rendered": False,
        "graphics": [{
            "id": item["id"],
            "frames": [item["start_f"], item["end_f_exclusive"] - 1],
            "expected_frame_count": item["end_f_exclusive"] - item["start_f"],
            "applied_frame_count": graphic_counts[item["id"]],
            "fields": item["fields"],
        } for item in text_config["graphics"]],
        "sources": [{"scene": scene["scene"], "pexels_id": scene["pexels_id"], "sha256": scene["sha256"], "raw_published": False} for scene in scenes],
        "events": [{
            "event": event["event"],
            "transition_id": event["transition_id"],
            "frames": event["frames"],
            "expected_frame_count": expected_counts[event["event"]],
            "applied_frame_count": applied_counts[event["event"]],
            "sample_frame_sha256": sample_hashes[event["event"]],
        } for event in contract["timeline_events"]],
        "all_17_events_applied": len(applied_counts) == 17 and applied_counts == expected_counts,
        "all_4_graphics_applied": all(graphic_counts[item["id"]] == item["end_f_exclusive"] - item["start_f"] for item in text_config["graphics"]),
        "references_covered": ["R3-B03-REF-02", "R3-B03-REF-04"],
        "raw_rushes_embedded_as_standalone_assets": False,
        "owner_approval_required": True,
    }
    report_path = args.output_dir / "T3_SILENT_RENDER_REPORT.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    contact = args.output_dir / text_config["output"]["contact_sheet_filename"]
    samples = [0, 17, 35, 86, 179, 225, 263, 312, 383, 419, 466, 551, 629, 710, 771, 778, 781, 840, 899]
    make_contact_sheet(output, contact, samples)
    sums = args.output_dir / "SHA256SUMS.txt"
    files = [output, report_path, contact]
    sums.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in files), encoding="utf-8")
    print(f"T3_SILENT_RENDER_PASS {output} {output_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
