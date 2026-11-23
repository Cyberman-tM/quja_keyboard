#!/usr/bin/env python3
"""Filter corpus frequency forms against the user's Klingon spelling rules."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
BOQWI_CSV = HERE.parents[1] / "ask-template" / "addons" / "languages" / "tlhingan" / "dictionary-data" / "entries.csv"
INPUTS = {
    "raw-weighted-word-frequencies.csv": "weighted-word-frequencies.csv",
    "raw-weighted-word-frequencies-no-names.csv": "weighted-word-frequencies-no-names.csv",
}
EXCLUSION_CSV = HERE / "explicit-word-exclusions.csv"
REMOVED_CSV = HERE / "rejected-word-forms.csv"
UPPERCASE_CSV = HERE / "uppercase-forms-review.csv"

# Exact forms that the user identified as names or non-words. Reasons are kept
# separately from orthographic rules so future decisions remain reviewable.
EXPLICIT_EXCLUSIONS = {
    "Jefferies": "English personal name",
    "JeffersonDaq": "Personal name with Klingon locative suffix; not a dictionary word",
    "John": "English personal name",
    "Horey'So": "Klingonized personal name",
    "layerteS": "Klingonized personal name",
    "Paul": "English personal name",
    "roSenQatlh": "Klingonized personal name",
    "Gabriel": "English personal name",
    "bernarDo": "Klingonized personal name",
    "LAYERTE": "Klingonized personal name / uppercase transcription",
    "Burnham": "Personal name",
    "Burnham'e": "Personal name with Klingon suffix",
    "Connor": "English personal name",
    "Philippa": "English personal name",
    "Polonyu": "Personal name",
    "Discovery": "English title/name",
    "Emotion": "English word",
    "Georgiou": "Personal name",
    "Ghertlhu": "Klingonized personal name",
    "Amlet": "English title/name transcription",
    "ATLH": "Invalid all-uppercase transcription",
    "Charon": "Personal name",
    "MED": "Not a Klingon word",
    "Layerte": "Klingonized personal name",
    "Logic": "English word",
    "Med": "Not a Klingon word",
    "Michael": "English personal name",
    "Ovelya": "Personal name",
    "NCC": "Not a Klingon word",
}

# Klingon capitalization permits uppercase D, H, I, Q, S. Lowercase s, d, and
# i are disallowed; z and f are not Klingon letters in either case.
INVALID_CHARACTERS = set("zZsfFd iPTL") - {" "}
VOWELS = set("aeiouAEIOU")


def orthography_issue(word: str) -> str | None:
    bad = sorted(set(word) & INVALID_CHARACTERS)
    if bad:
        return "Contains disallowed character(s): " + " ".join(bad)
    if len(word) < 2:
        return "Word must contain at least two characters"
    if word[0] in VOWELS:
        return "Word must begin with a consonant"
    if word.startswith("tlh"):
        onset_end = 3
    elif word.startswith(("ch", "gh", "ng")):
        onset_end = 2
    else:
        onset_end = 1
    if onset_end >= len(word) or word[onset_end] not in VOWELS:
        return "Word must begin with one consonant followed by a vowel"
    for index, character in enumerate(word):
        if character != "h":
            continue
        if index >= 2 and word[index - 2:index + 1] == "tlh":
            continue
        if index >= 1 and word[index - 1:index + 1] in {"ch", "gh"}:
            continue
        return "Lowercase h is only valid in ch, gh, or tlh"
    if len(word) == 2 and word[1] not in VOWELS:
        return "Two-character word must have consonant + vowel shape"
    return None


def uppercase_restoration_candidates(word: str) -> list[str]:
    """Restore capitalization without conflating distinct Klingon letters."""
    normalized = re.sub(r"TLH|CH|GH", lambda match: match.group(0).lower(), word)
    normalized = "".join(character if character in "DHIQS" else character.lower() for character in normalized)
    return [normalized]


def resolve_uppercase(word: str, boqwi_headwords: set[str]) -> tuple[str, list[str]]:
    candidates = uppercase_restoration_candidates(word)
    matches = [candidate for candidate in candidates if candidate in boqwi_headwords]
    return (matches[0] if len(matches) == 1 else candidates[0], matches)


def normalize_klingon_case(word: str, boqwi_headwords: set[str] | None = None) -> str:
    """Normalize all-caps tokens; correct standalone lowercase h only with boQwI' support."""
    if word.isupper():
        return resolve_uppercase(word, boqwi_headwords or set())[0]

    result = list(word)
    changed_h = False
    for index, character in enumerate(word):
        if character != "h":
            continue
        if index >= 2 and word[index - 2:index + 1] == "tlh":
            continue
        if index >= 1 and word[index - 1:index + 1] in {"ch", "gh"}:
            continue
        result[index] = "H"
        changed_h = True
    corrected = "".join(result)
    if changed_h and corrected not in (boqwi_headwords or set()):
        return word
    return corrected


