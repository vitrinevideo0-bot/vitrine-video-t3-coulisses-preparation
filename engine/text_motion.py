"""Motion design T3 alimenté exclusivement par merchant_payload.

La v0.3 verrouille aussi la lisibilité dans le JSON : poids explicites des
polices variables, tailles minimales, contraste, ombre et fonds dégradés.
Les textes restent composités après les transitions.
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
REQUIRED = ("nom", "produit", "prix", "whatsapp", "quartier")
ALLOWED = (*REQUIRED, "accroche")
REQUIRED_ROLES = (
    "merchant_name",
    "hero_product",
    "offer_product",
    "hook",
    "price",
    "location",
    "cta",
    "phone",
)
SMALL_READABILITY_ROLES = ("merchant_name", "location", "cta", "phone")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hex_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    clean = value.lstrip("#")
    if len(clean) != 6 or not re.fullmatch(r"[0-9A-Fa-f]{6}", clean):
        raise ValueError(f"Couleur hexadécimale invalide : {value}")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16), alpha


def _relative_luminance(hex_color: str) -> float:
    rgb = _hex_rgba(hex_color)[:3]
    channels = []
    for value in rgb:
        normalized = value / 255.0
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first, second = _relative_luminance(foreground), _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def typography_audit(config: dict[str, Any]) -> dict[str, Any]:
    legibility = config["legibility"]
    scale = float(legibility["preview_scale_floor"])
    background = legibility["contrast_test_background"]
    colors = legibility["colors"]
    role_audit: dict[str, Any] = {}
    for role_name in REQUIRED_ROLES:
        role = legibility["roles"][role_name]
        font = config["fonts"][role["font"]]
        ratio = _contrast_ratio(colors[role["color"]], background)
        role_audit[role_name] = {
            "font": font["family"],
            "weight": role.get("weight"),
            "minimum_font_size_px": role["min_size_px"],
            "effective_minimum_at_preview_scale_px": round(float(role["min_size_px"]) * scale, 2),
            "contrast_ratio": round(ratio, 2),
        }
    return {
        "config_id": config["id"],
        "preview_scale_floor": scale,
        "required_effective_font_px": legibility["minimum_effective_font_px"],
        "required_contrast_ratio": legibility["minimum_contrast_ratio"],
        "variable_font_weights_explicit": all(
            role_audit[name]["weight"] is not None
            for name in REQUIRED_ROLES
            if config["fonts"][legibility["roles"][name]["font"]].get("variable_weight_axis")
        ),
        "shadow": legibility["shadow"],
        "roles": role_audit,
    }


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
    output = config.get("output", {})
    for key in ("video_filename", "contact_sheet_filename", "directory_name"):
        value = output.get(key, "")
        if not value or Path(value).name != value:
            raise ValueError(f"Nom de sortie JSON invalide : {key}")
    for font in config["fonts"].values():
        path = ROOT / font["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Police absente : {path}")
        if _sha256(path) != font["sha256"]:
            raise ValueError(f"Empreinte de police invalide : {path}")

    legibility = config.get("legibility")
    if not legibility:
        raise ValueError("Contrat de lisibilité absent")
    if set(REQUIRED_ROLES) - set(legibility.get("roles", {})):
        raise ValueError("Rôles typographiques incomplets")
    minimum_effective = float(legibility["minimum_effective_font_px"])
    minimum_ratio = float(legibility["minimum_contrast_ratio"])
    scale = float(legibility["preview_scale_floor"])
    if not 0.35 <= scale <= 1.0:
        raise ValueError("Échelle minimale de prévisualisation invalide")
    if int(legibility["shadow"]["stroke_width_px"]) < 2 or int(legibility["shadow"]["opacity"]) < 220:
        raise ValueError("Protection de contraste insuffisante")
    for role_name, role in legibility["roles"].items():
        if role["font"] not in config["fonts"]:
            raise ValueError(f"Police inconnue pour {role_name}")
        if int(role["min_size_px"]) > int(role["max_size_px"]):
            raise ValueError(f"Tailles inversées pour {role_name}")
        font_cfg = config["fonts"][role["font"]]
        weight = role.get("weight")
        if font_cfg.get("variable_weight_axis"):
            if weight is None:
                raise ValueError(f"Poids variable absent pour {role_name}")
            if not int(font_cfg["axis_min"]) <= int(weight) <= int(font_cfg["axis_max"]):
                raise ValueError(f"Poids hors axe pour {role_name}")
        if role_name in SMALL_READABILITY_ROLES:
            if int(role["min_size_px"]) * scale < minimum_effective:
                raise ValueError(f"Texte trop petit à l’échelle de contrôle : {role_name}")
            if weight is None or int(weight) < 600:
                raise ValueError(f"Graisse insuffisante pour {role_name}")
        color = legibility["colors"][role["color"]]
        if _contrast_ratio(color, legibility["contrast_test_background"]) < minimum_ratio:
            raise ValueError(f"Contraste insuffisant pour {role_name}")
    final_scrim = legibility["scrims"]["T3_G04_FINAL"]
    if float(final_scrim["bottom"]) < 0.75 or float(final_scrim["top"]) < 0.60:
        raise ValueError("Fond final insuffisamment protégé")


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


def _font(config: dict[str, Any], key: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(ROOT / config["fonts"][key]["file"]), size=int(size))
    if weight is not None and config["fonts"][key].get("variable_weight_axis") and hasattr(font, "set_variation_by_axes"):
        try:
            font.set_variation_by_axes([int(weight)])
        except (OSError, ValueError):
            raise ValueError(f"Impossible d’appliquer le poids {weight} à {key}")
    return font


def _role(config: dict[str, Any], role_name: str) -> dict[str, Any]:
    return config["legibility"]["roles"][role_name]


def _fit_role(text: str, config: dict[str, Any], role_name: str) -> ImageFont.FreeTypeFont:
    role = _role(config, role_name)
    for size in range(int(role["max_size_px"]), int(role["min_size_px"]) - 1, -1):
        font = _font(config, role["font"], size, role.get("weight"))
        if font.getlength(text) <= int(role["max_width_px"]):
            return font
    return _font(config, role["font"], int(role["min_size_px"]), role.get("weight"))


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
    if best:
        return best[1]
    raise ValueError(f"Texte impossible à afficher sans troncature : {text!r}")


def _color(config: dict[str, Any], name: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return _hex_rgba(config["legibility"]["colors"][name], alpha)


def _draw_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: float,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    config: dict[str, Any],
) -> None:
    effect = config["legibility"]["shadow"]
    width = draw.textlength(text, font=font)
    x = (720 - width) / 2
    stroke = int(effect["stroke_width_px"])
    shadow = _color(config, "shadow", int(effect["opacity"]))
    stroke_fill = _color(config, "stroke", int(effect["stroke_opacity"]))
    draw.text(
        (x + int(effect["offset_x_px"]), y + int(effect["offset_y_px"])),
        text,
        font=font,
        fill=shadow,
        stroke_width=stroke,
        stroke_fill=shadow,
    )
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def _draw_tracked_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    tracking: int,
    fill: tuple[int, int, int, int],
    config: dict[str, Any],
) -> None:
    effect = config["legibility"]["shadow"]
    widths = [draw.textlength(char, font=font) for char in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = (720 - total) / 2
    stroke = int(effect["stroke_width_px"])
    shadow = _color(config, "shadow", int(effect["opacity"]))
    stroke_fill = _color(config, "stroke", int(effect["stroke_opacity"]))
    for char, width in zip(text, widths):
        draw.text(
            (x + int(effect["offset_x_px"]), y + int(effect["offset_y_px"])),
            char,
            font=font,
            fill=shadow,
            stroke_width=stroke,
            stroke_fill=shadow,
        )
        draw.text((x, y), char, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
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
    layout = config["legibility"]["layouts"]["identity"]
    name_role = _role(config, "merchant_name")
    name_font = _fit_role(fields["nom"], config, "merchant_name")
    _draw_tracked_center(
        draw, fields["nom"].upper(), int(layout["brand_y_px"]), name_font,
        int(name_role["tracking_px"]), _color(config, name_role["color"]), config,
    )
    product_role = _role(config, "hero_product")
    product_font = _fit_role(fields["produit"], config, "hero_product")
    lines = _balanced_lines(fields["produit"], product_font, int(product_role["max_width_px"]))
    for index, line in enumerate(lines):
        _draw_center(
            draw, line, int(layout["product_y_px"]) + index * int(product_font.size * 0.94),
            product_font, _color(config, product_role["color"]), config,
        )
    rule_y = int(layout["rule_y_px"])
    draw.rounded_rectangle((260, rule_y, 460, rule_y + 5), radius=2, fill=_color(config, "accent"))
    return layer


def _offer(fields: dict[str, str], config: dict[str, Any], progress: float) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    layout = config["legibility"]["layouts"]["offer"]
    product_role = _role(config, "offer_product")
    product_font = _fit_role(fields["produit"], config, "offer_product")
    lines = _balanced_lines(fields["produit"], product_font, int(product_role["max_width_px"]))
    for index, line in enumerate(lines):
        _draw_center(
            draw, line, int(layout["product_y_px"]) + index * int(product_font.size * 0.95),
            product_font, _color(config, product_role["color"]), config,
        )
    price = _format_price(fields["prix"])
    price_role = _role(config, "price")
    price_font = _fit_role(price, config, "price")
    y = int(layout["price_y_px"]) + int((1.0 - progress) * int(layout["price_rise_px"]))
    _draw_center(draw, price, y, price_font, _color(config, price_role["color"]), config)
    return layer


def _hook(fields: dict[str, str], config: dict[str, Any]) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    layout = config["legibility"]["layouts"]["hook"]
    hook = fields.get("accroche", "")
    if hook:
        hook_role = _role(config, "hook")
        hook_font = _fit_role(hook, config, "hook")
        for index, line in enumerate(_balanced_lines(hook, hook_font, int(hook_role["max_width_px"]))):
            _draw_center(
                draw, line, int(layout["hook_y_px"]) + index * int(hook_font.size * 0.96),
                hook_font, _color(config, hook_role["color"]), config,
            )
    name_role = _role(config, "merchant_name")
    name_font = _fit_role(fields["nom"], config, "merchant_name")
    _draw_tracked_center(
        draw, fields["nom"].upper(), int(layout["brand_y_px"]), name_font,
        int(name_role["tracking_px"]), _color(config, name_role["color"]), config,
    )
    return layer


def _final(fields: dict[str, str], config: dict[str, Any]) -> Image.Image:
    layer = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    layout = config["legibility"]["layouts"]["final"]

    name_role = _role(config, "merchant_name")
    name_font = _fit_role(fields["nom"], config, "merchant_name")
    _draw_tracked_center(
        draw, fields["nom"].upper(), int(layout["brand_y_px"]), name_font,
        int(name_role["tracking_px"]), _color(config, name_role["color"]), config,
    )

    product_role = _role(config, "hero_product")
    product_font = _fit_role(fields["produit"], config, "hero_product")
    for index, line in enumerate(_balanced_lines(fields["produit"], product_font, int(product_role["max_width_px"]))):
        _draw_center(
            draw, line, int(layout["product_y_px"]) + index * int(product_font.size * 0.92),
            product_font, _color(config, product_role["color"]), config,
        )

    price_text = _format_price(fields["prix"])
    price_role = _role(config, "price")
    price_font = _fit_role(price_text, config, "price")
    _draw_center(
        draw, price_text, int(layout["price_y_px"]), price_font,
        _color(config, price_role["color"]), config,
    )

    location_role = _role(config, "location")
    location_font = _fit_role(fields["quartier"], config, "location")
    location_lines = _balanced_lines(fields["quartier"], location_font, int(location_role["max_width_px"]))
    location_y = int(layout["location_y_px"])
    for index, line in enumerate(location_lines):
        _draw_center(
            draw, line, location_y + index * int(location_font.size * 1.12), location_font,
            _color(config, location_role["color"]), config,
        )

    cta_role = _role(config, "cta")
    cta_font = _fit_role("COMMANDER MAINTENANT", config, "cta")
    cta_y = max(int(layout["cta_y_px"]), location_y + len(location_lines) * int(location_font.size * 1.12) + 13)
    _draw_tracked_center(
        draw, "COMMANDER MAINTENANT", cta_y, cta_font,
        int(cta_role["tracking_px"]), _color(config, cta_role["color"]), config,
    )

    phone_role = _role(config, "phone")
    phone_font = _fit_role(fields["whatsapp"], config, "phone")
    phone_width = draw.textlength(fields["whatsapp"], font=phone_font)
    dot = 24
    gap = 16
    total = dot + gap + phone_width
    x = (720 - total) / 2
    y = max(int(layout["phone_y_px"]), cta_y + int(cta_font.size * 1.55))
    draw.ellipse((x, y + 9, x + dot, y + 9 + dot), fill=_color(config, "whatsapp"))
    effect = config["legibility"]["shadow"]
    shadow = _color(config, "shadow", int(effect["opacity"]))
    stroke_fill = _color(config, "stroke", int(effect["stroke_opacity"]))
    phone_x = x + dot + gap
    draw.text(
        (phone_x + int(effect["offset_x_px"]), y + int(effect["offset_y_px"])),
        fields["whatsapp"], font=phone_font, fill=shadow,
        stroke_width=int(effect["stroke_width_px"]), stroke_fill=shadow,
    )
    draw.text(
        (phone_x, y), fields["whatsapp"], font=phone_font,
        fill=_color(config, phone_role["color"]),
        stroke_width=int(effect["stroke_width_px"]), stroke_fill=stroke_fill,
    )
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
    scrim = config["legibility"]["scrims"][block["id"]]
    frame_bgr = _soft_scrim(frame_bgr, top=float(scrim["top"]), bottom=float(scrim["bottom"]))
    if block["id"] == "T3_G01_IDENTITY":
        layer = _animate(_identity(fields, config), progress, opacity, 18)
    elif block["id"] == "T3_G02_OFFER":
        layer = _animate(_offer(fields, config, progress), progress, opacity, 14)
    elif block["id"] == "T3_G03_HOOK":
        layer = _animate(_hook(fields, config), progress, opacity, 16)
    else:
        layer = _animate(_final(fields, config), progress, opacity, 12)
    base = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    result = Image.alpha_composite(base, layer).convert("RGB")
    return cv2.cvtColor(np.asarray(result), cv2.COLOR_RGB2BGR), [block["id"]]
