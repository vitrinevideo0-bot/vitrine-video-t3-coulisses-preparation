from __future__ import annotations

import unittest
import numpy as np

from engine import render_silent as r


class EffectsSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        yy, xx = np.mgrid[0:r.H, 0:r.W]
        self.frame = np.zeros((r.H, r.W, 3), dtype=np.uint8)
        self.frame[:, :, 0] = (xx % 256).astype(np.uint8)
        self.frame[:, :, 1] = (yy % 256).astype(np.uint8)
        self.frame[:, :, 2] = ((xx + yy) % 256).astype(np.uint8)

    def assert_frame(self, value: np.ndarray) -> None:
        self.assertEqual(value.shape, (r.H, r.W, 3))
        self.assertEqual(value.dtype, np.uint8)
        self.assertGreater(float(value.std()), 1.0)

    def test_core_families_return_valid_frames(self) -> None:
        functions = [
            lambda: r.tile_grid(self.frame, 0.5),
            lambda: r.geometric_arrow(self.frame, 0.5),
            lambda: r.radial_zoom(self.frame, 0.5),
            lambda: r.orange_flash(self.frame, self.frame[::-1].copy(), 0.5),
            lambda: r.hard_action_cut(self.frame, 0.6),
            lambda: r.selective_color(self.frame, 0.5),
            lambda: r.electric_flash(self.frame, 0.5),
            lambda: r.soft_overlay(self.frame, 0.5),
            lambda: r.strobe(self.frame, 4, 0.5),
            lambda: r.kaleidoscope(self.frame, self.frame[:, ::-1].copy(), 0.5),
            lambda: r.multi_panel(self.frame, 0.5),
            lambda: r.rotating_mask(self.frame, 0.5),
            lambda: r.radial_cross(self.frame, self.frame[::-1].copy(), 0.5),
            lambda: r.whip_zoom(self.frame, 0.5),
            lambda: r.panel_match(self.frame, 0.5),
            lambda: r.diagonal_rotating_wipe(self.frame, 0.75),
            lambda: r.background_fade(self.frame, 0.8),
        ]
        for function in functions:
            with self.subTest(function=function):
                self.assert_frame(function())


if __name__ == "__main__":
    unittest.main()
