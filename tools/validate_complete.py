#!/usr/bin/env python3
"""Independent validation of the single T3 complete server render."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 48_000
N = 30 * SR


def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, **kwargs)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(path: Path, channels: int) -> np.ndarray:
    raw = run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ar", str(SR), "-ac", str(channels), "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    data = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    return data.reshape(-1, channels) if channels > 1 else data


def probe(path: Path) -> dict[str, Any]:
    return json.loads(
        run(
            ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)],
            capture_output=True,
            text=True,
        ).stdout
    )


def stream_hash(path: Path) -> str:
    output = run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "hash", "-hash", "sha256", "-"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return output.split("=", 1)[1].lower()


def loudness(path: Path) -> dict[str, Any]:
    result = run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "loudnorm=I=-16:TP=-1:LRA=7:print_format=json", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    blocks = re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)
    if not blocks:
        raise RuntimeError(f"No loudness measurement for {path}")
    return json.loads(blocks[-1])


def sample_qc(audio: np.ndarray) -> dict[str, Any]:
    peak = float(np.max(np.abs(audio)))
    return {
        "sample_peak_dbfs": round(20 * math.log10(max(peak, 1e-12)), 3),
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
                envelope[attack_start:full_start], np.linspace(0, 1, full_start - attack_start, endpoint=False)
            )
        envelope[full_start:full_end] = 1
        if release_end > full_end:
            envelope[full_end:release_end] = np.maximum(
                envelope[full_end:release_end], np.linspace(1, 0, release_end - full_end, endpoint=False)
            )
    return envelope


def speech_ratio(voice: np.ndarray, music: np.ndarray, spans: list[tuple[float, float]], envelope: np.ndarray, open_db: float, under_db: float) -> float:
    gains_db = open_db + (under_db - open_db) * envelope
    ducked = music * (10 ** (gains_db / 20.0))[:, None]
    frame = int(0.02 * SR)
    voice_powers: list[float] = []
    music_powers: list[float] = []
    for start, end in spans:
        for index in range(int(start * SR) // frame, min(N // frame, int(math.ceil(end * SR / frame)))):
            left, right = index * frame, (index + 1) * frame
            vp = float(np.mean(voice[left:right] ** 2))
            if 10 * math.log10(max(vp, 1e-20)) <= -38:
                continue
            voice_powers.append(vp)
            music_powers.append(float(np.mean(ducked[left:right] ** 2)))
    return round(10 * math.log10(np.mean(voice_powers) / np.mean(music_powers)), 2)


def correlation(left: np.ndarray, right: np.ndarray) -> float:
    count = min(len(left), len(right))
    left = left[:count].astype(np.float64)
    right = right[:count].astype(np.float64)
    left -= np.mean(left)
    right -= np.mean(right)
    denominator = math.sqrt(float(np.dot(left, left)) * float(np.dot(right, right)))
    return float(np.dot(left, right) / denominator) if denominator else 0.0


def safe_music_samples(audio: np.ndarray) -> np.ndarray:
    # Regions strictly outside the 120 ms attack / 450 ms release ramps.
    regions = [(11.2, 14.4), (18.5, 21.5), (27.3, 29.7)]
    mono = np.mean(audio, axis=1) if audio.ndim == 2 else audio
    return np.concatenate([mono[int(start * SR):int(end * SR)] for start, end in regions])


def check(name: str, condition: bool, detail: Any = None) -> dict[str, Any]:
    return {"check": name, "status": "PASS" if bool(condition) else "FAIL", "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/t3-complete-v0.7.0")
    parser.add_argument("--music-config", type=Path, default=ROOT / "config/T3_MUSIC_PACK_V1_0_0.json")
    parser.add_argument("--mix-config", type=Path, default=ROOT / "config/T3_VOICE_MIX_V1_0_0.json")
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()

    music_config = json.loads(args.music_config.read_text(encoding="utf-8"))
    mix_config = json.loads(args.mix_config.read_text(encoding="utf-8"))
    report_path = args.output_dir / "T3_COMPLETE_RENDER_REPORT.json"
    if not report_path.exists():
        raise SystemExit("Render report is missing")
    render_report = json.loads(report_path.read_text(encoding="utf-8"))
    final_video = args.output_dir / mix_config["final_render"]["output_filename"]
    master_wav = args.output_dir / "T3_MASTER_AUDIO_VOIX_MUSIQUE_D_30S.wav"
    if not final_video.exists() or not master_wav.exists():
        raise SystemExit("Final video or master WAV is missing")

    tracks = music_config["tracks"]
    track_integrity = []
    decoded_tracks: dict[str, np.ndarray] = {}
    for track in tracks:
        path = ROOT / track["file"]
        actual = sha256(path) if path.exists() else None
        track_integrity.append({"choice": track["choice"], "file": track["file"], "expected": track["sha256"], "actual": actual, "match": actual == track["sha256"]})
        if path.exists():
            decoded_tracks[track["choice"]] = decode(path, 2)[:N]

    clips = mix_config["voice"]["clips"]
    reconstructed_voice = np.zeros(N, dtype=np.float64)
    placement_details = []
    clip_integrity = True
    for clip in clips:
        path = ROOT / clip["processed"]
        actual_hash = sha256(path) if path.exists() else None
        clip_integrity &= actual_hash == clip["processed_sha256"]
        samples = decode(path, 1)
        start = int(round(float(clip["start_s"]) * SR))
        reconstructed_voice[start:start + len(samples)] += samples[: N - start]
        measured_end = (start + len(samples)) / SR
        placement_details.append(
            {
                "scene": clip["scene"], "start_s": clip["start_s"], "configured_end_s": clip["end_s"],
                "measured_end_s": round(measured_end, 6), "decoded_samples": len(samples),
                "processed_sha256_match": actual_hash == clip["processed_sha256"],
            }
        )

    stem_path = ROOT / mix_config["voice"]["stem_file"]
    stem = decode(stem_path, 1)
    stem_difference = np.abs(stem - reconstructed_voice[: len(stem)])
    max_stem_error = float(np.max(stem_difference))
    nonzero_difference_samples = int(np.count_nonzero(stem_difference > 2e-7))
    spans = [(float(clip["start_s"]), float(clip["end_s"])) for clip in clips]
    duck = mix_config["mix_contract"]
    envelope = duck_envelope(spans, float(duck["duck_attack_ms"]) / 1000.0, float(duck["duck_release_ms"]) / 1000.0)
    selected_music = decoded_tracks.get("D")
    if selected_music is None:
        raise SystemExit("Selected music D could not be decoded")
    measured_speech_ratio = speech_ratio(stem, selected_music, spans, envelope, float(duck["music_open_gain_db"]), float(duck["music_under_voice_gain_db"]))

    master_audio = decode(master_wav, 2)
    final_audio = decode(final_video, 2)
    master_loudness = loudness(master_wav)
    final_loudness = loudness(final_video)
    master_qc = sample_qc(master_audio)
    final_qc = sample_qc(final_audio)

    # Independently identify the selected music in voice-free portions.
    master_safe = safe_music_samples(master_audio)
    identity_correlations = {
        choice: round(correlation(master_safe, safe_music_samples(audio)), 6)
        for choice, audio in decoded_tracks.items()
    }
    identified_choice = max(identity_correlations, key=identity_correlations.get)
    master_final_correlation = correlation(
        np.mean(master_audio[: min(len(master_audio), len(final_audio))], axis=1),
        np.mean(final_audio[: min(len(master_audio), len(final_audio))], axis=1),
    )

    media_probe = probe(final_video)
    video_streams = [stream for stream in media_probe["streams"] if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in media_probe["streams"] if stream.get("codec_type") == "audio"]
    video_stream = video_streams[0] if video_streams else {}
    audio_stream = audio_streams[0] if audio_streams else {}
    actual_stream_hash = stream_hash(final_video)
    expected_stream_hash = mix_config["visual_approved"]["video_bitstream_sha256"]
    mp4_files = sorted(path.name for path in args.output_dir.glob("*.mp4"))
    music_mp3_files = sorted((ROOT / "audio/music/t3-afrobeat-v1").glob("*.mp3"))
    source_original_names = {
        item["official_original_filename"]
        for item in json.loads((ROOT / "audio/music/t3-afrobeat-v1/source_manifest.json").read_text(encoding="utf-8"))["tracks"]
    }
    committed_music_names = {path.name for path in music_mp3_files}

    checks = [
        check("render_report_pass", render_report.get("status") == "PASS", render_report.get("status")),
        check("render_created_on_github_actions", render_report.get("rendered_on") == "github_actions", render_report.get("rendered_on")),
        check("one_complete_mp4_only", mp4_files == [final_video.name], mp4_files),
        check("exactly_four_music_derivatives", len(music_mp3_files) == 4 and len(tracks) == 4, len(music_mp3_files)),
        check("music_choices_A_B_C_D", [item["choice"] for item in tracks] == ["A", "B", "C", "D"], [item["choice"] for item in tracks]),
        check("approved_pixabay_ids", [item["pixabay_id"] for item in tracks] == [481806, 360659, 485507, 245452], [item["pixabay_id"] for item in tracks]),
        check("all_music_hashes_match", all(item["match"] for item in track_integrity), track_integrity),
        check("all_four_owner_approved", all(item["audition_approved_by_owner"] and item["production_eligible"] for item in tracks)),
        check("no_full_original_pixabay_file_bundled", not (source_original_names & committed_music_names), sorted(source_original_names & committed_music_names)),
        check("music_D_selected_in_contract", music_config["selection_contract"]["final_render_choice"] == "D" and mix_config["final_render"]["music_choice"] == "D"),
        check("music_D_identified_from_master_waveform", identified_choice == "D", {"identified": identified_choice, "correlations": identity_correlations}),
        check("music_D_identity_correlation", identity_correlations.get("D", 0) >= 0.90, identity_correlations.get("D")),
        check("voice_id_02", mix_config["voice"]["voice_id"] == "voice-02", mix_config["voice"]["voice_id"]),
        check("four_voice_clips", len(clips) == 4, len(clips)),
        check("voice_clip_hashes_match", clip_integrity, placement_details),
        check("voice_stem_hash_matches", sha256(stem_path) == mix_config["voice"]["stem_sha256"], sha256(stem_path)),
        check("voice_stem_exact_30s", len(stem) == N, len(stem)),
        check("voice_starts_exact", [item["start_s"] for item in clips] == [1.2, 6.8, 14.7, 21.8], [item["start_s"] for item in clips]),
        check("voice_ends_match_decoded_clips", all(abs(item["configured_end_s"] - item["measured_end_s"]) <= 0.001 for item in placement_details), placement_details),
        check("voice_stem_reconstructed_from_four_clips", max_stem_error <= 2e-7 and nonzero_difference_samples == 0, {"max_abs_error": max_stem_error, "samples_over_tolerance": nonzero_difference_samples}),
        check("duck_open_minus_3_db", duck["music_open_gain_db"] == -3.0, duck["music_open_gain_db"]),
        check("duck_under_voice_minus_10_db", duck["music_under_voice_gain_db"] == -10.0, duck["music_under_voice_gain_db"]),
        check("duck_attack_120ms", duck["duck_attack_ms"] == 120, duck["duck_attack_ms"]),
        check("duck_release_450ms", duck["duck_release_ms"] == 450, duck["duck_release_ms"]),
        check("speech_to_music_ratio", measured_speech_ratio >= 4.0, measured_speech_ratio),
        check("master_exact_30s", len(master_audio) == N, len(master_audio)),
        check("master_loudness", -16.5 <= float(master_loudness["input_i"]) <= -15.5, master_loudness["input_i"]),
        check("master_true_peak", float(master_loudness["input_tp"]) <= -1.9, master_loudness["input_tp"]),
        check("master_no_clipping_or_invalid_samples", master_qc["clipped_samples"] == master_qc["nan_count"] == master_qc["inf_count"] == 0, master_qc),
        check("aac_loudness", -16.6 <= float(final_loudness["input_i"]) <= -15.5, final_loudness["input_i"]),
        check("aac_true_peak", float(final_loudness["input_tp"]) <= -1.0, final_loudness["input_tp"]),
        check("aac_no_clipping_or_invalid_samples", final_qc["clipped_samples"] == final_qc["nan_count"] == final_qc["inf_count"] == 0, final_qc),
        check("aac_matches_master_program", master_final_correlation >= 0.98, round(master_final_correlation, 6)),
        check("one_video_stream", len(video_streams) == 1, len(video_streams)),
        check("one_audio_stream", len(audio_streams) == 1, len(audio_streams)),
        check("h264_yuv420p", video_stream.get("codec_name") == "h264" and video_stream.get("pix_fmt") == "yuv420p", [video_stream.get("codec_name"), video_stream.get("pix_fmt")]),
        check("dimensions_720x1280", (video_stream.get("width"), video_stream.get("height")) == (720, 1280), [video_stream.get("width"), video_stream.get("height")]),
        check("fps_30", video_stream.get("r_frame_rate") == "30/1" and video_stream.get("avg_frame_rate") == "30/1", [video_stream.get("r_frame_rate"), video_stream.get("avg_frame_rate")]),
        check("exactly_900_frames", int(video_stream.get("nb_read_frames") or video_stream.get("nb_frames") or 0) == 900, [video_stream.get("nb_frames"), video_stream.get("nb_read_frames")]),
        check("duration_30s", abs(float(media_probe["format"]["duration"]) - 30.0) <= 0.001, media_probe["format"]["duration"]),
        check("aac_stereo_48khz", audio_stream.get("codec_name") == "aac" and int(audio_stream.get("sample_rate", 0)) == 48000 and int(audio_stream.get("channels", 0)) == 2, [audio_stream.get("codec_name"), audio_stream.get("sample_rate"), audio_stream.get("channels")]),
        check("approved_visual_stream_bit_exact", actual_stream_hash == expected_stream_hash, {"expected": expected_stream_hash, "actual": actual_stream_hash}),
        check("approved_visual_is_immutable_v0_4", mix_config["visual_approved"]["immutable"] is True and mix_config["visual_approved"]["owner_approved"] is True),
        check("final_sha_matches_render_report", sha256(final_video) == render_report["final_video"]["sha256"], sha256(final_video)),
        check("all_builder_checks_pass", all(item["status"] == "PASS" for item in render_report.get("checks", [])), render_report.get("summary")),
    ]

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    validation = {
        "schema_version": "1.0.0",
        "template_id": "RESTAURATION-T3",
        "status": status,
        "scope": "Independent validation of the single complete GitHub server render",
        "selection": {"choice": "D", "title": "Dlozi Lam", "artist": "PremiumMusicOdyssey", "identified_from_waveform": identified_choice, "identity_correlations": identity_correlations},
        "voice": {"voice_id": "voice-02", "placements": placement_details, "stem_reconstruction_max_abs_error": max_stem_error},
        "mix": {"music_open_gain_db": duck["music_open_gain_db"], "music_under_voice_gain_db": duck["music_under_voice_gain_db"], "attack_ms": duck["duck_attack_ms"], "release_ms": duck["duck_release_ms"], "speech_to_music_db": measured_speech_ratio},
        "visual": {"expected_bitstream_sha256": expected_stream_hash, "actual_bitstream_sha256": actual_stream_hash, "unchanged": actual_stream_hash == expected_stream_hash},
        "audio": {"master_loudness": master_loudness, "final_loudness": final_loudness, "master_qc": master_qc, "final_qc": final_qc, "master_to_aac_correlation": round(master_final_correlation, 6)},
        "video": {"file": final_video.name, "sha256": sha256(final_video), "bytes": final_video.stat().st_size, "duration_s": float(media_probe["format"]["duration"]), "frames": int(video_stream.get("nb_read_frames") or video_stream.get("nb_frames") or 0)},
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "failed": sum(item["status"] == "FAIL" for item in checks), "total": len(checks)},
        "ffprobe": media_probe,
    }
    proof = args.proof or args.output_dir / "T3_COMPLETE_INDEPENDENT_VALIDATION.json"
    proof.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = args.output_dir / "RAPPORT_RENDU_COMPLET.md"
    markdown.write_text(
        "# T3 — rendu complet voix + musique D\n\n"
        f"**Validation indépendante : {status} — {validation['summary']['passed']}/{validation['summary']['total']} contrôles PASS.**\n\n"
        f"- Fichier : `{final_video.name}`\n"
        f"- SHA-256 : `{validation['video']['sha256']}`\n"
        "- 30,000 s · 720 × 1280 · 30 i/s · 900 images\n"
        "- Vidéo H.264/yuv420p copiée bit pour bit depuis le silencieux v0.4 approuvé\n"
        "- Musique : choix D — Dlozi Lam / PremiumMusicOdyssey\n"
        "- Voix : voice-02, quatre placements approuvés\n"
        "- Ducking : −3 dB hors parole, −10 dB sous parole, attaque 120 ms, relâchement 450 ms\n"
        f"- Audio final : {float(final_loudness['input_i']):.2f} LUFS, {float(final_loudness['input_tp']):.2f} dBTP, AAC stéréo 48 kHz\n"
        f"- Rapport parole/musique pré-master : +{measured_speech_ratio:.2f} dB\n"
        "- Échantillons écrêtés : 0\n",
        encoding="utf-8",
    )
    print(f"T3_COMPLETE_VALIDATION_{status} {validation['summary']['passed']}/{validation['summary']['total']} {proof}")
    if status != "PASS":
        for item in checks:
            if item["status"] == "FAIL":
                print("FAIL", item["check"], item["detail"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
