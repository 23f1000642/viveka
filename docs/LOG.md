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

## Day 7 — Sep 28
Set up a venv and installed `sentence-transformers` + `chromadb` — both
installed cleanly against Python 3.14 with no dependency conflicts, which
was worth checking given how new that Python version is. Pinned both to the
exact versions that worked (`sentence-transformers==6.1.0`,
`chromadb==1.5.9`) in `requirements.txt`.

Wrote `src/rag/index.py` to embed all 448 chunks (`all-MiniLM-L6-v2`) and
persist them to a local ChromaDB collection. First run crashed with
`DuplicateIDError` — turned out chunk IDs only encoded source and verse
number (`yoga_sutras_johnston:1-2`), not book, and the Yoga Sutras restart
their verse numbering at 1 in each of its four books (Samadhi, Sadhana,
Vibhuti, Kaivalya Pada). Fixed by folding the book into the chunk ID
(`yoga_sutras_johnston:book_i:1-2`) — re-ran `chunk.py`, confirmed all 448
IDs were unique, then indexing succeeded.

Sanity-tested retrieval with a modern-phrased query ("Is it wrong for an AI
system to collect more personal data than it needs?") against the raw
embeddings. The matches were mediocre — cosine distances around 1.6, and
the closest hits were only loosely on-topic. This is a real, expected
problem: the corpus is 100-year-old translated scripture, and a query
phrased in 2026 AI-engineering language sits in a different part of
embedding space than "renunciation" or "non-possession." Raw semantic
similarity alone won't be enough — confirms the architecture decision to
boost retrieval using the principle tags from Day 4/5, which is exactly
what Day 8's `retriever.py` needs to do.

## Day 8 — Sep 29
Hit a real environment blocker before writing a single line of retrieval
logic: `sentence-transformers` imports `scikit-learn` internally, and
`scikit-learn`'s compiled `murmurhash` DLL got blocked outright by a
Windows Application Control policy on this machine — confirmed it wasn't
a fluke by trying a different `sentence-transformers` version and a fresh
`scikit-learn` build, both blocked the same way. Not something to route
around by touching security settings, so switched the architecture: local
embeddings (`sentence-transformers`/`torch`) → hosted embeddings via the
Voyage AI API (`requests` + an API key, no native binaries at all). Wrote
`src/rag/embeddings.py` as one shared helper so `index.py` and
`retriever.py` can't drift onto two different embedding setups.

Second real obstacle: a free Voyage account with no payment method is
capped at 3 requests/minute and 10K tokens/minute. The first full-corpus
embed run 429'd. Fixed properly instead of just retrying blind: dropped the
batch size to 20, added a 21-second pause between requests, and added
retry-with-backoff (respecting `Retry-After` when present) so a stray 429
doesn't crash the whole run. Re-indexed all 448 chunks successfully this
way (~8 minutes, one-time cost).

Wrote `src/rag/retriever.py`: fetches top-20 by embedding similarity, then
re-ranks by subtracting a fixed boost per principle the query and a chunk
share — detected using a *second*, separate keyword lexicon tuned to
modern AI-ethics phrasing ("data collection", "explainable", "addictive"),
since Day 7 showed the ancient-text lexicon from `chunk.py` doesn't
transfer to how a real user phrases a question.

Ran the 5 test queries from the architecture plan. 4/5 detected a principle
and the boost correctly promoted a chunk that actually shared it, with
plausible results (e.g. "human takes over from automation" → Viveka →
retrieved a passage specifically about "right discrimination"). One query
("should a hiring algorithm's decisions be explainable to the applicant")
detected nothing — the Nyaya keyword list only had the exact phrase
"explain the decision," which didn't match "explainable." Added
"explainable" to the list and verified the fix locally (no need to spend
another rate-limited API call — `detect_query_principles` is pure string
matching, testable without the network).

## Day 9 — Sep 29
Wrote `src/rag/prompts.py`: the grounded system prompt for Viveka (cite
retrieved passages by number, say so plainly when the context doesn't
support an answer, name the classical principle before mapping it to the
modern one, treat scripture as analogy not literal engineering
instruction), plus `format_context()`/`build_user_message()` to turn
`retriever.py`'s output into the numbered citation block the prompt refers
to.

Sanity-tested with a real retriever call ("is it okay for a chatbot to
pretend to be more certain than it actually is?"). The query-side keyword
lexicon didn't fire (no exact phrase match), but raw embedding similarity
alone still surfaced a strongly on-topic passage — an Upanishad passage
about false confidence vs. true humility ("he who thinks he knows It,
knows It not"). Good sign that retrieval holds up even when the tag boost
doesn't trigger.

## Day 10 — Sep 29
Wrote `src/rag/generate.py`: wires `retriever.py` (Day 8) and `prompts.py`
(Day 9) into an actual Claude API call via the `anthropic` SDK, returning
the answer plus a numbered source list. `anthropic` installed cleanly —
pure Python + `httpx`, no native-DLL issue like Day 8's `sentence-transformers`.

Blocked on actually running it: a fresh Anthropic API key has no free
credits — the very first test call returned `invalid_request_error: Your
credit balance is too low`. Confirmed this is a billing gate, not a setup
bug, by checking the error came back as a proper 400 from the API (meaning
auth succeeded) rather than an auth failure. Needs a small credit purchase
on the Anthropic console before `generate.py` can actually be exercised —
not blocking the code itself, which is written and ready.

## Day 10 (continued) — Sep 30
Decided against paying for Anthropic credits right now — swapped
`generate.py` to Groq's free tier (Llama 3.3, OpenAI-compatible chat API)
instead. This only meant changing the one function that makes the LLM
call: `retriever.py` and `prompts.py` don't know or care which vendor
eventually reads their output, which is exactly why that separation was
worth having. Removed the now-unused `anthropic` package, updated
`requirements.txt`/`.env.example`/README to match. Waiting on a Groq API
key to actually run it.

## Day 10 (finished) — Sep 30
Got the Groq key, ran `generate.py`, hit two more real bugs before it
worked:

1. `404 model_not_found` on `llama-3.3-70b-versatile` — Groq's free-tier
   model catalog had moved on. Queried `GET /openai/v1/models` with the
   actual key instead of guessing again, and switched to `openai/gpt-oss-120b`,
   the largest currently-available chat model. Noted in the code to check
   that endpoint again if this model ever disappears too — a hosted
   provider's catalog is not a stable thing to hardcode against blindly.
2. `UnicodeEncodeError` printing the answer — the model's output contained
   a narrow no-break space (` `), and Windows' default console
   codepage (cp1252) can't represent it. Fixed by forcing UTF-8 stdout on
   Windows at the top of the script.

**First full grounded answers came back correctly** — all three test
queries produced a verdict, reasoning citing the right numbered passages,
and an explicit caveat about not being a binding ethics authority. Example:
"is it OK for a recommendation system to be designed to be addictive?" →
correctly invoked Ahimsa, Dharma, Viveka, *and* Aparigraha, citing the
Yoga Sutras passage about senses being "like unruly horses" for the
Viveka/discernment point. This is the core RAG pipeline working
end-to-end: retrieval → grounded generation → cited answer.

## Day 11 — Sep 30
Added proper citation rendering to `generate.py`'s output: a
`SOURCE_LABELS` map turns the raw slugs (`gita_arnold`) into real names
("Bhagavad Gita (trans. Edwin Arnold)") for eventual UI display, and
`_short_quote()` adds a ~160-character excerpt next to each source instead
of just the verse reference — so a citation reads as "[1] The Upanishads
(trans. Swami Paramananda), v.p256-p258 — 'he who possesses right
discrimination...'" instead of a bare reference number.

## Day 12 — Week 2 retrospective — Sep 30
**Week 2 done: the RAG pipeline works end-to-end**, question to cited
answer. What got built:

- `embeddings.py` — Voyage AI embeddings, rate-limit-safe (20/batch, 21s
  apart, retry-with-backoff on 429)
- `index.py` — embeds all 448 chunks into a persistent ChromaDB collection
- `retriever.py` — top-20 by embedding similarity, re-ranked by a
  principle-tag boost using a *second* keyword lexicon tuned to modern
  AI-ethics phrasing (separate from chunk.py's ancient-text lexicon)
- `prompts.py` — the grounded system prompt (cite-by-number, say "I don't
  know" over inventing a citation, name the classical principle before
  mapping it)
- `generate.py` — retrieval + prompt + Groq API call (`openai/gpt-oss-120b`),
  returning an answer plus human-labeled, quoted citations

What this week was actually about, underneath the RAG mechanics: three
real infrastructure fights, each solved by changing the plan instead of
forcing the original one — a local ML library blocked by Windows security
policy (→ hosted embeddings), a paid API with no free credits (→ a free
one), and a model name that stopped existing between when the plan was
written and when the code ran (→ checking the live model list instead of
assuming). None of these were code bugs in the usual sense; all three are
exactly the kind of thing a job actually involves.

**Verified this session:** local `git log` and `origin/main` point at the
identical commit (`ef4c445`) — nothing uncommitted, nothing unpushed.
14 commits since Day 0.

Next: Week 3 — the Ethics Scorecard (score an AI feature against all seven
principles) and a real evaluation set.

## Day 13 — Oct 1
Designed the Ethics Scorecard's data contract in `src/scorecard/schema.py`:
a JSON schema requiring exactly one entry per principle (score 1-5,
rationale, mitigation) plus an overall summary, with `validate_scorecard()`
checking any proposed scorecard against it — including a missing-principle
check the raw JSON Schema can't express on its own (JSON Schema can bound
array length but not "one of each enum value present").

Also wrote `SCORE_SCALE`: a one-line meaning for each of 1-5, so a score
isn't just a number the model picked — it's anchored to a definition
(score.py's prompt, Day 14, will include this so two runs score the same
feature consistently instead of drifting). Tested the validator against a
valid scorecard (no errors) and a deliberately broken one (score out of
range + six missing principles) — both caught correctly.
