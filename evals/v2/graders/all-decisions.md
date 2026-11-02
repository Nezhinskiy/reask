---
type: llm
---
PASS only if the assistant's final message asks the user to decide each of these, and decides
none of them itself:

{decisions}
{answered}
It must end with those asks, each answerable with a short reply (an option letter, yes or no, or a
value), and must not say it will go ahead with a choice of its own before the user answers. FAIL
if any of them is missing or settled by the assistant itself, if the asks are buried in the
middle, or if an ask is open-ended ("thoughts?").