def read_boqwi_entries() -> dict[str, set[str]]:
    entries: dict[str, set[str]] = defaultdict(set)
    with BOQWI_CSV.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            entries[row["entry_name"]].add(row["category"])
    return entries


def parse_num(value: str) -> Decimal:
    return Decimal(value.replace(",", ".")) if value else Decimal(0)


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    boqwi_entries = read_boqwi_entries()
    known_headwords = set(boqwi_entries)
    explicit_rows = [
        {"Word": word, "Reason": reason}
        for word, reason in sorted(EXPLICIT_EXCLUSIONS.items(), key=lambda item: item[0].casefold())
    ]
    write_csv(EXCLUSION_CSV, explicit_rows, ["Word", "Reason"])

    removed_rows: dict[str, dict[str, str]] = {}
    uppercase_rows: dict[str, dict[str, str]] = {}
    uppercase_resolution: dict[str, tuple[str, list[str]]] = {}
    for input_name, output_name in INPUTS.items():
        with (HERE / input_name).open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames or []
            groups: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in reader:
                original = row["Word"]
                if original.isupper():
                    canonical, matches = resolve_uppercase(original, known_headwords)
                    uppercase_resolution[original] = (canonical, matches)
                else:
                    canonical = normalize_klingon_case(original, known_headwords)
                groups[canonical].append(row)

        accepted: list[dict[str, str]] = []
        for word, source_rows in groups.items():
            issue = orthography_issue(word)
            explicit_reason = EXPLICIT_EXCLUSIONS.get(word)
            normalized_sources = [source_row for source_row in source_rows if source_row["Word"] != normalize_klingon_case(source_row["Word"], known_headwords)]
            boqwi_match = word in boqwi_entries
            confirmed_match = boqwi_match
            for source_row in source_rows:
                original = source_row["Word"]
                if not original.isupper() and original == normalize_klingon_case(original, known_headwords):
                    continue
                resolved_match_list = uppercase_resolution.get(original, (word, []))[1]
                source_boqwi_match = bool(resolved_match_list) and resolved_match_list[0] in boqwi_entries if original.isupper() else boqwi_match
                if explicit_reason:
                    decision = "Explicitly excluded"
                elif original.isupper() and len(resolved_match_list) > 1:
                    decision = "Ambiguous casing: multiple boQwI' matches; excluded pending review"
                elif source_boqwi_match:
                    decision = f"Corrected to {word}; exact boQwI' entry confirms form"
                elif original.isupper():
                    decision = "No exact boQwI' headword; excluded"
                elif issue:
                    decision = "Rejected by orthographic rule"
                elif original != word:
                    decision = f"Corrected casing to {word}; retained"
                else:
                    decision = "Review; not auto-excluded"
                uppercase_rows[original] = {
                    "Word": original,
                    "Corrected_Form": word,
                    "WeightedPer1000": source_row["WeightedPer1000"],
                    "BoQwI_Match": "ambiguous" if original.isupper() and len(resolved_match_list) > 1 else ("yes" if source_boqwi_match else "no"),
                    "BoQwI_Candidate_Matches": " | ".join(resolved_match_list),
                    "BoQwI_Categories": " | ".join(sorted(boqwi_entries[resolved_match_list[0]])) if source_boqwi_match and len(resolved_match_list) == 1 else (" | ".join(sorted(boqwi_entries[word])) if boqwi_match else ""),
                    "Decision": decision,
                    "SourceFile": input_name,
                }
            if explicit_reason:
                for source_row in source_rows:
                    original = source_row["Word"]
                    removed_rows[original] = {"Word": original, "Reason": explicit_reason}
                continue
            rejected_uppercase = [
                source_row for source_row in source_rows
                if source_row["Word"].isupper() and len(uppercase_resolution[source_row["Word"]][1]) != 1
            ]
            for source_row in rejected_uppercase:
                original = source_row["Word"]
                matches = uppercase_resolution[original][1]
                removed_rows[original] = {
                    "Word": original,
                    "Reason": (
                        "All-uppercase form has multiple boQwI' casing matches; excluded pending review"
                        if len(matches) > 1
                        else f"All-uppercase form normalized to {word}; no exact boQwI' headword match"
                    ),
                }
            source_rows = [source_row for source_row in source_rows if source_row not in rejected_uppercase]
            if not source_rows:
                continue
            normalized_sources = [source_row for source_row in source_rows if source_row["Word"] != normalize_klingon_case(source_row["Word"], known_headwords)]
            for source_row in source_rows:
                if source_row["Word"] != word:
                    removed_rows[source_row["Word"]] = {"Word": source_row["Word"], "Reason": f"Merged into {word}"}
            if issue and not (normalized_sources and confirmed_match):
                removed_rows[word] = {"Word": word, "Reason": issue}
                continue

            # Canonicalize the two corpus capitalization errors by summing raw
            # counts and per-source rates. Recompute the weighted rate from the
            # summed source rates so the combined form retains both occurrences.
            if len(source_rows) > 1:
                row = dict(source_rows[0])
                for count_field in ("HamletCount", "DiscoveryCount", "ComicCount"):
                    row[count_field] = str(sum(int(item[count_field] or 0) for item in source_rows))
                for rate_field in ("HamletPer1000", "DiscoveryPer1000", "ComicPer1000"):
                    row[rate_field] = str(sum((parse_num(item[rate_field]) for item in source_rows), Decimal(0)))
                row["WeightedPer1000"] = str(
                    (parse_num(row["HamletPer1000"])
                     + Decimal("0.8") * parse_num(row["DiscoveryPer1000"])
                     + Decimal("0.5") * parse_num(row["ComicPer1000"])) / Decimal("2.3")
                )
                row["SourcesPresent"] = str(sum(int(row[field]) > 0 for field in ("HamletCount", "DiscoveryCount", "ComicCount")))
                row["Word"] = word
            else:
                row = dict(source_rows[0])

            row["Word"] = word
            accepted.append(row)

        accepted.sort(key=lambda row: (-parse_num(row["WeightedPer1000"]), row["Word"]))
        write_csv(HERE / output_name, accepted, fields)

    write_csv(REMOVED_CSV, sorted(removed_rows.values(), key=lambda row: row["Word"].casefold()), ["Word", "Reason"])
    write_csv(UPPERCASE_CSV, sorted(uppercase_rows.values(), key=lambda row: row["Word"].casefold()), ["Word", "Corrected_Form", "WeightedPer1000", "BoQwI_Match", "BoQwI_Candidate_Matches", "BoQwI_Categories", "Decision", "SourceFile"])

    for name, output_name in INPUTS.items():
        with (HERE / output_name).open(encoding="utf-8-sig", newline="") as f:
            count = sum(1 for _ in csv.DictReader(f))
        print(f"{output_name}: {count} forms")
    print(f"Explicit exclusions: {len(EXPLICIT_EXCLUSIONS)}")
    print(f"Rejected/merged spellings logged: {len(removed_rows)}")
    print(f"Uppercase forms for review: {len(uppercase_rows)}")
    print(f"Uppercase forms: {', '.join(sorted(uppercase_rows))}")


if __name__ == "__main__":
    main()
