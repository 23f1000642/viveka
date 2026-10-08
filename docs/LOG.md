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

## Day 14 — Oct 2
Wrote `src/scorecard/score.py`. Design choices worth remembering:

- **One retrieval, not seven.** Scoring each principle with its own
  retrieval would mean seven embedding calls, and the free Voyage tier
  allows 3 requests/minute. One retrieval of six passages is shared across
  all seven principles instead.
- **Validate, then retry with the errors.** The model's JSON goes through
  `validate_scorecard()`; if it fails, the exact problems are sent back
  ("missing principles: [...]") and the model corrects itself, up to three
  attempts, then raises. A broken scorecard never reaches a user.
- `API_URL`, `MODEL` and the key lookup are imported from `generate.py`
  instead of copied — the model name has already gone stale once, so it
  should live in exactly one place.

First run on a facial-recognition-in-retail description validated on
attempt 1 and the scores read as sensible (storing every shopper's face for
90 days → Aparigraha 2/5; no mention of human review → Viveka 3/5 with "the
description doesn't address it", per the prompt's no-inventing rule).
Passages were retrieved but the rationales didn't cite them — fine for now
(citation is optional in the prompt), worth revisiting in the eval set.

## Day 15 — Oct 2
Wrote the evaluation set: 19 realistic AI-feature descriptions in
`data/eval/dilemmas.jsonl` — 15 `problem` cases (hiring screener,
predictive policing, teen ad targeting, ER triage, exam proctoring...), 1
`mixed` case (a mental-health chatbot that is good on almost everything
except indefinite transcript retention), and 3 `control` cases (a
mammogram assistant, an on-device spam filter, a library book widget)
that were deliberately designed well.

Each entry carries `expected_low`: the principles a thoughtful reviewer
would expect to score 2 or below. The controls are the important part —
without them, a scorecard that reflexively scores everything low would
look great on the problem cases. These labels are *my judgment calls*, not
ground truth; Day 16's run is meant to be graded by hand against them, and
disagreements are as informative as agreements.

Coverage of `expected_low` per principle: ahimsa 7, nyaya 7, satya 6,
dharma 6, viveka 5, aparigraha 4, **seva 2** — thinnest, so Seva results
will be the least trustworthy signal in the first eval run.

## Day 16 — Oct 2
Wrote `src/eval/run_eval.py` and ran all 19 cases through the scorecard.
Results append to `data/eval/results.jsonl` one case at a time and a re-run
only retries failures — that mattered immediately: 4 of 19 cases died on
`ConnectionResetError` (the remote end dropped the connection mid-run), and
the retry picked up exactly those. One of the four (`fitness-data-hoard`)
failed in the middle of the run and I only noticed because the retry said
"4 to run" instead of the 3 I'd seen at the tail — a reminder to grep a long
run's output for `FAILED` rather than trust its last few lines.

**What the numbers say** (full detail in `docs/EVAL_RESULTS_v1.md`):

- Expected-low principles flagged: 34/37 (92%). Control cases with a false
  alarm: 0/3 (mean score 4.19, vs 1.89 on problem cases). Good.
- But **flag precision is only 34/78 (44%)**: on problem cases the model
  flags ~5 of 7 principles where I expected ~2. The 92% recall is partly
  just a model that flags nearly everything on anything bad-sounding. I
  added the precision line to the report because recall alone was flattering
  the scorecard. Many "extra" flags may be legitimate (seva/viveka on
  chatbot-overclaim is arguable) — that's what the hand grading is for.
- **A concrete faithfulness failure:** `predictive-policing`. The description
  says outright that the arrest records "come mostly from neighborhoods that
  were already heavily patrolled" — a textbook fairness (Nyaya) problem —
  yet Nyaya scored 3 with the rationale "the description provides no
  information about fairness." The model scored six of seven principles 3 on
  that case by applying the prompt's "if the description says nothing, score
  3" rule, including to a principle the description speaks to directly. This
  is my reading; it needs checking by hand (see `docs/EVAL_HANDGRADES.md`).
- Same prompt, two behaviours: near-neutral 3s on predictive-policing, but
  4-6 flags on `fake-human-sales-calls` and `warehouse-robot-accountability`.
  That inconsistency, more than the recall figure, is what Day 17 should
  chase.

Added `--show <case-id>` to print one scorecard in readable form for the
hand-grading step.

## Day 17 — Oct 3
Tried to fix the two v1 problems by making the model quote its evidence:
every score now carries a verbatim quote from the description (or `none
stated`, which forces a 3), and `schema.py` rejects invented quotes. Full
write-up with before/after table in `docs/CHANGELOG.md`.

The honest summary is that **it did not move the headline numbers**:
recall 92% → 92%, precision 44% → 45%, controls still 0/3 false alarms.
What it bought was auditability (31 explicit abstentions; every score tied
to a real quote), not accuracy.

Three things I learned that are more useful than the numbers:

1. **My first fix didn't work, and the reason was the prompt's own
   definition.** `predictive-policing` Nyaya stayed at 3 / `none stated`
   because the prompt defined Nyaya as "inspectable and contestable" and the
   description said nothing about either — it talked about biased data. The
   model followed the definition literally. Widening the definition fixed
   that case.
