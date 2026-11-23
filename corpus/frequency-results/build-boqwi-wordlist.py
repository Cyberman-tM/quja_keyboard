#!/usr/bin/env python3
"""Join boQwI' headwords with case-sensitive Klingon surface-form frequencies."""

from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOQWI_CSV = (
    ROOT
    / "ask-template"
    / "addons"
    / "languages"
    / "tlhingan"
    / "dictionary-data"
    / "entries.csv"
)
FREQUENCIES_CSV = Path(__file__).with_name("weighted-word-frequencies-no-names.csv")
WORDLIST_CSV = Path(__file__).with_name("boqwi-wordlist-frequency-join.csv")
CORPUS_ONLY_CSV = Path(__file__).with_name("corpus-only-forms-for-review.csv")
KEYBOARD_CANDIDATES_CSV = Path(__file__).with_name("keyboard-word-candidates.csv")

DISALLOWED_KLINGON_CHARACTERS = set("zZsfFd iPTL") - {" "}
KLINGON_VOWELS = set("aeiouAEIOU")
EXPLICIT_EXCLUSION_FILE = Path(__file__).with_name("explicit-word-exclusions.csv")


def candidate_has_valid_shape(word: str) -> bool:
    if set(word) & DISALLOWED_KLINGON_CHARACTERS or len(word) < 2 or word[0] in KLINGON_VOWELS:
        return False
    if word.startswith("tlh"):
        onset_end = 3
    elif word.startswith(("ch", "gh", "ng")):
        onset_end = 2
    else:
        onset_end = 1
    if onset_end >= len(word) or word[onset_end] not in KLINGON_VOWELS:
        return False
    for index, character in enumerate(word):
        if character != "h":
            continue
        if index >= 2 and word[index - 2:index + 1] == "tlh":
            continue
        if index >= 1 and word[index - 1:index + 1] in {"ch", "gh"}:
            continue
        return False
    return len(word) != 2 or word[1] in KLINGON_VOWELS


def read_boQwI_entries() -> dict[str, dict[str, object]]:
    words: dict[str, dict[str, object]] = {}
    with BOQWI_CSV.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            word = row["entry_name"]
            if not word:
                continue
            item = words.setdefault(word, {"categories": set(), "entries": 0, "name": False, "lexical": False})
            item["categories"].add(row["category"])
            item["entries"] += 1
            pos_tags = set(row["part_of_speech"].split(","))
            is_name = "n:name" in pos_tags or "name" in pos_tags or row["pos_subtype"] == "name"
            item["name"] = item["name"] or is_name
            item["lexical"] = item["lexical"] or not is_name
    return words


def read_frequencies() -> dict[str, dict[str, str]]:
    frequencies: dict[str, dict[str, str]] = {}
    with FREQUENCIES_CSV.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            frequencies[row["Word"]] = row
    return frequencies


def main() -> None:
    entries = read_boQwI_entries()
    frequencies = read_frequencies()

    matched_rows = []
    for word, metadata in entries.items():
        frequency = frequencies.get(word)
        categories = sorted(metadata["categories"])
        if metadata["name"] and not metadata["lexical"]:
            candidate_status = "name-review"
        elif any(category.startswith("sentences") for category in categories):
            candidate_status = "review-sentence-entry"
        elif any(category.startswith("suffixes") for category in categories):
            candidate_status = "affix-review"
        elif any(character.isspace() for character in word):
            candidate_status = "phrase-review"
        else:
            candidate_status = "single-word-candidate"
        matched_rows.append(
            {
                "Word": word,
                "BoQwI_Categories": " | ".join(categories),
                "BoQwI_Entry_Count": metadata["entries"],
                "Hamlet_Count": frequency["HamletCount"] if frequency else "",
                "Discovery_Count": frequency["DiscoveryCount"] if frequency else "",
                "Comic_Count": frequency["ComicCount"] if frequency else "",
                "Weighted_Per_1000": frequency["WeightedPer1000"] if frequency else "",
                "Sources_Present": frequency["SourcesPresent"] if frequency else "0",
                "Frequency_Status": "matched" if frequency else "boQwI-only",
                "Candidate_Status": candidate_status,
            }
        )

    def rank(row: dict[str, str]) -> tuple[int, Decimal, str]:
        if row["Frequency_Status"] == "matched":
            return (0, -Decimal(row["Weighted_Per_1000"].replace(",", ".")), row["Word"])
        return (1, Decimal(0), row["Word"])

    matched_rows.sort(key=rank)
    fields = list(matched_rows[0].keys())
    with WORDLIST_CSV.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(matched_rows)

    with EXPLICIT_EXCLUSION_FILE.open(encoding="utf-8-sig", newline="") as source:
        explicitly_excluded = {row["Word"] for row in csv.DictReader(source)}
    keyboard_candidates = [
        row for row in matched_rows
        if row["Candidate_Status"] == "single-word-candidate"
        and candidate_has_valid_shape(row["Word"])
        and row["Word"] not in explicitly_excluded
    ]
    with KEYBOARD_CANDIDATES_CSV.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(keyboard_candidates)

    corpus_only = [
        row for word, row in frequencies.items() if word not in entries
    ]
    corpus_only.sort(
        key=lambda row: (
            -Decimal(row["WeightedPer1000"].replace(",", ".")),
            row["Word"],
        )
    )
    with CORPUS_ONLY_CSV.open("w", encoding="utf-8-sig", newline="") as output:
        fields = list(corpus_only[0].keys())
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(corpus_only)

    matched = sum(row["Frequency_Status"] == "matched" for row in matched_rows)
    print(f"boQwI' unique headwords: {len(entries)}")
    print(f"Exact case-sensitive frequency matches: {matched}")
    print(f"boQwI'-only headwords: {len(entries) - matched}")
    print(f"Single-word keyboard candidates: {len(keyboard_candidates)}")
    print(f"Corpus-only surface forms for review: {len(corpus_only)}")
    print(WORDLIST_CSV)
    print(KEYBOARD_CANDIDATES_CSV)
    print(CORPUS_ONLY_CSV)


if __name__ == "__main__":
    main()
