"""Run every case in data/eval/dilemmas.jsonl through the scorecard and
compare the result to each case's `expected_low` labels.

Results append to data/eval/results.jsonl one case at a time, so a crash or
rate-limit failure halfway through doesn't throw away the cases that
already finished — re-running only retries the ones that failed or are
missing. `--report-only` rebuilds docs/EVAL_RESULTS.md without calling any
API.

The automated numbers only say whether the scorecard flagged what I
expected it to flag. They can't say whether a rationale is *true to the
description* — that part is graded by hand (see the report).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "scorecard"))

from schema import PRINCIPLES  # noqa: E402

DILEMMAS = ROOT / "data" / "eval" / "dilemmas.jsonl"
RESULTS = ROOT / "data" / "eval" / "results.jsonl"
REPORT = ROOT / "docs" / "EVAL_RESULTS.md"
LOW = 2  # a score at or below this counts as "flagged"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def latest_results() -> dict[str, dict]:
    latest = {}
    for r in load_jsonl(RESULTS):
        latest[r["id"]] = r
    return latest


def run_all() -> None:
    from score import score_feature  # imported here so --report-only needs no API keys

    done = {i for i, r in latest_results().items() if "error" not in r}
    todo = [d for d in load_jsonl(DILEMMAS) if d["id"] not in done]
    print(f"{len(done)} already done, {len(todo)} to run")
    for n, d in enumerate(todo, start=1):
        print(f"[{n}/{len(todo)}] {d['id']} ...", flush=True)
        try:
            res = score_feature(d["description"])
            rec = {
                "id": d["id"],
                "scores": {s["principle"]: s for s in res["scorecard"]["scores"]},
                "overall_summary": res["scorecard"]["overall_summary"],
                "attempts": res["attempts"],
                "sources": res["sources"],
            }
        except Exception as e:  # keep going; failures are retried on the next run
            rec = {"id": d["id"], "error": f"{type(e).__name__}: {e}"}
            print(f"  FAILED: {rec['error']}", flush=True)
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_report() -> str:
    dilemmas = {d["id"]: d for d in load_jsonl(DILEMMAS)}
    latest = latest_results()
    ok = {i: r for i, r in latest.items() if "error" not in r and i in dilemmas}
    failed = [i for i in dilemmas if i not in ok]

    expected_n = defaultdict(int)
    caught_n = defaultdict(int)
    extra_n = 0
    rows, discuss = [], []
    kind_scores = defaultdict(list)
    control_false_alarms = 0

    for i, d in dilemmas.items():
        if i not in ok:
            continue
        r = ok[i]
        scores = {p: r["scores"][p]["score"] for p in PRINCIPLES}
        kind_scores[d["kind"]].extend(scores.values())
        flagged = {p for p, s in scores.items() if s <= LOW}
        expected = set(d["expected_low"])
        caught, missed, extra = expected & flagged, expected - flagged, flagged - expected
        for p in expected:
            expected_n[p] += 1
            caught_n[p] += p in caught
        extra_n += len(extra)
        if d["kind"] == "control" and flagged:
            control_false_alarms += 1
        fmt = lambda s: ", ".join(sorted(s)) or "-"
        rows.append(f"| {i} | {d['kind']} | {fmt(expected)} | {fmt(flagged)} | {fmt(missed)} | {fmt(extra)} | {r['attempts']} |")
        if missed or (d["kind"] == "control" and flagged):
            lines = [f"### {i} ({d['kind']})", f"> {d['description']}", ""]
            for p in sorted(missed):
                lines.append(f"- **missed {p}** (scored {scores[p]}): {r['scores'][p]['rationale']}")
            if d["kind"] == "control":
                for p in sorted(flagged):
                    lines.append(f"- **false alarm {p}** (scored {scores[p]}): {r['scores'][p]['rationale']}")
            discuss.append("\n".join(lines))

    total_exp, total_caught = sum(expected_n.values()), sum(caught_n.values())
    n_controls = sum(1 for i in ok if dilemmas[i]["kind"] == "control")
    out = ["# Evaluation results", "",
           f"Scored cases: {len(ok)} of {len(dilemmas)}"
           + (f" (failed, rerun needed: {', '.join(failed)})" if failed else ""),
           f"\"Flagged\" means a principle scored {LOW} or lower. `expected_low` labels are the "
           "author's judgment, not ground truth.", "",
           "## Headline numbers", "",
           f"- Expected-low principles flagged: **{total_caught} / {total_exp}**"
           + (f" ({total_caught / total_exp:.0%})" if total_exp else ""),
           f"- Control cases with a false alarm: **{control_false_alarms} / {n_controls}**",
           f"- Principles flagged that were *not* expected: {extra_n} (not automatically wrong; "
           "read them before counting them as errors)",
           f"- Flag precision against `expected_low`: **{total_caught} / {total_caught + extra_n}**"
           + (f" ({total_caught / (total_caught + extra_n):.0%})" if total_caught + extra_n else "")
           + " — recall alone is easy to inflate by flagging everything, so read the two together"]
    for kind in ("problem", "mixed", "control"):
        if kind_scores[kind]:
            out.append(f"- Mean score, {kind} cases: {mean(kind_scores[kind]):.2f}")
    out += ["", "## Per-principle recall", "", "| principle | caught | expected |", "|---|---|---|"]
    out += [f"| {p} | {caught_n[p]} | {expected_n[p]} |" for p in PRINCIPLES]
    out += ["", "## Per case", "",
            "| case | kind | expected low | flagged | missed | extra | attempts |",
            "|---|---|---|---|---|---|---|"] + rows
    out += ["", "## Disagreements to read by hand", ""]
    out += discuss or ["None."]
    return "\n".join(out) + "\n"


def show(case_id: str) -> None:
    dilemmas = {d["id"]: d for d in load_jsonl(DILEMMAS)}
    r = latest_results().get(case_id)
    if case_id not in dilemmas or r is None or "error" in r:
        sys.exit(f"no scored result for '{case_id}' (known ids: {', '.join(dilemmas)})")
    d = dilemmas[case_id]
    print(f"{case_id} ({d['kind']}), expected low: {', '.join(d['expected_low']) or '-'}\n")
    print(d["description"], "\n")
    for p in PRINCIPLES:
        s = r["scores"][p]
        print(f"{p} {s['score']}/5\n  why: {s['rationale']}\n  fix: {s['mitigation']}")
    print(f"\nsummary: {r['overall_summary']}")


if __name__ == "__main__":
    if "--show" in sys.argv:
        show(sys.argv[sys.argv.index("--show") + 1])
        sys.exit()
    if "--report-only" not in sys.argv:
        run_all()
    REPORT.write_text(build_report(), encoding="utf-8")
    print(f"wrote {REPORT}")
