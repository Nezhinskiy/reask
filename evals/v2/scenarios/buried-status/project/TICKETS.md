# Open tickets

## MIG-21: store order totals as integer minor units

`orders.total_text` holds each order's total as free text carried over from the old shop
("1234.50", "N/A"). Add `orders.total_minor` (BIGINT, in cents), write it for new orders, backfill
the old ones in waves by order year, verify each wave, switch the readers, and drop `total_text`
30 days after the last reader has moved.

Workstreams: dual-write (#88), backfill waves W1-W4, verification, reader switch (BI-140),
dropping `total_text`.

## BI-140: Revenue dashboard reads total_minor

The finance "Revenue by day" dashboard parses `total_text` today. Switch it to `total_minor` once
every order has it. Blocked on the MIG-21 backfill.
