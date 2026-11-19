"""Motion design T3 alimenté exclusivement par merchant_payload.

La logique reprend le contrat éprouvé T1/T2 : champs validés, blocs liés aux
scènes, révélation par masque et texte composité après les transitions.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IVORY = (251, 247, 238, 255)
SOFT = (235, 226, 211, 248)
AMBER = (247, 181, 59, 255)
GREEN = (37, 211, 102, 255)
REQUIRED = ("nom", "produit", "prix", "whatsapp", "quartier")
ALLOWED = (*REQUIRED, "accroche")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_text_config(config: dict[str, Any]) -> None:
    canvas = config["canvas"]
    if (canvas["width"], canvas["height"], canvas["fps"], canvas["frames"]) != (720, 1280, 30, 900):
        raise ValueError("Canevas texte T3 invalide")
    if config.get("hard_cards") is not False or config.get("text_layer_affected_by_transitions") is not False:
        raise ValueError("Les textes T3 doivent rester nets et sans carte dure")
    ids = [item["id"] for item in config["graphics"]]
    if ids != ["T3_G01_IDENTITY", "T3_G02_OFFER", "T3_G03_HOOK", "T3_G04_FINAL"]:
        raise ValueError("Les quatre blocs graphiques T3 sont incomplets")
    if tuple(config["allowed_merchant_fields"]) != ALLOWED:
        raise ValueError("Clés commerçant visibles non canoniques")
    for font in config["fonts"].values():
        path = ROOT / font["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Police absente : {path}")
        if _sha256(path) != font["sha256"]:
            raise ValueError(f"Empreinte de police invalide : {path}")


def normalize_payload(raw: dict[str, Any]) -> dict[str, str]:
    extras = sorted(set(raw) - set(ALLOWED))
    if extras:
        raise ValueError(f"Propriétés commerçant interdites : {extras}")
    clean: dict[str, str] = {}
    limits = {"nom": 40, "produit": 32, "prix": 7, "whatsapp": 20, "quartier": 40, "accroche": 48}
    for key in ALLOWED:
        value = raw.get(key, "")
        if not isinstance(value, str):
            raise ValueError(f"{key} doit être du texte")
        value = " ".join(value.strip().split())
        if key in {"nom", "produit", "accroche"}:
            value = value.rstrip(".").strip()
        if key in REQUIRED and not value:
            raise ValueError(f"Champ obligatoire vide : {key}")
        if len(value) > limits[key]:
            raise ValueError(f"Champ trop long : {key}")
        clean[key] = value
    if not re.fullmatch(r"[0-9 .]+", clean["prix"]):
        raise ValueError("Prix invalide")
    return clean


def _font(config: dict[str, Any], key: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ROOT / config["fonts"][key]["file"]), size=int(size))


def _fit(text: str, config: dict[str, Any], key: str, maximum: int, minimum: int, width: int) -> ImageFont.FreeTypeFont:
    for size in range(maximum, minimum - 1, -1):
        font = _font(config, key, size)
        if font.getlength(text) <= width:
            return font
    return _font(config, key, minimum)


def _balanced_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    if font.getlength(text) <= max_width:
        return [text]
    words = text.split()
    best: tuple[float, list[str]] | None = None
    for cut in range(1, len(words)):
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
        widths = [font.getlength(line) for line in lines]
        score = max(widths) + abs(widths[0] - widths[1]) * 0.3
        if max(widths) <= max_width and (best is None or score < best[0]):
            best = (score, lines)
    return best[1] if best else [text]


def _draw_center(draw: ImageDraw.ImageDraw, text: str, y: float, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int] = IVORY, stroke: int = 1) -> None:
    width = draw.textlength(text, font=font)
    x = (720 - width) / 2
    draw.text((x + 3, y + 4), text, font=font, fill=(0, 0, 0, 145), stroke_width=stroke, stroke_fill=(0, 0, 0, 145))
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(20, 14, 9, 180))


def _draw_tracked_center(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, tracking: int, fill: tuple[int, int, int, int] = SOFT) -> None:
    widths = [draw.textlength(char, font=font) for char in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = (720 - total) / 2
    for char, width in zip(text, widths):
        draw.text((x + 2, y + 3), char, font=font, fill=(0, 0, 0, 150))
        draw.text((x, y), char, font=font, fill=fill)
        x += width + tracking


def _format_price(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        raise ValueError("Prix sans chiffre")
    grouped = f"{int(digits):,}".replace(",", " ")
    return f"{grouped} FCFA"


def active_graphics(config: dict[str, Any], frame_index: int) -> list[dict[str, Any]]:
    return [item for item in config["graphics"] if int(item["start_f"]) <= frame_index < int(item["end_f_exclusive"])]


def _smooth(value: float) -> float:
    x = float(np.clip(value, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


def _progress(block: dict[str, Any], frame_index: int) -> float:
    return _smooth((frame_index - int(block["start_f"]) + 1) / max(1, int(block["reveal_end_f"]) - int(block["start_f"])))


def _opacity(block: dict[str, Any], frame_index: int) -> float:
    reveal = _progress(block, frame_index)
    end = int(block["end_f_exclusive"])
    if end == 900:
        return reveal
    fade_start = end - 18
    fade = 1.0 if frame_index < fade_start else _smooth((end - frame_index) / 18.0)
    return float(np.clip(reveal * fade, 0.0, 1.0))


def _soft_scrim(frame: np.ndarray, top: float, bottom: float) -> np.ndarray:
    y = np.linspace(0.0, 1.0, frame.shape[0], dtype=np.float32)[:, None]
    top_curve = np.clip(1.0 - y / 0.58, 0.0, 1.0) * top
    bottom_curve = np.clip((y - 0.42) / 0.58, 0.0, 1.0) * bottom
    alpha = np.maximum(top_curve, bottom_curve)[..., None]
    return np.clip(frame.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)


def _animate(layer: Image.Image, progress: float, opacity: float, rise: int) -> Image.Image:
    revealed = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    width = int(round(layer.width * np.clip(progress, 0.0, 1.0)))
    if width > 0:
        revealed.paste(layer.crop((0, 0, width, layer.height)), (0, 0))
    shift = int(round((1.0 - progress) * rise))
    if shift:
        moved = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        moved.alpha_composite(revealed, (0, shift))
        revealed = moved
    alpha = revealed.getchannel("A").point(lambda value: int(value * float(np.clip(opacity, 0.0, 1.0))))
    revealed.putalpha(alpha)
    return revealed


def _identity(fields: dict[str, str], config: dict[str, Any]) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    name_font = _fit(fields["nom"], config, "light_sans", 27, 19, 560)
    _draw_tracked_center(draw, fields["nom"].upper(), 128, name_font, 3, AMBER)
    product_font = _fit(fields["produit"], config, "display_serif", 76, 46, 610)
    lines = _balanced_lines(fields["produit"], product_font, 610)
    for index, line in enumerate(lines):
        _draw_center(draw, line, 192 + index * int(product_font.size * 0.94), product_font)
    draw.rounded_rectangle((270, 350, 450, 354), radius=2, fill=AMBER)
    return layer


def _offer(fields: dict[str, str], config: dict[str, Any], progress: float) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    product_font = _fit(fields["produit"], config, "display_serif", 62, 39, 600)
    lines = _balanced_lines(fields["produit"], product_font, 600)
    for index, line in enumerate(lines):
        _draw_center(draw, line, 135 + index * int(product_font.size * 0.95), product_font)
    price = _format_price(fields["prix"])
    price_font = _fit(price, config, "utility", 62, 40, 580)
    _draw_center(draw, price, 892 + int((1.0 - progress) * 22), price_font)
    return layer


def _hook(fields: dict[str, str], config: dict[str, Any]) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    hook = fields.get("accroche", "")
    if hook:
        hook_font = _fit(hook, config, "display_serif", 61, 39, 610)
        for index, line in enumerate(_balanced_lines(hook, hook_font, 610)):
            _draw_center(draw, line, 165 + index * int(hook_font.size * 0.96), hook_font)
    name_font = _fit(fields["nom"], config, "light_sans", 25, 18, 540)
    _draw_tracked_center(draw, fields["nom"].upper(), 350, name_font, 3, SOFT)
    return layer


def _final(fields: dict[str, str], config: dict[str, Any]) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    name_font = _fit(fields["nom"], config, "light_sans", 25, 18, 560)
    _draw_tracked_center(draw, fields["nom"].upper(), 82, name_font, 3, AMBER)
    product_font = _fit(fields["produit"], config, "display_serif", 66, 42, 610)
    for index, line in enumerate(_balanced_lines(fields["produit"], product_font, 610)):
        _draw_center(draw, line, 135 + index * int(product_font.size * 0.92), product_font)

    price_font = _fit(_format_price(fields["prix"]), config, "utility", 50, 34, 540)
    _draw_center(draw, _format_price(fields["prix"]), 875, price_font)
    location_font = _fit(fields["quartier"], config, "light_sans", 23, 17, 570)
    _draw_center(draw, fields["quartier"], 946, location_font, SOFT, 0)
    cta_font = _font(config, "light_sans", 20)
    _draw_tracked_center(draw, "COMMANDER MAINTENANT", 1005, cta_font, 2, AMBER)

    phone_font = _fit(fields["whatsapp"], config, "utility", 31, 23, 500)
    phone_width = draw.textlength(fields["whatsapp"], font=phone_font)
    total = 22 + 15 + phone_width
    x = (720 - total) / 2
    y = 1054
    draw.ellipse((x, y + 10, x + 22, y + 32), fill=GREEN)
    draw.text((x + 39 + 2, y + 3), fields["whatsapp"], font=phone_font, fill=(0, 0, 0, 145))
    draw.text((x + 39, y), fields["whatsapp"], font=phone_font, fill=IVORY, stroke_width=1, stroke_fill=(20, 14, 9, 180))
    return layer


def visible_text_contract(fields: dict[str, str], config: dict[str, Any]) -> dict[str, list[str]]:
    price = _format_price(fields["prix"])
    values = {
        "T3_G01_IDENTITY": [fields["nom"], fields["produit"]],
        "T3_G02_OFFER": [fields["produit"], price],
        "T3_G03_HOOK": ([fields["accroche"]] if fields.get("accroche") else []) + [fields["nom"]],
        "T3_G04_FINAL": [fields["nom"], fields["produit"], price, fields["quartier"], "COMMANDER MAINTENANT", fields["whatsapp"]],
    }
    forbidden = {value.upper() for value in config["forbidden_visible_strings"]}
    for block_values in values.values():
        for value in block_values:
            if value.upper() in forbidden:
                raise ValueError(f"Texte commercial en collision avec une chaîne interdite : {value}")
    return values


def render_text_motion(frame_bgr: np.ndarray, frame_index: int, fields: dict[str, str], config: dict[str, Any]) -> tuple[np.ndarray, list[str]]:
    blocks = active_graphics(config, frame_index)
    if not blocks:
        return frame_bgr, []
    block = blocks[0]
    progress = _progress(block, frame_index)
    opacity = _opacity(block, frame_index)
    if block["id"] == "T3_G01_IDENTITY":
        frame_bgr = _soft_scrim(frame_bgr, top=0.50, bottom=0.06)
        layer = _animate(_identity(fields, config), progress, opacity, 18)
    elif block["id"] == "T3_G02_OFFER":
        frame_bgr = _soft_scrim(frame_bgr, top=0.46, bottom=0.56)
        layer = _animate(_offer(fields, config, progress), progress, opacity, 14)
    elif block["id"] == "T3_G03_HOOK":
        frame_bgr = _soft_scrim(frame_bgr, top=0.52, bottom=0.08)
        layer = _animate(_hook(fields, config), progress, opacity, 16)
    else:
        frame_bgr = _soft_scrim(frame_bgr, top=0.52, bottom=0.62)
        layer = _animate(_final(fields, config), progress, opacity, 12)
    base = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    result = Image.alpha_composite(base, layer).convert("RGB")
    return cv2.cvtColor(np.asarray(result), cv2.COLOR_RGB2BGR), [block["id"]]
