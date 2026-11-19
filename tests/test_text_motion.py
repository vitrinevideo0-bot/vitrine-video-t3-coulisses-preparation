from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np
from PIL import Image, ImageDraw

from engine.text_motion import (
    _font,
    active_graphics,
    normalize_payload,
    render_text_motion,
    typography_audit,
    validate_text_config,
    visible_text_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class TextMotionContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads((ROOT / "config/T3_TEXT_MOTION_V0_3_0.json").read_text())
        self.job = json.loads((ROOT / "demo/render_job_silent_demo_v0_3.json").read_text())
        validate_text_config(self.config)
        self.fields = normalize_payload(self.job["merchant_payload"])

    def test_only_six_merchant_fields_are_allowed(self) -> None:
        self.assertEqual(list(self.fields), ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"])
        bad = dict(self.job["merchant_payload"], scene="S1")
        with self.assertRaises(ValueError):
            normalize_payload(bad)

    def test_exact_graphic_windows(self) -> None:
        expected = {
            17: [], 18: ["T3_G01_IDENTITY"], 155: ["T3_G01_IDENTITY"], 156: [],
            209: [], 210: ["T3_G02_OFFER"], 377: ["T3_G02_OFFER"], 378: [],
            449: [], 450: ["T3_G03_HOOK"], 605: ["T3_G03_HOOK"], 606: [],
            659: [], 660: ["T3_G04_FINAL"], 899: ["T3_G04_FINAL"],
        }
        for frame, ids in expected.items():
            self.assertEqual([item["id"] for item in active_graphics(self.config, frame)], ids)

    def test_visible_strings_are_merchant_values_or_single_cta(self) -> None:
        visible = visible_text_contract(self.fields, self.config)
        flattened = {text for values in visible.values() for text in values}
        allowed = set(self.fields.values()) | {"2 500 FCFA", "COMMANDER MAINTENANT"}
        self.assertTrue(flattened <= allowed)
        forbidden = {text.upper() for text in self.config["forbidden_visible_strings"]}
        self.assertFalse({text.upper() for text in flattened} & forbidden)

    def test_no_technical_overlay_on_blank_frames(self) -> None:
        frame = np.full((1280, 720, 3), 90, dtype=np.uint8)
        untouched, ids = render_text_motion(frame.copy(), 0, self.fields, self.config)
        self.assertEqual(ids, [])
        self.assertTrue(np.array_equal(untouched, frame))

    def test_merchant_motion_is_rendered_after_reveal(self) -> None:
        frame = np.full((1280, 720, 3), 90, dtype=np.uint8)
        rendered, ids = render_text_motion(frame.copy(), 60, self.fields, self.config)
        self.assertEqual(ids, ["T3_G01_IDENTITY"])
        self.assertGreater(float(np.mean(np.abs(rendered.astype(np.int16) - frame.astype(np.int16)))), 1.0)

    def test_small_text_legibility_is_locked_in_json(self) -> None:
        audit = typography_audit(self.config)
        self.assertTrue(audit["variable_font_weights_explicit"])
        for name in ("merchant_name", "location", "cta", "phone"):
            role = audit["roles"][name]
            self.assertGreaterEqual(role["weight"], 600)
            self.assertGreaterEqual(role["effective_minimum_at_preview_scale_px"], 11.0)
            self.assertGreaterEqual(role["contrast_ratio"], 7.0)

    def test_montserrat_weight_axis_is_actually_applied(self) -> None:
        def ink(weight: int) -> int:
            font = _font(self.config, "light_sans", 40, weight)
            image = Image.new("L", (500, 100), 0)
            ImageDraw.Draw(image).text((0, 0), "CASA TACOS", font=font, fill=255)
            return int(np.asarray(image).sum())

        self.assertGreater(ink(700), ink(100) * 4)


if __name__ == "__main__":
    unittest.main()
