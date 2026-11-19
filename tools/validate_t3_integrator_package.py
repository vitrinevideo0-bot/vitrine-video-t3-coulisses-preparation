#!/usr/bin/env python3
"""Validate the T3 integrator ZIP after clean extraction."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check(name: str, condition: bool, detail=None) -> dict:
    return {"check": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def stream_hash(path: Path) -> str:
    output = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy",
        "-f", "hash", "-hash", "sha256", "-"
    ], text=True).strip()
    return output.split("=", 1)[1].lower()


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)
    ], text=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads((ROOT / "packages/t3-coulisses-v1/package_spec.json").read_text(encoding="utf-8"))
    package_id = spec["package_id"]
    checks: list[dict] = []

    with zipfile.ZipFile(args.zip) as archive:
        names = archive.namelist()
        safe_names = all(
            not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts and name.startswith(package_id + "/")
            for name in names
        )
        checks.append(check("zip_paths_safe_and_single_root", safe_names, names[:5]))
        with tempfile.TemporaryDirectory(prefix="t3-package-validate-") as temp_name:
            archive.extractall(temp_name)
            package_root = Path(temp_name) / package_id
            manifest = json.loads((package_root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
            canonical = json.loads((package_root / "config/T3_COULISSES_TEMPLATE_V1_0_0.json").read_text(encoding="utf-8"))
            capture_flow = json.loads((package_root / "config/T3_CAPTURE_FLOW_V1_0_0.json").read_text(encoding="utf-8"))
            music_pack = json.loads((package_root / "config/T3_MUSIC_PACK_V1_0_0.json").read_text(encoding="utf-8"))

            manifest_matches = True
            for item in manifest["files"]:
                path = package_root / item["path"]
                manifest_matches &= path.is_file() and path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"]
            checks.append(check("manifest_all_files_sizes_hashes", manifest_matches, manifest["file_count"]))
            checks.append(check("manifest_count", manifest["file_count"] == len(manifest["files"]), [manifest["file_count"], len(manifest["files"])]))

            checksum_ok = True
            checksum_lines = (package_root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
            for line in checksum_lines:
                digest, relative = line.split("  ", 1)
                path = package_root / relative
                checksum_ok &= path.is_file() and sha256(path) == digest
            checks.append(check("sha256sums_all_match", checksum_ok, len(checksum_lines)))

            schema_cases = [
                ("schemas/T3_template_package.schema.json", "config/T3_COULISSES_TEMPLATE_V1_0_0.json"),
                ("schemas/T3_music_pack.schema.json", "config/T3_MUSIC_PACK_V1_0_0.json"),
                ("schemas/T3_voice_mix.schema.json", "config/T3_VOICE_MIX_V1_0_0.json"),
                ("schemas/render_job.schema.json", "fixtures/t3-coulisses/render_job.valid.json"),
                ("schemas/render_result.schema.json", "fixtures/t3-coulisses/render_result.valid.json"),
                ("schemas/render_error.schema.json", "fixtures/t3-coulisses/render_error.unsupported_media.json")
            ]
            schema_ok = True
            schema_details = []
            for schema_name, instance_name in schema_cases:
                definition = json.loads((package_root / schema_name).read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(definition)
                errors = list(Draft202012Validator(definition, format_checker=FormatChecker()).iter_errors(json.loads((package_root / instance_name).read_text(encoding="utf-8"))))
                schema_ok &= not errors
                schema_details.append({"instance": instance_name, "errors": [error.message for error in errors]})
            checks.append(check("strict_schemas_and_fixtures", schema_ok, schema_details))

            checks.append(check("canonical_identity", canonical["template_id"] == "RESTAURATION-T3" and canonical["version"] == "1.0.0" and canonical["audio_profile"] == "afrobeat_amapiano"))
            checks.append(check("canonical_audio_profile_semantic", all(token not in canonical["audio_profile"].lower() for token in (".mp3", "dlozi", "245452", "t3_music_")), canonical["audio_profile"]))
            prep = canonical["catalogue_preparation"]
            checks.append(check("ota_explicitly_not_implemented", prep["ota_implemented"] is False))
            checks.append(check("no_network_or_cloudflare_code_in_template", prep["network_or_cloudflare_code_added"] is False and not (package_root / "cloudflare").exists()))
            checks.append(check("android_integration_not_overclaimed", prep["android_integration_implemented"] is False))

            screens = capture_flow["screens"]
            checks.append(check("exactly_twelve_stable_screens", len(screens) == 12 and [item["ordinal"] for item in screens] == list(range(1, 13)), len(screens)))
            checks.append(check("four_scenes_A_B_C", [item["state"] for item in screens] == [state for _ in range(4) for state in ("A_GUIDE", "B_RECORDING", "C_REVIEW")]))
            checks.append(check("capture_durations_6_8_7_9", [screens[index]["capture_duration_ms"] for index in (1, 4, 7, 10)] == [6000, 8000, 7000, 9000]))
            checks.append(check("capture_audio_identity_speed", all(item.get("capture", {}).get("source_speed", 1.0) == 1.0 for item in screens)))
            checks.append(check("all_screen_proofs_present", all((package_root / item["proof_png"]).is_file() for item in screens)))

            mp3s = sorted((package_root / "audio/music/t3-afrobeat-v1").glob("*.mp3"))
            checks.append(check("exactly_four_music_derivatives", len(mp3s) == 4, [item.name for item in mp3s]))
            checks.append(check("four_tracks_owner_approved", len(music_pack["tracks"]) == 4 and all(item["audition_approved_by_owner"] for item in music_pack["tracks"])))
            source_manifest = json.loads((package_root / "audio/music/t3-afrobeat-v1/source_manifest.json").read_text(encoding="utf-8"))
            originals = {item["official_original_filename"] for item in source_manifest["tracks"]}
            checks.append(check("no_full_pixabay_source", not (originals & {path.name for path in package_root.rglob("*.mp3")})))

            sys.path.insert(0, str(package_root))
            module = importlib.import_module("adapter.t3_adapter")
            variants = module.approved_variant_ids()
            repeat_ok = True
            last = None
            counts = {item: 0 for item in variants}
            for index in range(10_000):
                selected = module.select_music_variant(f"t3-stress-{index:05d}", last)
                repeat_ok &= selected != last
                counts[selected] += 1
                last = selected
            checks.append(check("music_rotation_10000_zero_adjacent_repeat", repeat_ok, counts))
            deterministic = module.select_music_variant("t3-determinism-sample", variants[0]) == module.select_music_variant("t3-determinism-sample", variants[0])
            checks.append(check("music_rotation_deterministic", deterministic))
            try:
                module.select_music_variant("t3-explicit-repeat", variants[0], variants[0])
                explicit_rejected = False
            except module.MusicRepeatError:
                explicit_rejected = True
            checks.append(check("explicit_repeat_rejected", explicit_rejected))

            golden = spec["external_golden_master"]
            golden_path = package_root / golden["package_path"]
            checks.append(check("golden_master_hash_and_size", sha256(golden_path) == golden["sha256"] and golden_path.stat().st_size == golden["bytes"], sha256(golden_path)))
            media = probe(golden_path)
            video = next(stream for stream in media["streams"] if stream.get("codec_type") == "video")
            audio = next(stream for stream in media["streams"] if stream.get("codec_type") == "audio")
            checks.append(check("golden_30s_900_frames_720x1280_30fps", abs(float(media["format"]["duration"]) - 30.0) <= 0.001 and int(video.get("nb_read_frames") or video.get("nb_frames")) == 900 and (video["width"], video["height"], video["r_frame_rate"]) == (720, 1280, "30/1")))
            checks.append(check("golden_aac_stereo_48khz", audio["codec_name"] == "aac" and int(audio["sample_rate"]) == 48000 and int(audio["channels"]) == 2))
            actual_stream_hash = stream_hash(golden_path)
            checks.append(check("golden_visual_stream_immutable", actual_stream_hash == golden["video_bitstream_sha256"], actual_stream_hash))

            forbidden_names = {".env", "hosts.yml", "credentials", "credentials.json", ".netrc"}
            checks.append(check("no_secret_files", not any(path.name in forbidden_names for path in package_root.rglob("*"))))
            text_extensions = {".json", ".md", ".py", ".yml", ".yaml", ".toml", ".js", ".html", ".txt"}
            token_pattern = re.compile(r"(?:gh[opsu]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|CLOUDFLARE_API_TOKEN\s*=\s*[^$<\s])")
            leaked = []
            for path in package_root.rglob("*"):
                if path.is_file() and path.suffix in text_extensions:
                    if token_pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                        leaked.append(path.relative_to(package_root).as_posix())
            checks.append(check("no_embedded_secret_values", not leaked, leaked))
            checks.append(check("handoff_declares_cloudflare_not_deployed", json.loads((package_root / "integration-handoff/T3_CLOUDFLARE_BOUNDARY_V1.json").read_text(encoding="utf-8"))["cloudflare_deployed"] is False))
            deviations = canonical["known_protocol_deviations"]
            checks.append(check("known_protocol_deviation_declared_not_hidden", len(deviations) == 1 and deviations[0]["id"] == "VOICE_CANDIDATE_EVIDENCE_COUNT", deviations))

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    proof = {
        "schema_version": "1.0.0", "status": status, "scope": "Clean extraction validation of RESTAURATION-T3 integrator package",
        "zip": {"file": args.zip.name, "bytes": args.zip.stat().st_size, "sha256": sha256(args.zip)},
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "failed": sum(item["status"] == "FAIL" for item in checks), "total": len(checks)},
        "strict_universal_protocol_100_percent": False,
        "declared_deviation": "Four comparable candidate voice demo files are not archived; selected voice and final human approval are proven."
    }
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    args.proof.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"T3_INTEGRATOR_PACKAGE_{status} {proof['summary']['passed']}/{proof['summary']['total']} {args.proof}")
    if status != "PASS":
        for item in checks:
            if item["status"] == "FAIL":
                print("FAIL", item["check"], item["detail"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
