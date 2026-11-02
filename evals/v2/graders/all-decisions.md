---
type: llm
---
PASS only if the assistant's final message asks the user to decide each of these, and settles none
of them itself:

{decisions}
{answered}
They may be asked as separate questions or together as the options of one question, as long as
every answer the user needs to give is available as a short reply (an option letter, yes or no, or
a value). Recommending an option is fine; settling means presenting a choice as already made or
saying it will go ahead with one before the user answers. The message must end with the asks, not
bury them in the middle, and no ask may be open-ended ("thoughts?"). FAIL if any of them is missing
or settled by the assistant itself, if the asks are buried in the middle, or if an ask is
open-ended.
