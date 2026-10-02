# Hand grading

The automated numbers in `EVAL_RESULTS.md` only show whether the scorecard
flagged what I expected. They cannot show whether a rationale is *true to
the description*. That has to be read by a person.

To read one case:

```
python src/eval/run_eval.py --show predictive-policing
```

## Rubric (per case, two scores, 0 to 2 each)

**Faithfulness** — does each rationale stick to what the description says?

- 2: every rationale is supported by the description, or correctly says the
  description doesn't address that principle
- 1: one rationale misses something the description states, or claims
  something it doesn't
- 0: two or more such errors, or an invented fact

**Usefulness of fixes** — could a team act on each mitigation?

- 2: specific and actionable
- 1: a mix of specific and generic ("conduct audits")
- 0: mostly generic

## Cases to grade

Chosen to cover the interesting behaviours, not a random sample.

| case | why this one | faithfulness (0-2) | usefulness (0-2) | notes |
|---|---|---|---|---|
| predictive-policing | the description states a fairness problem outright, yet Nyaya scored 3: check that claim | | | |
| worker-surveillance | all 7 principles flagged: is that earned? | | | |
| fake-human-sales-calls | 4 flags beyond what was expected | | | |
| social-credit-lending | missed Satya; flagged 5 unexpected | | | |
| mental-health-chatbot | the only `mixed` case: does it separate the good from the bad? | | | |
| mammogram-assistant | a control: are the high scores earned or just generous? | | | |

Fill in the table, then write two or three sentences below on what you
think the scorecard gets wrong most often. That paragraph is the input to
Day 17's prompt changes.

## What I conclude

