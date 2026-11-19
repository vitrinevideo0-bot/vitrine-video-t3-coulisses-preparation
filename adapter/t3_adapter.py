#!/usr/bin/env python3
"""Offline T3 adapter and deterministic non-repeating music selector."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MUSIC_PACK = ROOT / "config/T3_MUSIC_PACK_V1_0_0.json"
CANONICAL_TEMPLATE = ROOT / "config/T3_COULISSES_TEMPLATE_V1_0_0.json"


class MusicRepeatError(ValueError):
    """Raised when an explicit choice repeats the last successful track."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def approved_variant_ids(music_pack_path: Path = MUSIC_PACK) -> list[str]:
    pack = _load(music_pack_path)
    variants = list(pack["selection_contract"]["owner_approved_variant_ids"])
    if len(variants) != 4 or len(set(variants)) != 4:
        raise ValueError("T3 requires exactly four distinct approved music variants")
    return variants


def select_music_variant(
    render_job_id: str,
    last_successful_variant_id: str | None = None,
    explicit_variant_id: str | None = None,
    music_pack_path: Path = MUSIC_PACK,
) -> str:
    """Select one approved track offline, never repeating the previous success.

    The caller persists the returned ID only after a successful render. This
    function performs no I/O beyond reading the immutable music catalogue.
    """
    variants = approved_variant_ids(music_pack_path)
    if last_successful_variant_id is not None and last_successful_variant_id not in variants:
        raise ValueError("Unknown last successful music variant")
    if explicit_variant_id is not None:
        if explicit_variant_id not in variants:
            raise ValueError("Explicit music variant is not approved")
        if explicit_variant_id == last_successful_variant_id:
            raise MusicRepeatError("Explicit music choice repeats the last successful render")
        return explicit_variant_id
    eligible = [item for item in variants if item != last_successful_variant_id]
    digest = hashlib.sha256(render_job_id.encode("utf-8")).digest()
    return eligible[int.from_bytes(digest[:8], "big") % len(eligible)]


def build_render_job(
    *,
    job_id: str,
    merchant_payload: dict[str, str],
    captures: dict[str, dict[str, Any]],
    last_successful_variant_id: str | None = None,
    explicit_variant_id: str | None = None,
    voice_mode: str = "captured_or_registered_fallback",
    control_plane: str = "github_actions_manual",
) -> dict[str, Any]:
    template = _load(CANONICAL_TEMPLATE)
    required_fields = ["nom", "produit", "prix", "whatsapp", "quartier", "accroche"]
    if list(merchant_payload) != required_fields:
        raise ValueError(f"merchant_payload keys must be exactly {required_fields}")
    if list(captures) != ["S1", "S2", "S3", "S4"]:
        raise ValueError("captures must be exactly S1, S2, S3 and S4 in order")
    selected = select_music_variant(job_id, last_successful_variant_id, explicit_variant_id)
    return {
        "schema_version": "1.0.0",
        "job_id": job_id,
        "template_id": template["template_id"],
        "template_version": template["version"],
        "audio_profile": template["audio_profile"],
        "merchant_payload": merchant_payload,
        "captures": captures,
        "music": {
            "selection_mode": "explicit" if explicit_variant_id else "deterministic_excluding_last_successful",
            "selected_variant_id": selected,
            "last_successful_variant_id": last_successful_variant_id,
            "state_update_policy": "after_success_only"
        },
        "voice": {
            "mode": voice_mode,
            "registered_voice_id": "voice-02",
            "source_speed": 1.0,
            "audio_time_map": "identity",
            "fallback_contract": "config/T3_VOICE_MIX_V1_0_0.json"
        },
        "render": {
            "visual_contract": "config/T3_TEXT_MOTION_V0_4_0.json",
            "transition_contract": "reverse-engineering/T3_TRANSITIONS_30S.json",
            "capture_flow_contract": "config/T3_CAPTURE_FLOW_V1_0_0.json",
            "width": 720,
            "height": 1280,
            "fps": 30,
            "frames": 900,
            "duration_s": 30.0,
            "output_count": 1,
            "production_render_plane": "github_actions"
        },
        "control_plane": control_plane
    }
