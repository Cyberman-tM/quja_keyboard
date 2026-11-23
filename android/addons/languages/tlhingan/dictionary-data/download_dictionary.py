#!/usr/bin/env python3
"""Download boQwI' language data and create a lossless CSV index.

Uses only the Python standard library. The original repository files are kept
under ``source/``; entries.csv provides a flat, spreadsheet/AI-friendly index
while retaining each complete YAML entry in the ``yaml`` column.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


REPOSITORY = "https://github.com/De7vID/klingon-assistant-data"
ARCHIVE_URL = f"{REPOSITORY}/archive/refs/heads/main.zip"
WINDOWS_INVALID = set('<>:"\\|?*')
ENTRY_NAME_PATTERN = re.compile(r"(?m)^[ \t]*(?:-[ \t]*)?entry_name:[ \t]*(.*)$")


def parse_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return json.loads(value)
    return value.split(" #", 1)[0].rstrip()


def entry_records(yaml_text: str) -> list[dict[str, str]]:
    matches = list(ENTRY_NAME_PATTERN.finditer(yaml_text))
    records = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(yaml_text)
        section = yaml_text[match.start():end]
        part_of_speech = re.search(r"(?m)^[ \t]*part_of_speech:[ \t]*(.*)$", section)
        pos_subtype = re.search(r"(?m)^[ \t]*pos_subtype:[ \t]*(.*)$", section)
        records.append(
            {
                "entry_name": parse_yaml_scalar(match.group(1)),
                "part_of_speech": parse_yaml_scalar(part_of_speech.group(1)) if part_of_speech else "",
                "pos_subtype": parse_yaml_scalar(pos_subtype.group(1)) if pos_subtype else "",
                "entry_index": str(index + 1),
            }
        )
    return records


def safe_component(value: str) -> str:
    """Encode characters Windows forbids while keeping the name reversible."""
    result = []
    for index, char in enumerate(value):
        if char == "%" or char in WINDOWS_INVALID or ord(char) < 32:
            result.append(f"%{ord(char):02X}")
        elif char == "." and index == len(value) - 1:
            result.append("%2E")
        elif char == " " and index == len(value) - 1:
            result.append("%20")
        else:
            result.append(char)
    return "".join(result)


def allocate_windows_path(parts: tuple[str, ...], allocations: dict) -> Path:
    """Keep distinct upstream paths distinct on case-insensitive Windows."""
    output_parts = []
    parent_key = ""
    for index, original in enumerate(parts):
        original_key = (parent_key, original)
        assigned = allocations["original_to_safe"].get(original_key)
        if assigned is not None:
            safe = assigned
        else:
            base = safe_component(original)
            safe = base
            used = allocations["used"].setdefault(parent_key, {})
            suffix = 2
            while safe.casefold() in used and used[safe.casefold()] != original:
                if index == len(parts) - 1 and original.casefold().endswith(".yaml"):
                    safe = f"{base[:-5]}~case{suffix}{base[-5:]}"
                else:
                    safe = f"{base}~case{suffix}"
                suffix += 1
            used[safe.casefold()] = original
            allocations["original_to_safe"][original_key] = safe
        output_parts.append(safe)
        parent_key = "/".join(output_parts).casefold()
    return Path(*output_parts)


def download_archive() -> bytes:
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": "quja-klingon-dictionary-data/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def write_index(output: Path, source: Path, original_paths: dict[str, str]) -> tuple[int, int]:
    entry_files = sorted(
        [
            path
            for path in (source / "entries").rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".yaml", ".yml"}
            and path.name.lower() not in {"_index.yaml", "_index.yml"}
        ],
        key=lambda path: original_paths.get(path.relative_to(source).as_posix(), ""),
    )
    csv_path = output / "entries.csv"
    temp_csv_path = output / "entries.csv.tmp"
    entry_total = 0
    with temp_csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "entry_name",
                "category",
                "part_of_speech",
                "pos_subtype",
                "source_file",
                "entry_index",
                "yaml",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for path in entry_files:
            relative = path.relative_to(source).as_posix()
            original_relative = original_paths.get(relative, relative)
            original_parts = PurePosixPath(original_relative).parts
            category = "/".join(original_parts[1:-1])
            yaml_text = path.read_text(encoding="utf-8")
            records = entry_records(yaml_text)
            if not records:
                raise ValueError(f"No entry_name found in {original_relative}")
            for record in records:
                writer.writerow(
                    {
                        **record,
                        "category": category,
                        "source_file": original_relative,
                        "yaml": yaml_text,
                    }
                )
                entry_total += 1
    temp_csv_path.replace(csv_path)

    current_source_paths = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file()
    }
    renamed_paths = {
        safe_path: original_path
        for safe_path, original_path in original_paths.items()
        if safe_path in current_source_paths and safe_path != original_path
    }
    temp_map_path = output / "path_map.json.tmp"
    temp_map_path.write_text(
        json.dumps(renamed_paths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temp_map_path.replace(output / "path_map.json")

    version_path = source / "VERSION"
    revision = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "unknown"
    metadata = {
        "repository": REPOSITORY,
        "branch": "main",
        "version": revision,
        "entry_files": len(entry_files),
        "dictionary_entries": entry_total,
        "archive_url": ARCHIVE_URL,
    }
    temp_metadata_path = output / "download_metadata.json.tmp"
    temp_metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temp_metadata_path.replace(output / "download_metadata.json")
    print(f"Saved {entry_total} dictionary entries from {len(entry_files)} YAML files to {csv_path}")
    return len(entry_files), entry_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Output directory (default: this script's directory)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild the CSV index from the existing source/ snapshot without downloading",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    source = output / "source"
    output.mkdir(parents=True, exist_ok=True)

    if args.offline:
        if not source.is_dir():
            print(f"No local source directory to index: {source}", file=sys.stderr)
            return 1
        path_map_path = output / "path_map.json"
        original_paths = json.loads(path_map_path.read_text(encoding="utf-8")) if path_map_path.exists() else {}
    else:
        print(f"Downloading {REPOSITORY} ...")
        try:
            archive = download_archive()
        except Exception as exc:
            print(f"Download failed: {exc}", file=sys.stderr)
            return 1

        # Extract to a temporary sibling first so failed downloads never leave a
        # half-updated source tree. The archive has one top-level directory.
        staging = output / ".source-staging"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir()
        original_paths: dict[str, str] = {}
        path_allocations = {"original_to_safe": {}, "used": {}}
        try:
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                for member in bundle.infolist():
                    parts = PurePosixPath(member.filename).parts
                    if len(parts) < 2:
                        continue
                    original_relative = PurePosixPath(*parts[1:])
                    relative = allocate_windows_path(original_relative.parts, path_allocations)
                    target = (staging / relative).resolve()
                    if staging.resolve() not in target.parents and target != staging.resolve():
                        raise ValueError(f"Unsafe path in archive: {member.filename}")
                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(bundle.read(member))
                        original_paths[relative.as_posix()] = original_relative.as_posix()

            previous = output / ".source-previous"
            shutil.rmtree(previous, ignore_errors=True)
            if source.exists():
                source.rename(previous)
            try:
                staging.rename(source)
            except Exception:
                if previous.exists() and not source.exists():
                    previous.rename(source)
                raise
            shutil.rmtree(previous, ignore_errors=True)
        except Exception as exc:
            shutil.rmtree(staging, ignore_errors=True)
            print(f"Could not unpack repository archive: {exc}", file=sys.stderr)
            return 1

    try:
        write_index(output, source, original_paths)
    except Exception as exc:
        print(f"Could not build dictionary index: {exc}", file=sys.stderr)
        return 1
    print(f"Original repository snapshot: {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
