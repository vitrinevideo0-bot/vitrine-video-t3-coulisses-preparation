from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class T3ContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads((ROOT / "reverse-engineering/T3_TRANSITIONS_30S.json").read_text())
        self.manifest = json.loads((ROOT / "rushes/manifest.json").read_text())
        self.questions = json.loads((ROOT / "form/questions_T3.json").read_text())
        self.guide = json.loads((ROOT / "capture-guide/consignes_T3.json").read_text())

    def test_exact_format(self) -> None:
        fmt = self.contract["format_contract_candidate"]
        self.assertEqual((fmt["width"], fmt["height"], fmt["fps"], fmt["total_frames"]), (720, 1280, 30, 900))
        self.assertEqual(fmt["scene_boundaries_frames"], [0, 180, 420, 630, 900])

    def test_four_scenes_sum_to_30(self) -> None:
        durations = [scene["duration_seconds"] for scene in self.manifest["scenes"]]
        self.assertEqual(durations, [6, 8, 7, 9])
        self.assertEqual(sum(durations), 30)
        self.assertEqual([scene["secondes"] for scene in self.guide["scenes"]], durations)

    def test_all_17_events_and_profiles(self) -> None:
        events = self.contract["timeline_events"]
        profiles = self.contract["transition_parameter_profiles"]
        self.assertEqual(len(events), 17)
        self.assertTrue(all(event["parameter_profile"] in profiles for event in events))
        covered = {event["transition_id"] for event in events}
        required = {item["id"] for item in self.contract["mandatory_transition_families"] + self.contract["additional_observed_editing_events"] if item["required"]}
        self.assertTrue(required <= covered)

    def test_no_event_overlap_and_exact_seconds(self) -> None:
        events = self.contract["timeline_events"]
        for left, right in zip(events, events[1:]):
            self.assertLess(left["frames"][1], right["frames"][0])
        for event in events:
            start, end = event["frames"]
            self.assertAlmostEqual(event["start_seconds_exact"], start / 30, places=6)
            self.assertAlmostEqual(event["end_seconds_exclusive_exact"], (end + 1) / 30, places=6)

    def test_panel_match_separator_lines_are_forbidden(self) -> None:
        profile = self.contract["transition_parameter_profiles"]["R4_MULTI_PANEL_MATCH_CUT"]
        self.assertFalse(self.contract["owner_constraints"]["visible_transition_guides_allowed"])
        self.assertEqual(profile["gap_px"], 0)
        self.assertEqual(profile["border_px"], 0)
        self.assertFalse(profile["separator_lines"])
        self.assertIsNone(profile["separator_color"])
        event = next(item for item in self.contract["timeline_events"] if item["transition_id"] == "R4_MULTI_PANEL_MATCH_CUT")
        self.assertIn("borderless", event["variant"])

    def test_questions_and_languages_are_approved(self) -> None:
        self.assertEqual(self.questions["status"], "owner_approved")
        self.assertEqual([field["id"] for field in self.questions["fields"]], ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"])
        self.assertFalse(self.questions["fields"][-1]["required"])
        footer = self.guide["mention_langues_commune"].lower()
        self.assertTrue(all(language in footer for language in ("français", "fon", "anglais")))

    def test_raw_media_is_not_committed_or_published(self) -> None:
        self.assertFalse(self.manifest["license"]["raw_media_committed"])
        self.assertFalse(self.manifest["license"]["raw_media_published_as_artifact"])
        self.assertEqual(len(self.manifest["scenes"]), 4)
        self.assertTrue(all(len(scene["sha256"]) == 64 for scene in self.manifest["scenes"]))


if __name__ == "__main__":
    unittest.main()
