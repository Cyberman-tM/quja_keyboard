# tlhIngan Hol word-frequency sources

Each source is kept separate so results can be compared by genre and date. Source status describes provenance; canon status does not determine whether a text is counted.

## Current sources

- [Star Trek: Discovery subtitles](star-trek-discovery/README.md) — season 1, episodes 1–15; extracted and surface-form counts generated.
- [Starfleet Academy #18 comic](starfleet-academy-18/transcription-draft.md) — user-provided image pages 4–20; counted provisionally (650 tokens / 434 forms), but transcription remains unverified. Pages 0–3 were not included in the upload.
- [Hamlet](hamlet/README.md) — Klingon candidate extraction and provisional surface-form counts; 997 lines await review.
- [Qo'noS QonoS](qonos-qonos/README.md) — KLI archive identified; issues not yet imported.
- [Preliminary weighted results](frequency-results/README.md) — current surface-form counts from Hamlet, Discovery, and the partial comic transcript.

Each source remains independently tracked; the goal is to compare word use across source type and date.

## Provisional source ranking

Based on the user's current assessment: Hamlet highest; Lieven's Discovery subtitles next; Starfleet Academy #18 and Qo'noS QonoS lower and still uncertain. Provisional multipliers are applied in `frequency-results/`: Hamlet 1.00, Discovery 0.80, and the partial comic 0.50. The user's note that some Discovery Klingon is not canonically approved is recorded as metadata and does not exclude it from frequency counts.
