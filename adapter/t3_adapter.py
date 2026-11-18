#!/usr/bin/env python3
"""Offline T3 adapter with strict, persistent four-track music rotation."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MUSIC_PACK = ROOT / "config/T3_MUSIC_PACK_V1_0_0.json"
CANONICAL_TEMPLATE = ROOT / "config/T3_COULISSES_TEMPLATE_V1_0_0.json"
EXPECTED_VARIANTS = [
    "t3_music_481806",
    "t3_music_360659",
    "t3_music_485507",
    "t3_music_245452",
]


class MusicRepeatError(ValueError):
    """Raised when a music choice violates the strict approved cycle."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def approved_variant_ids(music_pack_path: Path = MUSIC_PACK) -> list[str]:
    pack = _load(music_pack_path)
    selection = pack.get("selection_contract", {})
    variants = list(selection.get("owner_approved_variant_ids", []))
    automatic = selection.get("automatic_selection", {})
    if (
        variants != EXPECTED_VARIANTS
        or selection.get("allowed_variant_ids") != EXPECTED_VARIANTS
        or [track.get("id") for track in pack.get("tracks", [])] != EXPECTED_VARIANTS
        or automatic.get("algorithm") != "strict approved order 1→2→3→4→1 from last successful variant"
        or automatic.get("first_render_pool") != "first_owner_approved_variant_only"
        or automatic.get("subsequent_pool") != "single_next_variant_in_approved_order"
        or automatic.get("explicit_selection_policy") != "exact_successor_only"
        or automatic.get("idempotency_ledger_key") != "successful_render_jobs"
        or automatic.get("state_update_policy") != "after_success_only"
        or automatic.get("failed_render_state_policy") != "unchanged"
    ):
        raise ValueError("T3 requires the exact four-track success cycle and durable idempotency ledger")
    return variants


def select_music_variant(
    render_job_id: str,
    last_successful_variant_id: str | None = None,
    explicit_variant_id: str | None = None,
    music_pack_path: Path = MUSIC_PACK,
) -> str:
    """Select one approved track offline in the strict 1 → 2 → 3 → 4 cycle.

    The caller persists the returned ID only after a successful render. Failed
    attempts therefore retry the same track, and the first successful render is
    always variant 1. This function performs no I/O beyond reading the immutable
    music catalogue.
    """
    variants = approved_variant_ids(music_pack_path)
    if not render_job_id:
        raise ValueError("render_job_id is required")
    if last_successful_variant_id is not None and last_successful_variant_id not in variants:
        raise ValueError("Unknown last successful music variant")
    previous_index = -1 if last_successful_variant_id is None else variants.index(last_successful_variant_id)
    expected = variants[(previous_index + 1) % len(variants)]
    if explicit_variant_id is not None:
        if explicit_variant_id not in variants:
            raise ValueError("Explicit music variant is not approved")
        if explicit_variant_id != expected:
            raise MusicRepeatError(
                f"Strict T3 cycle expects {expected}; {explicit_variant_id} cannot bypass it"
            )
    return expected


MUSIC_STATE_SCHEMA_VERSION = "1.0.0"


def load_music_selection_state(state_path: Path) -> dict[str, Any]:
    """Load persistent rotation state; a missing file represents the first render."""
    if not state_path.exists():
        return {
            "schema_version": MUSIC_STATE_SCHEMA_VERSION,
            "last_successful_music_id": None,
            "last_successful_render_job_id": None,
            "successful_render_count": 0,
            "successful_render_jobs": {},
        }
    state = _load(state_path)
    required = {
        "schema_version",
        "last_successful_music_id",
        "last_successful_render_job_id",
        "successful_render_count",
        "successful_render_jobs",
    }
    if set(state) != required or state["schema_version"] != MUSIC_STATE_SCHEMA_VERSION:
        raise ValueError("Invalid T3 music rotation state")
    if state["last_successful_music_id"] not in {None, *approved_variant_ids()}:
        raise ValueError("Unknown last successful music ID in T3 state")
    if not isinstance(state["successful_render_count"], int) or state["successful_render_count"] < 0:
        raise ValueError("Invalid T3 successful render count")
    receipts = state["successful_render_jobs"]
    if (
        not isinstance(receipts, dict)
        or any(not isinstance(job_id, str) or not job_id or music_id not in EXPECTED_VARIANTS for job_id, music_id in receipts.items())
        or len(receipts) != state["successful_render_count"]
    ):
        raise ValueError("Invalid T3 successful render ledger")
    if (state["last_successful_music_id"] is None) != (state["last_successful_render_job_id"] is None):
        raise ValueError("T3 state must pair the successful music and render job IDs")
    if (state["successful_render_count"] == 0) != (state["last_successful_music_id"] is None):
        raise ValueError("An empty T3 state cannot contain a successful render, and conversely")
    if state["last_successful_render_job_id"] is not None and receipts.get(state["last_successful_render_job_id"]) != state["last_successful_music_id"]:
        raise ValueError("The last T3 success must exist in the idempotency ledger")
    return state


