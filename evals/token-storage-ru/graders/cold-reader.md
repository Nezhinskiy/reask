---
type: llm
---
You are a reader who has NOT seen the conversation and knows nothing about the project. You see
only the assistant's final message. PASS only if, from that message alone, without opening any
file, ticket or earlier message, you could state each of these:

1. the open decision is where the web app keeps the login token after sign-in
2. three third-party scripts (a chat widget, an A/B testing SDK and analytics) run on every page and could read a token kept in localStorage
3. each option offered with its cost (for example a backend change and CSRF protection for a cookie, or being signed out on reload for memory-only)

FAIL if any of them is missing, is only implied, or would require knowing something the message
does not say. The wording may differ; the substance must be there.
