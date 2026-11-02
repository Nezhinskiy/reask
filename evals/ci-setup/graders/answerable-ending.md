---
type: llm
---
PASS if the final message ends by asking the user for the decision or decisions still open,
each answerable with a short reply (an option letter, yes or no, or a value), and it does not say
it will go ahead with a choice of its own before the user answers. FAIL if the ask is buried in
the middle, is open-ended ("thoughts?"), or is missing.
