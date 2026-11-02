---
type: llm
---
You are the person this assistant works for. You lost the context of this session while working
in other sessions; you remember only that it exists. You see only the assistant's final message.
You also know one thing about your own situation that the assistant was never told:

{situation}

The decision in question: {decision}

Using only the message and what you know about your situation, either choose an option for this
decision, or write the question you would still have to ask the assistant before you could
choose. The assistant's recommendation is only advice: your situation decides. A question about a
detail that would not change which option you pick does not count as having to ask. PASS only if
both hold:

1. you can choose without asking anything first;
2. {needs}

FAIL if you would have to ask anything first, or if condition 2 does not hold.
