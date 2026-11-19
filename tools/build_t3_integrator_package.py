#!/usr/bin/env python3
"""Build a deterministic, offline RESTAURATION-T3 integrator ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".git", ".tmp", "output", "github-release"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def allowed(path: Path) -> bool:
    return not (set(path.parts) & EXCLUDED_PARTS) and path.suffix not in EXCLUDED_SUFFIXES and path.name != ".DS_Store"


def expand(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*") if item.is_file() and allowed(item.relative_to(ROOT)))
    raise FileNotFoundError(path)


def deterministic_zip(source_root: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            relative = path.relative_to(source_root.parent).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=ROOT / "packages/t3-coulisses-v1/package_spec.json")
    parser.add_argument("--golden-master", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    package_id = spec["package_id"]
    golden = spec["external_golden_master"]
    if not args.golden_master.is_file():
        raise SystemExit("Golden master is missing")
    if sha256(args.golden_master) != golden["sha256"] or args.golden_master.stat().st_size != golden["bytes"]:
        raise SystemExit("Golden master lock mismatch")

    source_manifest = json.loads((ROOT / "audio/music/t3-afrobeat-v1/source_manifest.json").read_text(encoding="utf-8"))
    original_names = {item["official_original_filename"] for item in source_manifest["tracks"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = args.output_dir / f"{package_id}.zip"
    report_path = args.output_dir / "T3_INTEGRATOR_PACKAGE_BUILD_REPORT.json"

    with tempfile.TemporaryDirectory(prefix="t3-package-") as temp_name:
        temp = Path(temp_name)
        package_root = temp / package_id
        package_root.mkdir()
        entries: dict[str, dict] = {}
        for item in spec["include"]:
            source = ROOT / item["path"]
            for file_path in expand(source):
                relative = file_path.relative_to(ROOT)
                if file_path.name in original_names:
                    raise RuntimeError(f"Full Pixabay source forbidden: {file_path.name}")
                target = package_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file_path, target)
                key = relative.as_posix()
                if key in entries:
                    raise RuntimeError(f"Duplicate package path: {key}")
                entries[key] = {"path": key, "role": item["role"], "bytes": target.stat().st_size, "sha256": sha256(target)}

        golden_target = package_root / golden["package_path"]
        golden_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.golden_master, golden_target)
        entries[golden["package_path"]] = {
            "path": golden["package_path"], "role": "golden_complete_master", "bytes": golden_target.stat().st_size,
            "sha256": sha256(golden_target), "video_bitstream_sha256": golden["video_bitstream_sha256"]
        }
        payload = sorted(entries.values(), key=lambda item: item["path"])
        manifest = {
            "schema_version": "1.0.0", "package_id": package_id, "template_id": spec["template_id"],
            "template_version": spec["template_version"], "audio_profile": spec["audio_profile"],
            "status": "integrator_package_built", "ota_implemented": False, "cloudflare_deployed": False,
            "file_count": len(payload), "payload_bytes": sum(item["bytes"] for item in payload),
            "files": payload, "known_protocol_deviations": json.loads((ROOT / "config/T3_COULISSES_TEMPLATE_V1_0_0.json").read_text(encoding="utf-8"))["known_protocol_deviations"]
        }
        manifest_path = package_root / "PACKAGE_MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        checksums = package_root / "SHA256SUMS.txt"
        files_for_checksums = sorted(item for item in package_root.rglob("*") if item.is_file() and item != checksums)
        checksums.write_text("\n".join(f"{sha256(path)}  {path.relative_to(package_root).as_posix()}" for path in files_for_checksums) + "\n", encoding="utf-8")
        deterministic_zip(package_root, zip_path)

    report = {
        "schema_version": "1.0.0", "status": "PASS", "package_id": package_id,
        "zip": {"file": zip_path.name, "bytes": zip_path.stat().st_size, "sha256": sha256(zip_path)},
        "payload": {"file_count": manifest["file_count"], "bytes": manifest["payload_bytes"]},
        "golden_master": {"sha256": golden["sha256"], "bytes": golden["bytes"], "included": True},
        "constraints": spec["constraints"]
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
