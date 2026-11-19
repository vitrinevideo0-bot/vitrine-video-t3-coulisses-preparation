#!/usr/bin/env python3
"""Build the executable 12-screen T3 capture-flow contract from the approved guide."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(guide: dict) -> dict:
    screens: list[dict] = []
    for scene_index, scene in enumerate(guide["scenes"], 1):
        scene_id = f"S{scene_index}"
        duration_ms = int(scene["secondes"] * 1000)
        next_scene = f"T3_CAPTURE_S{scene_index + 1}_A_GUIDE" if scene_index < 4 else "T3_RENDER_CONFIRMATION"
        screens.extend(
            [
                {
                    "scene_id": scene_id,
                    "scene_index": scene_index,
                    "scene_total": 4,
                    "capture_duration_ms": duration_ms,
                    "capture_slot": f"captures.{scene_id}",
                    "ordinal": len(screens) + 1,
                    "screen_id": f"T3_CAPTURE_{scene_id}_A_GUIDE",
                    "state": "A_GUIDE",
                    "purpose": scene["fonction_commerciale"],
                    "bindings": {
                        "title": f"capture-guide/consignes_T3.json#/scenes/{scene_index - 1}/titre",
                        "instruction": f"capture-guide/consignes_T3.json#/scenes/{scene_index - 1}/consigne",
                        "film_list": f"capture-guide/consignes_T3.json#/scenes/{scene_index - 1}/a_filmer",
                        "avoid_list": f"capture-guide/consignes_T3.json#/scenes/{scene_index - 1}/a_eviter",
                        "example": f"capture-guide/consignes_T3.json#/scenes/{scene_index - 1}/exemple_facultatif"
                    },
                    "visible_components": ["camera_preview_dimmed", "scene_progress", "instruction_sheet", "film_list", "avoid_list", "voice_note", "optional_example", "start_recording_button"],
                    "forbidden_components": ["recording_timer", "review_actions", "subtitles"],
                    "actions": [{"event": "START_RECORDING", "effects": ["request_camera_permission", "request_microphone_permission", "run_COUNTDOWN_3_2_1"], "next_screen_id": f"T3_CAPTURE_{scene_id}_B_RECORDING"}],
                    "proof_png": f"ui-screens/approved/T3_CAPTURE_{scene_id}_A_GUIDE.png"
                },
                {
                    "scene_id": scene_id,
                    "scene_index": scene_index,
                    "scene_total": 4,
                    "capture_duration_ms": duration_ms,
                    "capture_slot": f"captures.{scene_id}",
                    "ordinal": len(screens) + 2,
                    "screen_id": f"T3_CAPTURE_{scene_id}_B_RECORDING",
                    "state": "B_RECORDING",
                    "purpose": "capturer la vidéo et le microphone à vitesse naturelle pendant la durée exacte",
                    "visible_components": ["camera_preview", "microphone_active", "recording_timer", "recording_progress"],
                    "forbidden_components": ["instruction_sheet", "merchant_fields", "example_text", "manual_stop_button", "review_actions", "subtitles"],
                    "capture": {"video": True, "microphone_audio": True, "source_speed": 1.0, "source_time_map": "identity", "audio_time_map": "identity", "duration_ms": duration_ms, "auto_stop": True, "manual_stop": False, "write_to": f"runtime.captures.{scene_id}.uri"},
                    "actions": [{"event": "CAPTURE_DURATION_REACHED", "effects": ["stop_recorder", "finalize_capture_file", "probe_capture_metadata", "open_audio_review"], "next_screen_id": f"T3_CAPTURE_{scene_id}_C_REVIEW"}],
                    "proof_png": f"ui-screens/approved/T3_CAPTURE_{scene_id}_B_RECORDING.png"
                },
                {
                    "scene_id": scene_id,
                    "scene_index": scene_index,
                    "scene_total": 4,
                    "capture_duration_ms": duration_ms,
                    "capture_slot": f"captures.{scene_id}",
                    "ordinal": len(screens) + 3,
                    "screen_id": f"T3_CAPTURE_{scene_id}_C_REVIEW",
                    "state": "C_REVIEW",
                    "purpose": "relire avec le son et accepter ou refaire la prise",
                    "visible_components": ["captured_video_preview", "captured_audio_playback", "review_question", "redo_button", "accept_button"],
                    "forbidden_components": ["instruction_sheet", "recording_timer", "recording_progress", "subtitles"],
                    "playback": {"audio": True, "loop": True, "source_speed": 1.0},
                    "actions": [
                        {"event": "RETAKE", "label": "REFAIRE", "effects": [f"delete:runtime.captures.{scene_id}", "reset_scene_capture_state"], "next_screen_id": f"T3_CAPTURE_{scene_id}_A_GUIDE"},
                        {"event": "ACCEPT_CAPTURE", "label": scene["positive_action"], "effects": [f"persist:runtime.captures.{scene_id}", "mark_capture_accepted"], "next_screen_id": next_scene}
                    ],
                    "proof_png": f"ui-screens/approved/T3_CAPTURE_{scene_id}_C_REVIEW.png"
                }
            ]
        )
    return {
        "schema_version": "1.0.0",
        "contract_id": "restauration_T3_coulisses_capture_flow_v1_0_0",
        "template_id": "RESTAURATION-T3",
        "template_version": "1.0.0",
        "status": "owner_approved_executable_contract",
        "source_guide": "capture-guide/consignes_T3.json",
        "counts": {"scenes": 4, "states_per_scene": 3, "stable_capture_screens": 12},
        "scene_durations_ms": [6000, 8000, 7000, 9000],
        "transient_states": [{"id": "COUNTDOWN_3_2_1", "counted_in_12_stable_screens": False, "sequence": [3, 2, 1], "must_not_be_written_into_capture": True}],
        "runtime_rules": {
            "camera_required": True,
            "microphone_requested": True,
            "speech_optional": True,
            "playback_audio_enabled": True,
            "source_speed": 1.0,
            "automatic_subtitles": False,
            "retake_deletes_previous_capture": True
        },
        "screens": screens
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide", type=Path, default=ROOT / "capture-guide/consignes_T3.json")
    parser.add_argument("--output", type=Path, default=ROOT / "config/T3_CAPTURE_FLOW_V1_0_0.json")
    args = parser.parse_args()
    contract = build(json.loads(args.guide.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"T3_CAPTURE_FLOW_BUILT {len(contract['screens'])} {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