def select_music_variant_from_state(
    render_job_id: str,
    state_path: Path,
    explicit_variant_id: str | None = None,
    music_pack_path: Path = MUSIC_PACK,
) -> str:
    """Select using the last success stored by the caller-owned orchestrator."""
    state = load_music_selection_state(state_path)
    return select_music_variant(
        render_job_id,
        state["last_successful_music_id"],
        explicit_variant_id,
        music_pack_path,
    )


def _record_music_render_result_unlocked(
    *,
    state_path: Path,
    render_job_id: str,
    selected_music_id: str,
    succeeded: bool,
    music_pack_path: Path = MUSIC_PACK,
) -> dict[str, Any]:
    """Atomically persist only successful T3 renders; failures leave no trace."""
    if not render_job_id:
        raise ValueError("render_job_id is required")
    if selected_music_id not in approved_variant_ids(music_pack_path):
        raise ValueError("Rendered T3 music is not owner-approved")
    current = load_music_selection_state(state_path)
    if not succeeded:
        return current
    if render_job_id in current["successful_render_jobs"]:
        if current["successful_render_jobs"][render_job_id] != selected_music_id:
            raise ValueError("An idempotent successful callback cannot change music")
        return current
    variants = approved_variant_ids(music_pack_path)
    previous_id = current["last_successful_music_id"]
    expected_id = variants[0] if previous_id is None else variants[(variants.index(previous_id) + 1) % len(variants)]
    if selected_music_id != expected_id:
        raise MusicRepeatError(
            f"Successful T3 render must follow the strict cycle: expected {expected_id}, got {selected_music_id}"
        )
    updated = {
        "schema_version": MUSIC_STATE_SCHEMA_VERSION,
        "last_successful_music_id": selected_music_id,
        "last_successful_render_job_id": render_job_id,
        "successful_render_count": current["successful_render_count"] + 1,
        "successful_render_jobs": {**current["successful_render_jobs"], render_job_id: selected_music_id},
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{state_path.name}.", dir=state_path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(updated, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, state_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return updated


def record_music_render_result(
    *,
    state_path: Path,
    render_job_id: str,
    selected_music_id: str,
    succeeded: bool,
    music_pack_path: Path = MUSIC_PACK,
) -> dict[str, Any]:
    """Serialize callbacks across processes before applying the atomic update."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_path.parent / f".{state_path.name}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _record_music_render_result_unlocked(
                state_path=state_path,
                render_job_id=render_job_id,
                selected_music_id=selected_music_id,
                succeeded=succeeded,
                music_pack_path=music_pack_path,
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


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
            "selection_mode": "explicit" if explicit_variant_id else "strict_success_cycle",
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


def build_render_job_from_state(
    *,
    state_path: Path,
    job_id: str,
    merchant_payload: dict[str, str],
    captures: dict[str, dict[str, Any]],
    explicit_variant_id: str | None = None,
    voice_mode: str = "captured_or_registered_fallback",
    control_plane: str = "github_actions_manual",
) -> dict[str, Any]:
    """Build a RenderJob using persisted last-success state."""
    state = load_music_selection_state(state_path)
    return build_render_job(
        job_id=job_id,
        merchant_payload=merchant_payload,
        captures=captures,
        last_successful_variant_id=state["last_successful_music_id"],
        explicit_variant_id=explicit_variant_id,
        voice_mode=voice_mode,
        control_plane=control_plane,
    )
