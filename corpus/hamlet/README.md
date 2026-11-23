# The Klingon Hamlet

Source: user-provided EPUB, *Hamlet, Prince of Denmark* (William Shakespeare; Lawrence Schoen).

Status: extracted as a reviewable draft from the four XHTML play files. The files interleave Klingon and English down to individual lines, so language classification is automated and conservative; 997 lines remain in `line-review.csv` for review rather than being counted as Klingon.

Files:

- `klingon-draft.txt`: high-confidence Klingon candidate lines; speaker labels and scene directions are excluded, names occurring in dialogue remain.
- `line-review.csv`: line-level language classification, dictionary-root evidence, and unresolved lines.
- `surface-frequencies-draft.csv`: exact written-form counts from candidate lines, not a final frequency table.

The draft currently contains 19,914 tokens across 8,233 written forms. This is provisional: ambiguous lines are excluded, a few English interjections may remain, and no proper-name filtering or headword normalization has been applied. Preserve the EPUB's exact edition; the KLI says the paperback text was revised from the earlier edition.
