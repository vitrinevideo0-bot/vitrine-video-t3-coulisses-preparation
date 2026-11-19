from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class T3AudioContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.music = json.loads((ROOT / "config/T3_MUSIC_PACK_V1_0_0.json").read_text(encoding="utf-8"))
        cls.mix = json.loads((ROOT / "config/T3_VOICE_MIX_V1_0_0.json").read_text(encoding="utf-8"))

    def test_exactly_four_owner_approved_music_derivatives(self) -> None:
        tracks = self.music["tracks"]
        self.assertEqual([item["choice"] for item in tracks], ["A", "B", "C", "D"])
        self.assertEqual([item["pixabay_id"] for item in tracks], [481806, 360659, 485507, 245452])
        self.assertTrue(all(item["audition_approved_by_owner"] for item in tracks))
        self.assertTrue(all(item["production_eligible"] for item in tracks))
        self.assertEqual(len(list((ROOT / "audio/music/t3-afrobeat-v1").glob("*.mp3"))), 4)

    def test_all_music_hashes_match(self) -> None:
        for item in self.music["tracks"]:
            path = ROOT / item["file"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), item["sha256"], path)

    def test_final_render_is_music_D_only(self) -> None:
        selection = self.music["selection_contract"]
        self.assertEqual(selection["final_render_choice"], "D")
        self.assertEqual(selection["final_render_variant_id"], "t3_music_245452")
        self.assertEqual(self.mix["final_render"]["music_choice"], "D")
        self.assertEqual(self.mix["final_render"]["music_variant_id"], "t3_music_245452")

    def test_full_pixabay_sources_are_not_bundled(self) -> None:
        source = json.loads((ROOT / "audio/music/t3-afrobeat-v1/source_manifest.json").read_text(encoding="utf-8"))
        names = {path.name for path in (ROOT / "audio/music/t3-afrobeat-v1").glob("*.mp3")}
        originals = {item["official_original_filename"] for item in source["tracks"]}
        self.assertFalse(names & originals)
        self.assertFalse(self.music["license_contract"]["original_full_tracks_bundled"])
        self.assertTrue(self.music["license_contract"]["standalone_redistribution_forbidden"])

    def test_voice_02_files_and_placements_are_locked(self) -> None:
        voice = self.mix["voice"]
        self.assertEqual(voice["voice_id"], "voice-02")
        self.assertEqual([item["start_s"] for item in voice["clips"]], [1.2, 6.8, 14.7, 21.8])
        self.assertEqual([item["end_s"] for item in voice["clips"]], [5.542, 10.469, 17.811, 26.618])
        self.assertEqual(len(voice["clips"]), 4)
        for item in voice["clips"]:
            for key, digest_key in (("source", "source_sha256"), ("processed", "processed_sha256")):
                path = ROOT / item[key]
                self.assertTrue(path.is_file(), path)
                self.assertEqual(sha256(path), item[digest_key], path)
        stem = ROOT / voice["stem_file"]
        self.assertEqual(sha256(stem), voice["stem_sha256"])

    def test_t1_ducking_contract(self) -> None:
        contract = self.mix["mix_contract"]
        self.assertEqual(contract["music_open_gain_db"], -3.0)
        self.assertEqual(contract["music_under_voice_gain_db"], -10.0)
        self.assertEqual(contract["duck_attack_ms"], 120)
        self.assertEqual(contract["duck_release_ms"], 450)
        self.assertEqual(contract["master_target_lufs"], -16.0)
        self.assertEqual(contract["master_true_peak_dbtp_max"], -2.0)

    def test_approved_v0_4_visual_is_immutable(self) -> None:
        visual = self.mix["visual_approved"]
        self.assertTrue(visual["owner_approved"])
        self.assertTrue(visual["immutable"])
        self.assertEqual(visual["file_sha256"], "cd61d3cf793874a8b7d2eb8fe694861048368ba64b01216395c6bba0eb879774")
        self.assertEqual(visual["video_bitstream_sha256"], "8e415063add70f5807e009b2306c6b1154b0ec19bf35d5b9350012a5f4abe666")


if __name__ == "__main__":
    unittest.main()
