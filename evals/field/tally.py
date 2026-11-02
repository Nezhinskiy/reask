"""Count what classify.py found. These counts are the only part meant to leave your machine.

python3 evals/field/tally.py classified.jsonl
"""

import json
import sys
from collections import Counter
from pathlib import Path

rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
ok = [r for r in rows if "_error" not in r]
dec = [r for r in ok if r.get("decision_pending")]


def share(key):
    k = sum(1 for r in dec if r.get(key))
    return f"{k}/{len(dec)} ({100 * k / max(len(dec), 1):.0f}%)"


print(f"uses: {len(rows)}, judged: {len(ok)}, with a decision pending: {len(dec)}")
print("how reask started:", dict(Counter(r["how"] for r in dec)))
print("dates:", min(r["ts"] for r in dec)[:10], "to", max(r["ts"] for r in dec)[:10])
print("re-ask offered an option the question had not:", share("new_option"))
print("  ...and recommended it:", share("new_option_recommended"))
print("recommendation changed:", share("recommendation_changed"))
print("user decided in their next message:", share("user_decided"))
print("judge's user_pick (noisy, check by hand):", dict(Counter(r.get("user_pick") for r in dec)))
