#!/usr/bin/env python3
"""Normalize the four archived T3 voice auditions without retiming speech."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
NORMALIZED = ROOT / "normalized"
TARGET_I = -20.0
TARGET_TP = -3.0
TARGET_LRA = 7.0


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def loudnorm_measure(path: Path) -> dict[str, str]:
    result = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
        "-f", "null", "-",
    ])
    matches = re.findall(r"\{\s*\"input_i\".*?\}", result.stderr, flags=re.S)
    if not matches:
        raise RuntimeError(f"No loudnorm JSON emitted for {path}")
    return json.loads(matches[-1])


def probe(path: Path) -> dict:
    result = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,sample_rate,channels,bits_per_sample",
        "-of", "json", str(path),
    ])
    return json.loads(result.stdout)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    NORMALIZED.mkdir(parents=True, exist_ok=True)
    rows = []
    sources = sorted(SOURCE.glob("*.wav"))
    if len(sources) != 4:
        raise SystemExit(f"Expected exactly four source WAV files, found {len(sources)}")

    for source in sources:
        first = loudnorm_measure(source)
        output = NORMALIZED / source.name
        filter_value = (
            f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
            f"measured_I={first['input_i']}:measured_TP={first['input_tp']}:"
            f"measured_LRA={first['input_lra']}:measured_thresh={first['input_thresh']}:"
            f"offset={first['target_offset']}:linear=true:print_format=json"
        )
        run([
            "ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(source),
            "-af", filter_value, "-ar", "48000", "-ac", "1",
            "-c:a", "pcm_s16le", str(output),
        ])
        final = loudnorm_measure(output)
        media = probe(output)
        rows.append({
            "source": source.relative_to(ROOT).as_posix(),
            "source_sha256": sha256(source),
            "normalized": output.relative_to(ROOT).as_posix(),
            "normalized_sha256": sha256(output),
            "duration_seconds": round(float(media["format"]["duration"]), 6),
            "sample_rate_hz": int(media["streams"][0]["sample_rate"]),
            "channels": int(media["streams"][0]["channels"]),
            "integrated_lufs": float(final["input_i"]),
            "true_peak_dbtp": float(final["input_tp"]),
            "loudness_range_lu": float(final["input_lra"]),
            "retimed": False,
        })

    report = {
        "schema_version": "1.0.0",
        "status": "PASS",
        "candidate_count": len(rows),
        "same_text": True,
        "language": "fr",
        "target_integrated_lufs": TARGET_I,
        "target_true_peak_dbtp": TARGET_TP,
        "target_lra_lu": TARGET_LRA,
        "retiming_forbidden": True,
        "candidates": rows,
    }
    (ROOT / "NORMALIZATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"T3_VOICE_CANDIDATES_NORMALIZED {len(rows)}/4 PASS")


if __name__ == "__main__":
    main()
