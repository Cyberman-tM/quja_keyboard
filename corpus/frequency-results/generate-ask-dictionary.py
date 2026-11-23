#!/usr/bin/env python3
"""Generate an AnySoftKeyboard wordlist from reviewed Klingon candidates."""

from __future__ import annotations

import csv
import math
import time
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUT = HERE / "keyboard-word-candidates.csv"
OUTPUT = (
    ROOT
    / "ask-template"
    / "addons"
    / "languages"
    / "tlhingan"
    / "pack"
    / "dictionary"
    / "prebuilt"
    / "tlh_wordlist.xml"
)


def parse_frequency(value: str) -> Decimal:
    return Decimal(value.replace(",", ".")) if value else Decimal(0)


def main() -> None:
    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        words = list(csv.DictReader(source))

    max_frequency = max((parse_frequency(row["Weighted_Per_1000"]) for row in words), default=Decimal(0))
    ranked_words = []
    for row in words:
        word = row["Word"]
        frequency = parse_frequency(row["Weighted_Per_1000"])
        if frequency > 0 and max_frequency > 0:
            # ASK uses integer frequencies from 0 to 255. A square-root scale
            # preserves order while giving less common corpus forms room above
            # the minimum frequency.
            ask_frequency = max(1, round(255 * math.sqrt(float(frequency / max_frequency))))
        else:
            # Keep boQwI'-only headwords available, but below corpus-attested forms.
            ask_frequency = 1
        ranked_words.append((word, ask_frequency, frequency))

    ranked_words.sort(key=lambda item: (-item[1], -item[2], item[0]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write(
            f'<wordlist locale="tlh" description="Klingon quja\' suggestions" '
            f'date="{int(time.time())}" version="1">\n'
        )
        for word, ask_frequency, _ in ranked_words:
            output.write(f' <w f="{ask_frequency}" flags="">{escape(word)}</w>\n')
        output.write("</wordlist>\n")

    matched = sum(parse_frequency(row["Weighted_Per_1000"]) > 0 for row in words)
    print(f"Wrote {len(ranked_words)} words ({matched} with corpus frequencies) to {OUTPUT}")


if __name__ == "__main__":
    main()
