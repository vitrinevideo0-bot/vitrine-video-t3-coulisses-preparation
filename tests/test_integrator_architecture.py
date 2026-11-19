from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from adapter.t3_adapter import MusicRepeatError, approved_variant_ids, build_render_job, select_music_variant
from tools.build_t3_capture_flow import build as build_capture_flow

ROOT = Path(__file__).resolve().parents[1]


class T3IntegratorArchitectureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical = json.loads((ROOT / "config/T3_COULISSES_TEMPLATE_V1_0_0.json").read_text(encoding="utf-8"))
        cls.music = json.loads((ROOT / "config/T3_MUSIC_PACK_V1_0_0.json").read_text(encoding="utf-8"))
        cls.capture = json.loads((ROOT / "config/T3_CAPTURE_FLOW_V1_0_0.json").read_text(encoding="utf-8"))

    def test_canonical_template_identity_and_ota_honesty(self) -> None:
        self.assertEqual(self.canonical["template_id"], "RESTAURATION-T3")
        self.assertEqual(self.canonical["version"], "1.0.0")
        self.assertEqual(self.canonical["audio_profile"], "afrobeat_amapiano")
        self.assertFalse(self.canonical["catalogue_preparation"]["ota_implemented"])
        self.assertFalse(self.canonical["catalogue_preparation"]["network_or_cloudflare_code_added"])
        self.assertFalse(self.canonical["catalogue_preparation"]["android_integration_implemented"])
        self.assertNotIn("http", json.dumps(self.canonical).lower())

    def test_canonical_template_matches_strict_schema(self) -> None:
        schema = json.loads((ROOT / "schemas/T3_template_package.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.canonical)

    def test_render_contract_fixtures_match_strict_schemas(self) -> None:
        cases = [
            ("schemas/render_job.schema.json", "fixtures/t3-coulisses/render_job.valid.json"),
            ("schemas/render_result.schema.json", "fixtures/t3-coulisses/render_result.valid.json"),
            ("schemas/render_error.schema.json", "fixtures/t3-coulisses/render_error.unsupported_media.json"),
            ("schemas/T3_music_pack.schema.json", "config/T3_MUSIC_PACK_V1_0_0.json"),
            ("schemas/T3_voice_mix.schema.json", "config/T3_VOICE_MIX_V1_0_0.json")
        ]
        for schema_name, fixture_name in cases:
            schema = json.loads((ROOT / schema_name).read_text(encoding="utf-8"))
            fixture = json.loads((ROOT / fixture_name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
            self.assertEqual(errors, [], (fixture_name, [error.message for error in errors]))

    def test_capture_flow_is_exactly_four_times_A_B_C(self) -> None:
        screens = self.capture["screens"]
        self.assertEqual(len(screens), 12)
        self.assertEqual([item["ordinal"] for item in screens], list(range(1, 13)))
        self.assertEqual([item["state"] for item in screens], [state for _ in range(4) for state in ("A_GUIDE", "B_RECORDING", "C_REVIEW")])
        self.assertEqual([screens[index]["capture_duration_ms"] for index in (1, 4, 7, 10)], [6000, 8000, 7000, 9000])
        self.assertTrue(all((ROOT / item["proof_png"]).is_file() for item in screens))

    def test_capture_flow_rebuild_has_no_drift(self) -> None:
        guide = json.loads((ROOT / "capture-guide/consignes_T3.json").read_text(encoding="utf-8"))
        self.assertEqual(build_capture_flow(guide), self.capture)

    def test_music_rotation_never_repeats_for_10000_successes(self) -> None:
        last = None
        observed = set()
        for index in range(10_000):
            selected = select_music_variant(f"t3-stress-{index:05d}", last)
            self.assertNotEqual(selected, last)
            observed.add(selected)
            last = selected
        self.assertEqual(observed, set(approved_variant_ids()))

    def test_music_rotation_is_deterministic_and_explicit_repeat_is_rejected(self) -> None:
        previous = approved_variant_ids()[0]
        first = select_music_variant("t3-same-job", previous)
        self.assertEqual(first, select_music_variant("t3-same-job", previous))
        with self.assertRaises(MusicRepeatError):
            select_music_variant("t3-repeat", previous, previous)

    def test_reference_render_D_does_not_replace_runtime_rotation(self) -> None:
        selection = self.music["selection_contract"]
        self.assertEqual(selection["reference_render"]["choice"], "D")
        self.assertTrue(selection["automatic_selection"]["offline"])
        self.assertEqual(selection["automatic_selection"]["explicit_repeat_policy"], "reject")
        self.assertEqual(selection["automatic_selection"]["state_update_policy"], "after_success_only")

    def test_adapter_rebuilds_committed_complete_fixture(self) -> None:
        fixture = json.loads((ROOT / "fixtures/t3-coulisses/render_job.valid.json").read_text(encoding="utf-8"))
        rebuilt = build_render_job(
            job_id=fixture["job_id"], merchant_payload=fixture["merchant_payload"], captures=fixture["captures"],
            explicit_variant_id=fixture["music"]["selected_variant_id"], voice_mode=fixture["voice"]["mode"], control_plane=fixture["control_plane"]
        )
        self.assertEqual(rebuilt, fixture)
        self.assertEqual(rebuilt, json.loads((ROOT / "demo/render_job_complete_v1_0_0.json").read_text(encoding="utf-8")))

    def test_cloudflare_boundary_is_separate_and_not_deployed(self) -> None:
        boundary = json.loads((ROOT / "integration-handoff/T3_CLOUDFLARE_BOUNDARY_V1.json").read_text(encoding="utf-8"))
        self.assertFalse(boundary["cloudflare_worker_in_template_repository"])
        self.assertFalse(boundary["cloudflare_deployed"])
        self.assertFalse(boundary["deployment_authorized"])
        self.assertEqual(boundary["production_render_plane"], "github_actions")
        self.assertFalse((ROOT / "cloudflare").exists())

    def test_release_publication_is_disabled_by_default(self) -> None:
        workflow = (ROOT / ".github/workflows/render-complete-voice-music-D.yml").read_text(encoding="utf-8")
        marker = "publish_prerelease:"
        block = workflow[workflow.index(marker):workflow.index("permissions:")]
        self.assertIn("default: false", block)
        self.assertNotIn("default: true", block)

    def test_package_spec_paths_exist_and_no_full_pixabay_sources(self) -> None:
        spec = json.loads((ROOT / "packages/t3-coulisses-v1/package_spec.json").read_text(encoding="utf-8"))
        self.assertTrue(all((ROOT / item["path"]).exists() for item in spec["include"]))
        source = json.loads((ROOT / "audio/music/t3-afrobeat-v1/source_manifest.json").read_text(encoding="utf-8"))
        originals = {item["official_original_filename"] for item in source["tracks"]}
        bundled = {path.name for path in (ROOT / "audio/music/t3-afrobeat-v1").glob("*.mp3")}
        self.assertFalse(originals & bundled)

    def test_protocol_deviation_is_explicit_not_hidden(self) -> None:
        deviations = self.canonical["known_protocol_deviations"]
        self.assertEqual([item["id"] for item in deviations], ["VOICE_CANDIDATE_EVIDENCE_COUNT"])
        self.assertIn("not_four_archived_candidate_files", deviations[0]["status"])


if __name__ == "__main__":
    unittest.main()
