"""Public T3 integration adapter API."""

from .t3_adapter import (
    MusicRepeatError,
    approved_variant_ids,
    build_render_job,
    build_render_job_from_state,
    load_music_selection_state,
    record_music_render_result,
    select_music_variant,
    select_music_variant_from_state,
)

__all__ = [
    "MusicRepeatError",
    "approved_variant_ids",
    "build_render_job",
    "build_render_job_from_state",
    "load_music_selection_state",
    "record_music_render_result",
    "select_music_variant",
    "select_music_variant_from_state",
]
