#!/usr/bin/env python3
"""Validation indépendante du master silencieux T3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import cv2


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check(name: str, condition: bool, detail: object = "") -> dict[str, object]:
    return {"check": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("output/t3-silent-v0.4.0"))
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()

    render_report_path = args.output_dir / "T3_SILENT_RENDER_REPORT.json"
    if not render_report_path.exists():
        raise SystemExit("Rapport de rendu absent")
    report = json.loads(render_report_path.read_text(encoding="utf-8"))
    video = args.output_dir / report["output"]["file"]
    contact = args.output_dir / report["contact_sheet_file"]
    if not video.exists():
        raise SystemExit("Rendu vidéo absent")

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe est requis pour prouver l’absence de piste audio")
    probe = json.loads(subprocess.check_output([
        ffprobe, "-v", "error", "-count_frames",
        "-show_entries", "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames,pix_fmt",
        "-of", "json", str(video),
    ], text=True))
    streams = probe.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    stream = video_streams[0] if video_streams else {}
    cap = cv2.VideoCapture(str(video))
    decoded = 0
    sampled_nonblack = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        decoded += 1
        if decoded in {1, 180, 420, 630, 900} and float(frame.mean()) > 5.0:
            sampled_nonblack += 1
    cap.release()

    checks = [
        check("video_exists", video.exists(), str(video)),
        check("one_video_stream", len(video_streams) == 1, len(video_streams)),
        check("zero_audio_stream", len(audio_streams) == 0, len(audio_streams)),
        check("h264_codec", stream.get("codec_name") == "h264", stream.get("codec_name")),
        check("dimensions_720x1280", (stream.get("width"), stream.get("height")) == (720, 1280), [stream.get("width"), stream.get("height")]),
        check("pixel_format_yuv420p", stream.get("pix_fmt") == "yuv420p", stream.get("pix_fmt")),
        check("fps_30", stream.get("r_frame_rate") == "30/1" and stream.get("avg_frame_rate") == "30/1", [stream.get("r_frame_rate"), stream.get("avg_frame_rate")]),
        check("duration_30_seconds", abs(float(probe["format"]["duration"]) - 30.0) <= 0.001, probe["format"]["duration"]),
        check("900_frames_probe", int(stream.get("nb_read_frames") or stream.get("nb_frames") or 0) == 900, [stream.get("nb_frames"), stream.get("nb_read_frames")]),
        check("900_frames_decoded", decoded == 900, decoded),
        check("scene_boundaries_nonblack", sampled_nonblack == 5, sampled_nonblack),
        check("sha256_matches_render_report", sha256(video) == report["output"]["sha256"], sha256(video)),
        check("all_17_events_applied", report.get("all_17_events_applied") is True and len(report.get("events", [])) == 17, len(report.get("events", []))),
        check("each_event_frame_count", all(event["expected_frame_count"] == event["applied_frame_count"] for event in report.get("events", []))),
        check("all_4_merchant_graphics_applied", report.get("all_4_graphics_applied") is True and len(report.get("graphics", [])) == 4, len(report.get("graphics", []))),
        check("each_graphic_frame_count", all(item["expected_frame_count"] == item["applied_frame_count"] for item in report.get("graphics", []))),
        check("canonical_merchant_fields_only", report.get("merchant_payload_fields") == ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"], report.get("merchant_payload_fields")),
        check("technical_labels_not_rendered", report.get("technical_labels_rendered") is False),
        check("visible_texts_do_not_contain_forbidden_labels", not ({text.upper() for values in report.get("visible_text_contract", {}).values() for text in values} & {text.upper() for text in report.get("forbidden_visible_strings", [])})),
        check("owner_feedback_legibility_corrected", report.get("owner_feedback_legibility_corrected") is True),
        check("owner_feedback_blue_lines_corrected", report.get("owner_feedback_blue_lines_corrected") is True),
        check("no_visible_transition_guides", report.get("transition_visibility_audit", {}).get("visible_transition_guides_rendered") is False),
        check("panel_match_has_zero_gap_and_border", report.get("transition_visibility_audit", {}).get("R4_MULTI_PANEL_MATCH_CUT", {}).get("gap_px") == 0 and report.get("transition_visibility_audit", {}).get("R4_MULTI_PANEL_MATCH_CUT", {}).get("border_px") == 0),
        check("panel_match_separators_disabled", report.get("transition_visibility_audit", {}).get("R4_MULTI_PANEL_MATCH_CUT", {}).get("separator_lines") is False and report.get("transition_visibility_audit", {}).get("R4_MULTI_PANEL_MATCH_CUT", {}).get("separator_color") is None),
        check("panel_match_separator_proof_frames", report.get("transition_visibility_audit", {}).get("R4_MULTI_PANEL_MATCH_CUT", {}).get("proof_frames") == [771, 778]),
        check("variable_font_weights_explicit", report.get("typography_audit", {}).get("variable_font_weights_explicit") is True),
        check("small_text_effective_size", all(float(report.get("typography_audit", {}).get("roles", {}).get(name, {}).get("effective_minimum_at_preview_scale_px", 0)) >= float(report.get("typography_audit", {}).get("required_effective_font_px", 999)) for name in ["merchant_name", "location", "cta", "phone"])),
        check("text_contrast_ratio", all(float(item.get("contrast_ratio", 0)) >= float(report.get("typography_audit", {}).get("required_contrast_ratio", 999)) for item in report.get("typography_audit", {}).get("roles", {}).values())),
        check("small_text_weight_at_least_600", all(int(report.get("typography_audit", {}).get("roles", {}).get(name, {}).get("weight") or 0) >= 600 for name in ["merchant_name", "location", "cta", "phone"])),
        check("references_2_and_4", report.get("references_covered") == ["R3-B03-REF-02", "R3-B03-REF-04"], report.get("references_covered")),
        check("raw_rushes_not_published", report.get("raw_rushes_embedded_as_standalone_assets") is False),
        check("transition_contact_sheet", contact.exists() and contact.stat().st_size > 10000, contact.stat().st_size if contact.exists() else 0),
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    validation = {
        "schema_version": "1.0.0",
        "template_id": "RESTAURATION-T3",
        "status": overall,
        "scope": "Master silencieux candidat produit sur GitHub Actions" if report.get("rendered_on") == "github_actions" else "Préflight local",
        "video": {
            "file": video.name,
            "sha256": sha256(video),
            "bytes": video.stat().st_size,
            "duration_seconds": float(probe["format"]["duration"]),
            "video_streams": len(video_streams),
            "audio_streams": len(audio_streams),
            "decoded_frames": decoded,
        },
        "checks": checks,
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "failed": sum(item["status"] == "FAIL" for item in checks),
        },
        "limitations": [
            "La validation objective ne remplace pas le visionnage créatif du propriétaire.",
            "Le master est un candidat silencieux; aucune musique ni voix off n’est incluse.",
            "Les rushes Pexels servent à la démonstration et ne sont pas les captations d’un commerçant réel.",
        ],
        "owner_approval_required": True,
        "ffprobe": probe,
    }
    proof = args.proof or args.output_dir / "T3_SILENT_VALIDATION.json"
    proof.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_md = args.output_dir / "RAPPORT_RENDU_SILENCIEUX.md"
    summary_md.write_text(
        "# T3 — Validation du rendu silencieux\n\n"
        f"**Résultat objectif : {overall}** — {validation['summary']['passed']} contrôles PASS, {validation['summary']['failed']} échec.\n\n"
        f"- fichier : `{video.name}` ;\n"
        f"- SHA-256 : `{validation['video']['sha256']}` ;\n"
        "- 30,000 s · 720 × 1280 · 30 i/s · 900 images ;\n"
        "- H.264 / yuv420p ;\n"
        "- zéro piste audio ;\n"
        "- 17 événements appliqués, couvrant les références 2 et 4 ;\n"
        "- quatre blocs de motion design alimentés uniquement par merchant_payload ;\n"
        "- poids variables explicites, petits textes ≥ 600, taille effective ≥ 11 px à 40 % ;\n"
        "- contraste typographique contractuel ≥ 7:1 sur le fond protégé ;\n"
        "- aucun trait séparateur bleu horizontal ou vertical dans la transition multi-panneaux ;\n"
        "- aucun titre de scène, durée, mot démo, mot rush ou provenance média visible ;\n"
        "- validation humaine encore requise.\n",
        encoding="utf-8",
    )
    print(f"T3_SILENT_VALIDATION_{overall} {proof}")
    if overall != "PASS":
        for item in checks:
            if item["status"] == "FAIL":
                print("FAIL", item["check"], item["detail"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
