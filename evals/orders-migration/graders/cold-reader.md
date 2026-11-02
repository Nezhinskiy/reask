---
type: llm
---
You are a reader who has NOT seen the conversation and knows nothing about the project. You see
only the assistant's final message. PASS only if, from that message alone, without opening any
file, ticket or earlier message, you could state each of these:

1. a new required region column is being added to a table of about 40 million orders
2. migrations run inside a deploy job that times out after 10 minutes, and a long table rewrite caused an outage before, which is why the work is split into steps
3. the questions still open (such as where the country-to-region mapping comes from and what an unmapped country gets, and whether old orders may use the customer's current country), each with its options

FAIL if any of them is missing, is only implied, or would require knowing something the message
does not say. The wording may differ; the substance must be there.
