# Build Log

## Day 0 — Sep 26
Scaffolded the repo: folder structure, README, MIT license, `.gitignore`,
`requirements.txt`, a placeholder `app.py`. Pushed to GitHub.

## Day 1 — Sep 26
Wrote `docs/MAPPING.md` — the seven classical-principle-to-AI-principle pairs
that everything else in the project is built on, with paraphrased citations
to verify later.

## Day 2 — Sep 27
Learned the hard way that `sacred-texts.com` sits behind Cloudflare and
blocks automated fetches (curl and WebFetch both got a 403 / bot-challenge
page). Switched to Project Gutenberg instead and pulled three real
public-domain translations into `data/raw/`: the Gita (Arnold), the Yoga
Sutras (Johnston), and the Upanishads (Paramananda, includes Isa). Confirmed
the Ahimsa and Aparigraha source passages actually exist in these files.
Arthashastra and Tirukkural aren't on Gutenberg — flagged in
`data/raw/SOURCES.md` as a manual-download follow-up, not blocking Day 3.

## Day 3 — Sep 27
Wrote `src/data_prep/clean.py`: strips the Gutenberg header/footer, then
splits what's left into small tagged records (source, book, verse, text).
First run leaked a transcriber credit line ("Produced by...") into the
output as a fake record — added a filter for that pattern and re-ran.
1,377 records total across the three sources. Numbered sutras/verses keep
their real number (confirmed against the Ahimsa passage from Day 2); plain
paragraphs get a sequential `p<N>` id since not every translator numbers
their text the same way.

## Day 4 — Sep 27
Wrote `src/data_prep/chunk.py`: groups records into 3-verse chunks (never
crossing a book boundary) and tags each with candidate principles via a
keyword lexicon. 460 chunks, 303 tagged with at least one principle.

Found a real weak-supervision problem worth fixing on Day 5: `dharma` only
matched 16 chunks because the lexicon only looked for the word "duty" —
Arnold's translation uses "work" (35 times) and "task" (11 times) for the
same concept (karma/duty) far more often. Meanwhile `viveka` over-matched
(149 chunks) because "wisdom" and "knowledge" are generic words that show up
in almost any philosophical passage, not just discernment-specific ones.
Day 5 needs to: widen the `dharma` keyword list, narrow the `viveka` one,
and hand-check a sample against `docs/MAPPING.md`.

## Day 5 — Sep 27
Fixed the lexicon: added "task" and "own work" to `dharma` (Arnold uses
these far more than "duty"), dropped the generic "wisdom"/"knowledge" from
`viveka` (they matched almost any philosophical sentence). Result: `dharma`
27 chunks (was 16), `viveka` 51 (was 149) — a much more honest signal.

Hand-reviewed a 45-chunk sample (5 per principle + 10 untagged, seeded
random sample) against `docs/MAPPING.md`. Found and fixed two real bugs in
`clean.py`, not just tagging bugs:

1. Standalone footnote paragraphs (`[FN#5]  I am doubtful of accuracy
   here...`) were being kept as if they were real verse content — one had
   even picked up an `aparigraha` tag by accident. Added a filter to drop
   any paragraph that starts with `[FN#`.
2. Footnote markers *inside* real verse lines (`...death-water.[FN#1]`)
   were left in the text. Added a regex substitution to strip them while
   keeping the surrounding verse. One OCR-garbled marker (`[FN#l6]`, an "l"
   instead of "1") survives this — not worth chasing for one stray token
   out of 448 chunks.

Known, accepted limitation going into Week 2: keyword tagging still
multi-tags dense passages with 4-5 principles at once, because classical
commentary genuinely discusses several ideas in one breath. This is fine —
these tags are only meant to *boost* the real signal in Week 2's retriever
(`retriever.py`), not to be the ground truth on their own; semantic
similarity from embeddings does the actual relevance ranking.

Also flagged for later, not fixed now: Yoga Sutra chunk IDs sometimes mix a
real sutra number with an unnumbered commentary paragraph in the same chunk
(e.g. `10-p181`) — not a citable reference as-is. Needs a smarter splitter
that separates terse sutra text from Johnston's prose commentary before
this data is used for citations in the app (Week 2).

**Week 1 done.** Data foundation: 3 public-domain sources, 1,340 cleaned
records, 448 tagged chunks, and a documented set of known limitations to
carry into the RAG build.
