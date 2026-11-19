from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
import wave

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = ROOT / "audio/voice/t3-voice-candidates-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class T3VoiceCandidateArchiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((CANDIDATE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        cls.report = json.loads((CANDIDATE_ROOT / "NORMALIZATION_REPORT.json").read_text(encoding="utf-8"))

    def test_manifest_matches_strict_schema(self) -> None:
        schema = json.loads((ROOT / "schemas/T3_voice_candidates.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(self.manifest))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_exactly_four_distinct_comparable_candidates(self) -> None:
        candidates = self.manifest["candidates"]
        self.assertEqual(self.manifest["candidate_count"], 4)
        self.assertEqual(len(candidates), 4)
        self.assertEqual([item["candidate"] for item in candidates], ["VOIX-A", "VOIX-B", "VOIX-C", "VOIX-D"])
        self.assertEqual(len({item["internal_voice_id"] for item in candidates}), 4)
        self.assertTrue(self.manifest["same_text_for_all"])
        self.assertEqual(self.manifest["language"], "fr")
        self.assertGreaterEqual(len(self.manifest["audition_text"].split()), 30)

    def test_source_and_listening_hashes_are_locked(self) -> None:
        for candidate in self.manifest["candidates"]:
            for file_key, hash_key in (("source_file", "source_sha256"), ("listening_file", "listening_sha256")):
                path = CANDIDATE_ROOT / candidate[file_key]
                self.assertTrue(path.is_file(), path)
                self.assertEqual(sha256(path), candidate[hash_key], path)

    def test_listening_wavs_are_48khz_mono_16bit_without_retime(self) -> None:
        for candidate in self.manifest["candidates"]:
            path = CANDIDATE_ROOT / candidate["listening_file"]
            with wave.open(str(path), "rb") as wav:
                self.assertEqual(wav.getframerate(), 48000)
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                duration = wav.getnframes() / wav.getframerate()
            self.assertAlmostEqual(duration, candidate["duration_seconds"], places=3)
            self.assertFalse(candidate["retimed"])

    def test_normalization_report_has_four_passed_outputs(self) -> None:
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["candidate_count"], 4)
        self.assertTrue(self.report["same_text"])
        self.assertTrue(self.report["retiming_forbidden"])
        for item in self.report["candidates"]:
            self.assertGreaterEqual(item["integrated_lufs"], -20.15)
            self.assertLessEqual(item["integrated_lufs"], -19.85)
            self.assertLessEqual(item["true_peak_dbtp"], -3.0)
            self.assertFalse(item["retimed"])

    def test_owner_selected_candidate_A_matching_current_master_voice(self) -> None:
        mix = json.loads((ROOT / "config/T3_VOICE_MIX_V1_0_0.json").read_text(encoding="utf-8"))
        mapping = {item["candidate"]: item["internal_voice_id"] for item in self.manifest["candidates"]}
        gate = self.manifest["owner_gate"]
        self.assertEqual(mapping["VOIX-A"], mix["voice"]["voice_id"])
        self.assertEqual(self.manifest["status"], "owner_selected")
        self.assertEqual(gate["decision"], "selected")
        self.assertEqual(gate["selected_candidate"], "VOIX-A")
        self.assertEqual(gate["selected_internal_voice_id"], "voice-02")
        self.assertFalse(gate["silence_is_approval"])
        approval = json.loads((ROOT / gate["approval_record"]).read_text(encoding="utf-8"))
        self.assertEqual(approval["selected_option_id"], "voice_a")
        self.assertEqual(approval["selected_internal_voice_id"], mix["voice"]["voice_id"])
        self.assertTrue(approval["same_as_previously_approved_final_voice"])

    def test_listening_board_references_each_candidate_once(self) -> None:
        board = (CANDIDATE_ROOT / "T3_ECOUTE_4_VOIX.html").read_text(encoding="utf-8")
        for candidate in self.manifest["candidates"]:
            self.assertEqual(board.count(candidate["listening_file"]), 1)
            self.assertIn(candidate["candidate"].replace("-", "‑"), board)


if __name__ == "__main__":
    unittest.main()