2. **A verified quote isn't a relevant quote.** One sentence ("sends extra
   patrols to the top-ranked areas") was cited as evidence for four
   different principles. My validator proves the quote exists; it cannot
   prove it supports the principle.
3. **Variance is larger than any effect I'm trying to measure.** Same
   input, three runs, three different scorecards (six principles at 3;
   seven flagged; two flagged). With one run per case, a 1-point change in
   precision means nothing. Measuring variance (3 runs per case) is the
   first thing to do before any further prompt change.

Not done: hand grading (still the user's), and the `expected_low` labels
that the `none stated` rule now contradicts. Also tuned on the same 19 cases
I evaluate on, so v2's numbers are likely optimistic.

Process slip worth noting: I launched the full eval chained to the commit
with its output sent to `/dev/null`, which would have hidden failures. The
report still caught the one real failure (a Groq 429 on
`insurance-auto-denial`), and the resume logic retried just that case.

## Day 18 — Oct 4
Used the buffer day for a safety gap I found by typing something real into
the app. Asked "I am feeling depressed because no one is giving me
attention", the advisor answered in full AI-ethics voice, with verses, and
told the person their problem was a "cycle of attention-seeking". Nothing in
the project knew that message wasn't an AI-ethics question. For a public demo
that is a real defect, and it contradicts the project's own Ahimsa principle.

**What I built** (all in `src/rag/`):

- `scope.py`: a classifier that sorts each message into `in_scope`,
  `personal_distress` or `off_topic` *before* any retrieval, so out-of-scope
  input also skips the rate-limited embedding call.
- **The two non-answers are fixed text, not model output.** Someone who is
  struggling should get a message that was reviewed in advance, not whatever
  the model says that day. It acknowledges them, says plainly what this tool
  is not, points to a person they trust, and to a crisis line directory
  (findahelpline.com) rather than a country-specific number I can't verify.
- **Deliberate bias:** unsure between in-scope and off-topic means in-scope
  (don't turn away a legitimate user); unsure whether it's distress means
  distress (a kind reply in the wrong place costs far less than ignoring
  someone). A message that asks about an AI system stays in scope even if the
  writer mentions feelings, since "I'm lonely and use a companion app, should
  apps be allowed to do that?" is a legitimate design question.
- `generate_answer` returns the fixed reply with `scope` set and no sources;
  `score_feature` raises `OutOfScope`, because a scorecard has no place to
  put a text reply.
- Refactor first, as its own commit: `llm.py` now holds the provider URL,
  model name and key lookup for `generate.py`, `score.py` and `scope.py`.
  Doing that dropped the stdout-UTF-8 fix `score.py` had been getting
  indirectly through importing `generate`; re-added it directly.

**Result:** `run_scope_eval.py` on 21 cases (8 in-scope, 6 distress, 7
off-topic, including prompt-injection, a borderline personal+AI case and 3
Hinglish messages): 21/21, with 0 distress messages missed and 0 legitimate
questions blocked. Also re-ran the original message end to end: it now gets
the kind reply, no sources, no retrieval.

**Limits, stated plainly:**
- I wrote both the classifier prompt and the test cases, so the cases fit my
  own idea of the categories. 21/21 on a set the author wrote is weak
  evidence. It should be tried against messages I didn't think of.
- The fixed replies are English only. The classifier handled Hinglish input,
  but a Hinglish message gets an English reply.
- If the classifier's JSON is unreadable it falls back to `in_scope`, which in
  the worst case reproduces the old behaviour.
- Single messages only; no conversation context.

## Day 19 — Oct 6
Started the Streamlit UI (`app.py`: chat input, answer, principles
detected, and a "Sources" expander showing each citation with translator,
book, verse and quote). Getting it to run turned into a bigger job than the
UI itself.

**The app crashed on import: `ImportError: DLL load failed while importing
cygrpc: An Application Control policy has blocked this file.`** That is the
same Windows policy as Day 8, but it hit a different package: `grpc`, pulled
in by ChromaDB's telemetry code. `grpc` was installed on Sep 28 and imported
fine through Oct 4. So this machine's policy is **not stable over time**;
a compiled dependency that works today can be blocked later. Checked what
else was affected: numpy, pandas, pyarrow, pydantic_core, rpds, jsonschema
and streamlit all still import. Only `grpc` was blocked.

**Decision: drop ChromaDB instead of working around gRPC.** The corpus is
448 chunks. A vector database was overkill, and its dependency tree
(gRPC, OpenTelemetry, Kubernetes client...) was the actual problem. Wrote
`src/rag/vectorstore.py`, standard library only: embeddings in one float32
file, text and metadata in one JSON file, and a query scans every vector
(~230k multiplications, tens of milliseconds). Nothing native, so nothing
for a policy to block. It uses squared L2 distance, the number ChromaDB
returned by default, so the retriever's boost value keeps its meaning.
Side benefit: the whole index is 1.4 MB, so it is committed to the repo
(`data/index/`) and a deployed copy needs no 8-minute embedding job.

**Checked it is equivalent, not just working.** Rebuilt the index (re-embedded
all 448 chunks) and re-ran the Day 8 queries: 4 of the 5 gave the same top
chunk with the same raw distance and adjusted score to 3 decimals as the
ChromaDB numbers logged on Day 8. The fifth differs because the "explainable"
keyword fix landed after that log entry; its new top chunk is the one the
later hiring-question answers already cited.

**Tested the UI in a browser, not just the code:** a normal question gives a
cited answer with a working Sources expander, and the distress message from
Day 18 gets the fixed kind reply with no verses and no sources, instantly
(the guard skips retrieval).

**Problem the UI made visible:** citations like `Book Ii, verse(s) 7,p91,8`
and `p242,51,p243`. That is the Day 5 issue (numbered sutras interleaved with
unnumbered commentary, so a chunk's verse list mixes real sutra numbers with
paragraph counters). Harmless in a log file, but it looks wrong to a user
and is exactly what citations must not do. Not fixed yet.

Process notes: `git push` was rejected because the remote had 2 README commits
(made from the GitHub web editor). Integrated with `git pull --rebase
--autostash` rather than forcing anything, and left that README wording as
written.

Still ahead for the UI: the scorecard tab, example questions, proper error
handling (an unhandled exception currently shows a raw traceback), and
deployment.

## Day 20 — Oct 7
Added the scorecard to the UI as a second page ("Audit a feature", at
`/audit`), using `st.navigation` rather than tabs. Reason: Streamlit pins
`st.chat_input` to the bottom of the page only when it is at the top level,
so putting the chat inside a tab would have moved the input box mid-page. A
separate page also gets its own URL, which helps once it's deployed.

The page opens with an example description pre-filled (labelled as an
example), so it isn't an empty form. Pressing "Score this feature" shows the
summary, a horizontal bar chart of the seven scores, and one expander per
principle with the quoted evidence, the reasoning and a suggested change.
Principles scoring 2 or below open expanded; the rest start collapsed.
The scored result is kept in `st.session_state` so opening/closing an expander
(which re-runs the script) doesn't wipe it.

Tested in a browser: the example scores correctly and renders; the
distress message sent to the audit page gets the same fixed kind reply (via
the `OutOfScope` exception) and no scorecard.

**What the UI exposed:** the same example description scored Satya 5/5 and
Viveka 4/5 today, against Satya 3/5 and Viveka 3/5 in the Day 14 run. That is
the run-to-run variance from `docs/CHANGELOG.md`, now visible to anyone who
presses the button twice. Rather than hide it, the page says so under the
summary: scores can change between runs, read the evidence and not just the
number, treat it as input to a human review. Measuring the variance properly
(3 runs per case) is still the open item.

Not done: the bar chart colours every bar the same (the colour lives in the
expander labels), and the verse-reference problem from Day 19 is still there.

## Day 21 — Oct 8
Fixed the citation problem the UI had exposed, instead of starting the
example-questions sidebar (that is still to do).

**Cause.** The `verse` ids from `clean.py` are a mix: real sutra numbers where
the translator numbered them, and this project's own paragraph counters
(`p91`) everywhere else. A chunk's list of them (`7,p91,8`) therefore pointed
at nothing a reader could look up in a book.

**Fix, in layers:**
- `chunk.py` now adds a `reference` to every chunk, built only from structure
  that really exists in the text: Gita chapter (from the `CHAPTER N` heading
  records), Upanishad name (from the `Katha-Upanishad` etc. headings), and for
  the Yoga Sutras the book plus the real sutra numbers, marked "with
  commentary" when unnumbered commentary paragraphs sit in the chunk. The
  `pNN` counters never appear. Example: `Book II, sutras 7-8 with commentary`
  (was `Book Ii`, `7,p91,8`).
- **Chunk ids, text, tags and verses are unchanged**; I checked all 448
  against the committed version and only the new field differs. That kept
  retrieval and every earlier eval result valid.
- To avoid another 8-minute re-embedding for what is only a metadata change,
  `index.py --metadata-only` rewrites metadata and keeps the vectors.
  `vectorstore.update_metadata` refuses if any chunk id is missing or any
  chunk's text differs from what the vector was computed from (tested both
  refusals). The `vectors.f32` hash was identical before and after.
- Threaded `reference` through the retriever and `generate_answer`, and the
  UI now prints it under each source.

**Spot-checked against the content, not just the code:** "Good Pleasure is the
pleasure that endures" comes out as Gita Chapter XVIII, and "the good is one
thing and the pleasant another" as Katha Upanishad; both are right.

**Limits of the new references.** They are only as precise as the structure
the text offered: Gita and Upanishad citations stop at chapter or Upanishad
level (no verse numbers, because Arnold's and Paramananda's texts don't
carry them in a form `clean.py` kept), and Yoga Sutra numbers follow
Johnston's numbering, which differs from some other editions (see Day 2). A
chunk that crosses a chapter boundary reads "Chapter III to Chapter IV".
Whether the cited passages actually support the claims the model attaches
to them is a separate question this change does not touch.
