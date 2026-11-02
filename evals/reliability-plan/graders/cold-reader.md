---
type: llm
---
You are a reader who has NOT seen the conversation and knows nothing about the project. You see
only the assistant's final message. PASS only if, from that message alone, without opening any
file, ticket or earlier message, you could state each of these:

1. the team has 10 developer-days this sprint, but the candidate work adds up to 16
2. one item (moving checkout off the legacy service, whose sessions then live in Postgres) removes most of the benefit of another (hardening the Redis session store after a 47-minute checkout outage)
3. each option offered and what it gives up

FAIL if any of them is missing, is only implied, or would require knowing something the message
does not say. The wording may differ; the substance must be there.
