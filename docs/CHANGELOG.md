# Scorecard changelog

What changed in the scorecard between eval runs, and what the eval said
about it. Numbers come from `docs/EVAL_RESULTS_v1.md` and
`docs/EVAL_RESULTS.md`.

## v2 — evidence-first prompt (Oct 3)

### Why

v1 had two problems (see `LOG.md`, Day 16):

1. **Stated facts ignored.** `predictive-policing` says the training records
   "come mostly from neighborhoods that were already heavily patrolled", yet
   Nyaya scored 3 with "no information about fairness."
2. **Flagging almost everything.** 44% flag precision against my
   `expected_low` labels, ~5 of 7 principles flagged on a typical problem case.

### What changed

1. **Every score now needs an `evidence` field**: an exact quote from the
   description, or the literal string `none stated`. `schema.py` checks the
   quote really appears in the description (case, whitespace, curly quotes
   and non-breaking hyphens normalised); a made-up quote fails validation
   and the model is sent the error and retried.
2. **`none stated` forces a score of exactly 3**, enforced in code as well
   as in the prompt. The prompt also says a safeguard that isn't mentioned is
   not a risk.
3. **The Nyaya definition in the prompt was widened** from "decisions fair,
   inspectable, and contestable" to include "biased or unrepresentative
   training data". The first attempt at (1) and (2) alone left
   `predictive-policing` Nyaya at 3 / `none stated`; the definition was
   literally too narrow to cover what the description said.

### Result

| | v1 | v2 |
|---|---|---|
| expected-low principles flagged | 34 / 37 (92%) | 34 / 37 (92%) |
| flag precision vs `expected_low` | 34 / 78 (44%) | 34 / 75 (45%) |
| control cases with a false alarm | 0 / 3 | 0 / 3 |
| mean score: problem / mixed / control | 1.89 / 3.00 / 4.19 | 1.75 / 3.29 / 4.48 |
| cases needing a validation retry | 0 / 19 | 1 / 19 |

**Headline: no real change.** Precision moved 1 point, which is noise. The
evidence requirement did not fix over-flagging.

What it did change:

- **Every score is now auditable.** 31 of 112 entries on the 16 non-control
  cases are an explicit `none stated`, so the model abstains where before it
  scored on vibes. Every other score points at a quote that is really in the
  description.
- **`predictive-policing` now flags Nyaya** in the full run (v1 did not).
  But see variance below; I would not call that case fixed.

What it did *not* fix, found by looking:

- **A real quote does not mean a relevant quote.** In 6 of 16 non-control
  cases, a single quote backs three or more flagged principles. E.g. "sends
  extra patrols to the top-ranked areas" is cited as evidence for Ahimsa,
  Dharma, Seva and Viveka at once. The validator proves the quote exists, not
  that it bears on the principle.
- **Variance.** The same `predictive-policing` input produced three
  different scorecards across three runs: six principles at 3 (before the
  Nyaya change), seven principles flagged (right after it), and two flagged
  in the full eval. One run per case is an anecdote; the table above is a
  single run too, so small differences between v1 and v2 can't be trusted.
- **Some "misses" may be my labels, not the model.** `dharma` on
  `predictive-policing` and `satya` on `social-credit-lending` are now
  `none stated` because the descriptions really don't mention accountability
  or capability claims. My `expected_low` labels counted implied absences.
  Under the v2 rule, those labels are arguably wrong. Not changed yet.

### Caveats on this evaluation

- I tuned the prompt while looking at these same 19 cases. There is no
  held-out set, so v2's numbers are likely optimistic for new input.
- `expected_low` is one person's judgment.
- Hand grading (`EVAL_HANDGRADES.md`) is not done yet; nothing above says
  whether the rationales are actually *good*.

### Next, in order of value

1. Measure variance directly: run each case 3 times and report how often the
   flagged set changes. Without it, no prompt change can be judged.
2. Reject a scorecard where one quote backs three or more flagged principles,
   or ask for a distinct quote per flag.
3. Reconsider the `expected_low` labels that the `none stated` rule contradicts.

## v1 — first scorecard (Oct 2)

Seven principles scored 1-5 with a rationale and a mitigation each, JSON
validated against `schema.py`, one retrieval of six passages shared across
all principles. 92% recall, 44% precision, 0/3 control false alarms.
