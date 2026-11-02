---
type: llm
---
You are a reader who has NOT seen the conversation and knows nothing about the project. You see
only the assistant's final message. PASS only if, from that message alone, without opening any
file, ticket or earlier message, you could state each of these:

1. a cache is being added in front of the pricing lookup, and the open decision is what each cache entry is keyed on
2. some products have different prices in countries that share a currency (for example B-2210 costs 49 euros in Germany and 45 in Austria), so a key that ignores the locale or country would show some customers the wrong price
3. each option offered, with what it costs (for example more cache entries or a lower hit rate, against a risk of wrong prices)

FAIL if any of them is missing, is only implied, or would require knowing something the message
does not say. The wording may differ; the substance must be there.
