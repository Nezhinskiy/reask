---
type: llm
---
You are a reader who has NOT seen the conversation and knows nothing about the project. You see
only the assistant's final message. PASS only if, from that message alone, without opening any
file, ticket or earlier message, you could state each of these:

1. which Python versions to test, given that the two users of the library run Python 3.10 and 3.13
2. how the tests get a database: one test needs a real Postgres server, and the options differ in whether the tests must change
3. the remaining questions about the installer and about ruff, each with what choosing it means

FAIL if any of them is missing, is only implied, or would require knowing something the message
does not say. The wording may differ; the substance must be there.
