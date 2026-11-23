# Weighted surface-form frequencies without identified names

Sources included: Hamlet Klingon extraction draft, Star Trek: Discovery season 1 Klingon subtitles (episodes 1–15), and the partial Starfleet Academy #18 comic transcription (pages 4–20). Qo'noS QonoS is not included because the full issue texts have not been imported.

## Weights and formula

Provisional source weights based on the user's current ranking: Hamlet 1.00, Discovery 0.80, comic 0.50. Each source is first normalized to occurrences per 1,000 counted word tokens. `WeightedPer1000` is the weighted mean of those three source-specific rates:

`(1.00 × Hamlet rate + 0.80 × Discovery rate + 0.50 × Comic rate) / 2.30`

This makes source quality weights, rather than raw corpus size, determine each source's contribution. Per-source raw counts and rates are included for inspection.

## Counting scope and limitations

These are case-sensitive exact written forms, with apostrophes retained, not boQwI' headwords or combined inflections. Names were matched to boQwI' entries marked `n:name`, supplemented with single-token names from the comic's accompanying name list. The filter also strips up to three recognized noun suffixes when matching a name. Ambiguous headwords shared with ordinary Klingon vocabulary are kept; `Qel` is explicitly retained because it can mean “doctor”. This removed 74 surface forms (635 raw occurrences) from the combined list. The detailed removal log is `removed-name-counts.csv`.

Primary name-filtered outputs are `weighted-word-frequencies-no-names.csv` and `all-surface-counts-no-names.csv`. `weighted-word-frequencies.csv` and `all-surface-counts.csv` retain the original unfiltered counts for comparison. The name filter is conservative: names missing from boQwI' and the comic's list, names embedded in multiword entries, and ambiguous words may remain. Hamlet excludes 997 uncertain lines and remains a draft; the comic transcription is partial and unverified. Discovery includes all subtitle text after cue numbers, timestamps, and basic markup were removed. English intrusions, speaker/name mentions, and occasional transcription errors may remain. No word forms were lemmatized.

## boQwI' word-list crosswalk

`build-boqwi-wordlist.py` joins the name-filtered weighted surface-form list to the boQwI' snapshot in `ask-template/addons/languages/tlhingan/dictionary-data/`. Matching is exact and case-sensitive, so Klingon distinctions such as `q`/`Q` and `i`/`I` are preserved. No lemmatization or normalization is applied.

- `boqwi-wordlist-frequency-join.csv`: all boQwI' headwords, candidate classifications, and any exact corpus frequency match.
- `keyboard-word-candidates.csv`: single-token entries except sentence and affix records; this is a starting candidate list, not a finalized keyboard dictionary.
- `corpus-only-forms-for-review.csv`: corpus forms with no exact boQwI' headword match. They may be valid inflected forms, names, or transcription noise and need review before inclusion.

The refreshed source import contains 6,264 YAML entries and 5,981 unique boQwI' headword forms, preserving case-colliding entries such as `'IQ` and `'Iq` separately. Corpus-only forms are kept separate rather than automatically treated as dictionary entries. The boQwI' source snapshot's Apache-2.0 license and attribution should accompany any redistributed derived dictionary data.

## Orthography review and exclusions

`validate-word-frequencies.py` applies the user-approved spelling rules to the primary frequency lists. The previous unfiltered files are preserved as `raw-weighted-word-frequencies.csv` and `raw-weighted-word-frequencies-no-names.csv`. Fully uppercase corpus tokens are treated as capitalization noise: `CH`, `GH`, and `TLH` are converted as lowercase digraphs, while standalone Klingon capitals `D`, `H`, `I`, `Q`, and `S` are preserved. `Q` and `q` are never interchangeable. Uppercase forms without one unique exact headword match are excluded, while matches are merged with any existing correctly capitalized form. A lowercase `h` outside `ch`, `gh`, or `tlh` is corrected to uppercase `H` only when the corrected form exactly occurs in boQwI'. `uppercase-forms-review.csv` records the normalized form, match status, and category. The current Windows-safe import retains case-colliding filenames separately via `path_map.json`; the refreshed `entries.csv` contains both `'IQ` and `'Iq` as distinct words. The cleaned lists remove forms containing `z/Z`, `s`, `f/F`, `d`, `i`, or uppercase `P`, `T`, `L`; remove one-character and vowel-initial forms; require the word to begin with a single consonant sound followed by a vowel (recognizing `ch`, `gh`, `ng`, and `tlh` as consonants); and require exactly two-character words to have consonant + vowel shape. Repeated adjacent characters are allowed in longer words. Non-uppercase forms without an exact boQwI' match remain subject to conservative spelling checks and manual review. The lists apply the exact, case-sensitive explicit name/non-word list in `explicit-word-exclusions.csv`. Every rejected form and reason is recorded in `rejected-word-forms.csv`.

The boQwI' join and keyboard candidate list are regenerated from the cleaned name-free frequency data; candidate entries with disallowed letters or explicit exclusions are omitted.

## ASK dictionary prototype

`generate-ask-dictionary.py` converts `keyboard-word-candidates.csv` into the
prebuilt ASK wordlist at
`ask-template/addons/languages/tlhingan/pack/dictionary/prebuilt/tlh_wordlist.xml`.
The initial list contains 4,176 exact-case headwords; 1,519 have a frequency
from the current corpora, while the remaining boQwI'-only entries receive the
minimum frequency so they remain available but rank lower. Positive corpus
frequencies are scaled to ASK's 1–255 range using a square-root curve. This is
a first-pass ranking for device testing and can be tuned after reviewing actual
suggestions. Re-run the generator after updating the candidate list.
