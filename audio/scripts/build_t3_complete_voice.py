#!/usr/bin/env python3
"""Build the single approved T3 complete master on a GitHub runner.

The approved v0.4 video stream is copied bit-for-bit. The script mixes the
owner-approved French voice stem with music choice D (Dlozi Lam), applies the
T1 ducking contract, masters to -16 LUFS / -2 dBTP, and muxes AAC at 48 kHz.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SR = 48_000
TOTAL_S = 30.0
N = int(SR * TOTAL_S)


def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    print("RUN", " ".join(command), flush=True)
    return subprocess.run(command, check=True, **kwargs)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(path: Path, channels: int) -> np.ndarray:
    raw = run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
            "-ar", str(SR), "-ac", str(channels), "-f", "f32le", "-",
        ],
        capture_output=True,
    ).stdout
    data = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    return data.reshape(-1, channels) if channels > 1 else data


def write_wav(path: Path, data: np.ndarray, codec: str = "pcm_s24le") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = data.shape[1] if data.ndim == 2 else 1
    proc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR),
            "-ac", str(channels), "-i", "-", "-map_metadata", "-1",
            "-c:a", codec, str(path),
        ],
        stdin=subprocess.PIPE,
    )
    proc.communicate(np.asarray(data, dtype="<f4").tobytes())
    if proc.returncode:
        raise RuntimeError(f"Cannot write {path}")


def loudness(path: Path, target_i: float, target_tp: float) -> dict[str, Any]:
    result = run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
            "-map", "0:a:0", "-af",
            f"loudnorm=I={target_i}:TP={target_tp}:LRA=7:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    blocks = re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)
    if not blocks:
        raise RuntimeError(f"No loudness measurement for {path}")
    return json.loads(blocks[-1])


def master(source: Path, target: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    before = loudness(source, -16.0, -2.0)
    audio_filter = (
        "loudnorm=I=-16:TP=-2:LRA=7:"
        f"measured_I={before['input_i']}:measured_LRA={before['input_lra']}:"
        f"measured_TP={before['input_tp']}:measured_thresh={before['input_thresh']}:"
        f"offset={before['target_offset']}:linear=false:print_format=summary"
    )
    run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(source), "-map", "0:a:0",
            "-af", audio_filter, "-t", str(TOTAL_S), "-ar", str(SR), "-ac", "2",
            "-map_metadata", "-1", "-c:a", "pcm_s24le", str(target),
        ]
    )
    return before, loudness(target, -16.0, -2.0)


def stream_hash(path: Path) -> str:
    result = run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
            "-c", "copy", "-f", "hash", "-hash", "sha256", "-",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return result.split("=", 1)[1].lower()


def probe(path: Path) -> dict[str, Any]:
    return json.loads(
        run(
            [
                "ffprobe", "-v", "error", "-count_frames", "-show_streams",
                "-show_format", "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
        ).stdout
    )


def sample_qc(audio: np.ndarray) -> dict[str, Any]:
    peak = float(np.max(np.abs(audio)))
    return {
        "sample_peak_dbfs": round(float(20 * math.log10(max(peak, 1e-12))), 3),
        "clipped_samples": int(np.count_nonzero(np.abs(audio) >= 0.999999)),
        "nan_count": int(np.isnan(audio).sum()),
        "inf_count": int(np.isinf(audio).sum()),
    }


def duck_envelope(spans: list[tuple[float, float]], attack_s: float, release_s: float) -> np.ndarray:
    envelope = np.zeros(N, dtype=np.float64)
    for start, end in spans:
        attack_start = max(0, int(round((start - attack_s) * SR)))
        full_start = int(round(start * SR))
        full_end = min(N, int(round(end * SR)))
        release_end = min(N, int(round((end + release_s) * SR)))
        if full_start > attack_start:
            envelope[attack_start:full_start] = np.maximum(
                envelope[attack_start:full_start],
                np.linspace(0, 1, full_start - attack_start, endpoint=False),
            )
        envelope[full_start:full_end] = 1
        if release_end > full_end:
            envelope[full_end:release_end] = np.maximum(
                envelope[full_end:release_end],
                np.linspace(1, 0, release_end - full_end, endpoint=False),
            )
    return envelope


def speech_metrics(voice: np.ndarray, ducked_music: np.ndarray, spans: list[tuple[float, float]]) -> dict[str, Any]:
    frame = int(0.02 * SR)
    ratios: list[float] = []
    voice_powers: list[float] = []
    music_powers: list[float] = []
    by_scene: list[dict[str, Any]] = []
    for scene, (start, end) in enumerate(spans, 1):
        local: list[float] = []
        begin = int(start * SR) // frame
        finish = min(len(voice) // frame, int(math.ceil(end * SR / frame)))
        for index in range(begin, finish):
            left, right = index * frame, (index + 1) * frame
            vp = float(np.mean(voice[left:right] ** 2))
            if 10 * math.log10(max(vp, 1e-20)) <= -38:
                continue
            mp = float(np.mean(ducked_music[left:right] ** 2))
            ratio = 10 * math.log10(max(vp, 1e-20) / max(mp, 1e-20))
            ratios.append(ratio)
            local.append(ratio)
            voice_powers.append(vp)
            music_powers.append(mp)
        by_scene.append(
            {
                "scene": scene,
                "active_speech_s": round(len(local) * 0.02, 3),
                "median_speech_to_music_db": round(float(np.median(local)), 2),
                "p10_speech_to_music_db": round(float(np.percentile(local, 10)), 2),
            }
        )
    aggregate = 10 * math.log10(np.mean(voice_powers) / np.mean(music_powers))
    return {
        "method": "20 ms frames; active voice above -38 dBFS; pre-master stems",
        "active_speech_s": round(len(ratios) * 0.02, 3),
        "aggregate_speech_to_music_db": round(float(aggregate), 2),
        "median_speech_to_music_db": round(float(np.median(ratios)), 2),
        "p10_speech_to_music_db": round(float(np.percentile(ratios, 10)), 2),
        "scenes": by_scene,
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent-video", type=Path, required=True)
    parser.add_argument("--music-config", type=Path, default=ROOT / "config/T3_MUSIC_PACK_V1_0_0.json")
    parser.add_argument("--mix-config", type=Path, default=ROOT / "config/T3_VOICE_MIX_V1_0_0.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/t3-complete-v0.7.0")
    args = parser.parse_args()

    music_config = json.loads(args.music_config.read_text(encoding="utf-8"))
    mix_config = json.loads(args.mix_config.read_text(encoding="utf-8"))
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Contract locks: exactly four owner-approved choices, but only D is rendered.
    tracks = music_config["tracks"]
    require(len(tracks) == 4, "The music pack must contain exactly four tracks")
    require([track["choice"] for track in tracks] == ["A", "B", "C", "D"], "Choices must be A/B/C/D")
    require([track["pixabay_id"] for track in tracks] == [481806, 360659, 485507, 245452], "Unexpected Pixabay IDs")
    require(all(track["audition_approved_by_owner"] and track["production_eligible"] for track in tracks), "Every variant must be owner-approved")
    require(music_config["selection_contract"]["final_render_choice"] == "D", "Final music choice must be D")
    require(mix_config["final_render"]["music_variant_id"] == "t3_music_245452", "Final variant must be Dlozi Lam")
    require(mix_config["voice"]["voice_id"] == "voice-02", "Unexpected voice")

    verified_tracks = []
    for track in tracks:
        path = ROOT / track["file"]
        require(path.is_file(), f"Missing derivative: {path}")
        actual = sha256(path)
        require(actual == track["sha256"], f"Music SHA-256 mismatch: {path}")
        verified_tracks.append({"id": track["id"], "choice": track["choice"], "file": track["file"], "sha256": actual, "bytes": path.stat().st_size})
    selected = next(track for track in tracks if track["id"] == "t3_music_245452")
    music_path = ROOT / selected["file"]

    voice_config = mix_config["voice"]
    stem_path = ROOT / voice_config["stem_file"]
    require(stem_path.is_file(), f"Missing voice stem: {stem_path}")
    require(sha256(stem_path) == voice_config["stem_sha256"], "Voice stem SHA-256 mismatch")
    require(len(voice_config["clips"]) == 4, "Exactly four voice clips are required")
    for clip in voice_config["clips"]:
        for key, hash_key in (("source", "source_sha256"), ("processed", "processed_sha256")):
            path = ROOT / clip[key]
            require(path.is_file() and sha256(path) == clip[hash_key], f"Voice clip integrity failure: {path}")

    visual = mix_config["visual_approved"]
    require(args.silent_video.is_file(), f"Approved silent master missing: {args.silent_video}")
    require(sha256(args.silent_video) == visual["file_sha256"], "Approved silent master file SHA-256 mismatch")
    input_stream_hash = stream_hash(args.silent_video)
    require(input_stream_hash == visual["video_bitstream_sha256"], "Approved visual stream hash mismatch")
    silent_probe = probe(args.silent_video)
    silent_video_streams = [s for s in silent_probe["streams"] if s.get("codec_type") == "video"]
    silent_audio_streams = [s for s in silent_probe["streams"] if s.get("codec_type") == "audio"]
    require(len(silent_video_streams) == 1 and len(silent_audio_streams) == 0, "Approved base must contain one video stream and no audio")

    voice = decode(stem_path, 1)
    require(len(voice) == N, f"Voice stem must decode to {N} samples, got {len(voice)}")
    music = decode(music_path, 2)
    require(len(music) >= N, f"Music must contain at least {N} decoded samples")
    music = music[:N]

    spans = [(float(clip["start_s"]), float(clip["end_s"])) for clip in voice_config["clips"]]
    duck = mix_config["mix_contract"]
    envelope = duck_envelope(spans, float(duck["duck_attack_ms"]) / 1000.0, float(duck["duck_release_ms"]) / 1000.0)
    gain_db = float(duck["music_open_gain_db"]) + (
        float(duck["music_under_voice_gain_db"]) - float(duck["music_open_gain_db"])
    ) * envelope
    ducked_music = music * (10 ** (gain_db / 20.0))[:, None]
    premix = ducked_music + np.column_stack((voice, voice))
    intelligibility = speech_metrics(voice, ducked_music, spans)

    final_name = mix_config["final_render"]["output_filename"]
    final_video = output_dir / final_name
    master_wav = output_dir / "T3_MASTER_AUDIO_VOIX_MUSIQUE_D_30S.wav"
    with tempfile.TemporaryDirectory(prefix="t3-complete-") as temp_name:
        raw_wav = Path(temp_name) / "T3_PREMASTER.wav"
        write_wav(raw_wav, premix)
        before, _ = master(raw_wav, master_wav)

    run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(args.silent_video),
            "-i", str(master_wav), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
            "-ac", "2", "-t", "30", "-map_metadata", "-1", "-movflags", "+faststart",
            str(final_video),
        ]
    )

    wav_audio = decode(master_wav, 2)
    final_audio = decode(final_video, 2)
    wav_loudness = loudness(master_wav, -16.0, -2.0)
    final_loudness = loudness(final_video, -16.0, -1.0)
    output_probe = probe(final_video)
    video_streams = [s for s in output_probe["streams"] if s.get("codec_type") == "video"]
    audio_streams = [s for s in output_probe["streams"] if s.get("codec_type") == "audio"]
    output_stream_hash = stream_hash(final_video)
    wav_qc = sample_qc(wav_audio)
    final_qc = sample_qc(final_audio)
    video_stream = video_streams[0] if video_streams else {}
    audio_stream = audio_streams[0] if audio_streams else {}

    checks = {
        "four_owner_approved_music_derivatives_verified": len(verified_tracks) == 4,
        "final_music_is_choice_D_Dlozi_Lam": selected["choice"] == "D" and selected["pixabay_id"] == 245452,
        "voice_is_voice_02": voice_config["voice_id"] == "voice-02",
        "four_voice_placements": [clip["start_s"] for clip in voice_config["clips"]] == [1.2, 6.8, 14.7, 21.8],
        "ducking_minus_3_minus_10_db": duck["music_open_gain_db"] == -3.0 and duck["music_under_voice_gain_db"] == -10.0,
        "ducking_attack_release": duck["duck_attack_ms"] == 120 and duck["duck_release_ms"] == 450,
        "master_duration_samples": len(wav_audio) == N,
        "master_loudness": -16.5 <= float(wav_loudness["input_i"]) <= -15.5,
        "master_true_peak": float(wav_loudness["input_tp"]) <= -1.9,
        "aac_loudness": -16.6 <= float(final_loudness["input_i"]) <= -15.5,
        "aac_true_peak": float(final_loudness["input_tp"]) <= -1.0,
        "no_master_clipping": wav_qc["clipped_samples"] == 0 and wav_qc["nan_count"] == 0 and wav_qc["inf_count"] == 0,
        "no_aac_clipping": final_qc["clipped_samples"] == 0 and final_qc["nan_count"] == 0 and final_qc["inf_count"] == 0,
        "speech_over_music": intelligibility["aggregate_speech_to_music_db"] >= 4.0,
        "one_video_stream": len(video_streams) == 1,
        "one_audio_stream": len(audio_streams) == 1,
        "dimensions_720x1280": (video_stream.get("width"), video_stream.get("height")) == (720, 1280),
        "fps_30": video_stream.get("r_frame_rate") == "30/1",
        "frames_900": int(video_stream.get("nb_read_frames", "0")) == 900,
        "duration_30s": abs(float(output_probe["format"]["duration"]) - 30.0) <= 0.001,
        "aac_stereo_48khz": audio_stream.get("codec_name") == "aac" and int(audio_stream.get("sample_rate", "0")) == 48000 and int(audio_stream.get("channels", 0)) == 2,
        "visual_stream_bit_exact": output_stream_hash == visual["video_bitstream_sha256"] == input_stream_hash,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "schema_version": "1.0.0",
        "template_id": "RESTAURATION-T3",
        "status": status,
        "purpose": "single_complete_GitHub_server_render_with_owner_selected_music_D",
        "rendered_on": "github_actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local_preflight",
        "github": {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_number": os.environ.get("GITHUB_RUN_NUMBER"),
            "sha": os.environ.get("GITHUB_SHA"),
        },
        "contracts": {"music": str(args.music_config), "voice_mix": str(args.mix_config)},
        "verified_music_derivatives": verified_tracks,
        "selection": {
            "choice": "D", "variant_id": selected["id"], "pixabay_id": selected["pixabay_id"],
            "title": selected["title"], "artist": selected["artist"], "file": selected["file"],
            "sha256": selected["sha256"],
        },
        "voice": {
            "voice_id": voice_config["voice_id"], "stem_file": voice_config["stem_file"],
            "stem_sha256": voice_config["stem_sha256"],
            "placements": [{"scene": c["scene"], "start_s": c["start_s"], "end_s": c["end_s"], "text": c["text"]} for c in voice_config["clips"]],
        },
        "mix_contract": duck,
        "visual": {
            "input_file": args.silent_video.name, "input_file_sha256": sha256(args.silent_video),
            "input_video_bitstream_sha256": input_stream_hash,
            "output_video_bitstream_sha256": output_stream_hash,
            "bitstream_copy": output_stream_hash == input_stream_hash,
        },
        "pre_master": {"integrated_lufs": float(before["input_i"]), "true_peak_dbtp": float(before["input_tp"])},
        "master_wav": {
            "file": master_wav.name, "sha256": sha256(master_wav), "bytes": master_wav.stat().st_size,
            "duration_samples": len(wav_audio), "integrated_lufs": float(wav_loudness["input_i"]),
            "true_peak_dbtp": float(wav_loudness["input_tp"]), **wav_qc,
        },
        "final_video": {
            "file": final_video.name, "sha256": sha256(final_video), "bytes": final_video.stat().st_size,
            "duration_s": float(output_probe["format"]["duration"]), "frames": int(video_stream.get("nb_read_frames", "0")),
            "width": video_stream.get("width"), "height": video_stream.get("height"), "fps": video_stream.get("r_frame_rate"),
            "video_codec": video_stream.get("codec_name"), "pixel_format": video_stream.get("pix_fmt"),
            "audio_codec": audio_stream.get("codec_name"), "audio_sample_rate": int(audio_stream.get("sample_rate", "0")),
            "audio_channels": int(audio_stream.get("channels", 0)), "integrated_lufs": float(final_loudness["input_i"]),
            "true_peak_dbtp": float(final_loudness["input_tp"]), **final_qc,
        },
        "intelligibility": intelligibility,
        "checks": [{"check": key, "status": "PASS" if value else "FAIL"} for key, value in checks.items()],
        "summary": {"passed": sum(checks.values()), "failed": len(checks) - sum(checks.values())},
    }
    report_path = output_dir / "T3_COMPLETE_RENDER_REPORT.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(final_video), "sha256": sha256(final_video), "checks": report["summary"]}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
