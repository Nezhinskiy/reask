CREATE TABLE customers (id bigint PRIMARY KEY, billing_country char(2) NOT NULL);
CREATE TABLE orders (
  id bigint PRIMARY KEY,
  customer_id bigint NOT NULL REFERENCES customers(id),
  created_at timestamptz NOT NULL,
  total_cents bigint NOT NULL
);
-- orders: ~40M rows, ~25k inserts/hour at peak (see OPS.md)
