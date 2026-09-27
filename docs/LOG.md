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
