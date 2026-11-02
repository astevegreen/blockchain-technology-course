-- Day 10 final trace: ready-made queries over the invented Tron snapshot (../snapshot), for DuckDB.
-- Students run these on the query page and read the output; they never edit them. Nothing here names the case's
-- addresses: finding them is the trace. Each query starts with a "-- name:" line; the query page shows them in order.
-- Column types are declared, not guessed: guessed, time_utc becomes a zoned timestamp shown in the viewer's local time.

CREATE OR REPLACE VIEW tx AS
SELECT * FROM read_csv('transactions.csv', header = true, columns = {
  'tx_id': 'VARCHAR', 'block': 'BIGINT', 'time_utc': 'TIMESTAMP', 'type': 'VARCHAR', 'signer': 'VARCHAR',
  'result': 'VARCHAR', 'fee_sun': 'BIGINT', 'energy_used': 'BIGINT', 'energy_fee_sun': 'BIGINT', 'bandwidth_used': 'BIGINT'});

CREATE OR REPLACE VIEW tr AS
SELECT r.*, t.block, t.time_utc, t.type, t.signer, t.fee_sun, t.energy_used, t.energy_fee_sun
FROM read_csv('transfers.csv', header = true, columns = {
  'tx_id': 'VARCHAR', 'seq': 'INTEGER', 'asset': 'VARCHAR', 'from_addr': 'VARCHAR', 'to_addr': 'VARCHAR',
  'amount': 'DECIMAL(38,6)'}) r
JOIN tx t USING (tx_id);

-- What a source says about an address, one line per address (labels.csv names the source for each).
CREATE OR REPLACE VIEW labels AS
SELECT address, string_agg(label || ' [' || source || ']', '; ' ORDER BY source) AS label
FROM read_csv('labels.csv', header = true, columns = {
  'address': 'VARCHAR', 'label': 'VARCHAR', 'source': 'VARCHAR', 'as_of': 'DATE'})
GROUP BY address;

CREATE OR REPLACE VIEW freeze_status AS
SELECT * FROM read_csv('freeze.csv', header = true, columns = {
  'address': 'VARCHAR', 'usdt_blacklisted': 'BOOLEAN', 'usdt_balance': 'DECIMAL(38,6)', 'as_of_block': 'BIGINT',
  'as_of_time_utc': 'TIMESTAMP'});

-- name: 1. Labelled addresses: what the case file and published lists say
SELECT address, label FROM labels ORDER BY address;

-- name: 2. Every transfer in the snapshot, oldest first, with any label on either side
SELECT t.time_utc, t.block, t.asset, t.amount, t.from_addr, lf.label AS from_label, t.to_addr, lt.label AS to_label,
       t.signer, t.tx_id
FROM tr t
LEFT JOIN labels lf ON lf.address = t.from_addr
LEFT JOIN labels lt ON lt.address = t.to_addr
ORDER BY t.block, t.seq, t.tx_id;

-- name: 3. Every address in one row each: USDT in and out, TRX in, how many counterparties, first and last seen
WITH legs AS (
  SELECT to_addr AS address, asset, amount, 1 AS dir, from_addr AS other, time_utc FROM tr
  UNION ALL
  SELECT from_addr, asset, amount, -1, to_addr, time_utc FROM tr)
SELECT g.address, l.label,
       coalesce(sum(amount) FILTER (WHERE asset = 'USDT' AND dir = 1), 0) AS usdt_in,
       count(*) FILTER (WHERE asset = 'USDT' AND dir = 1) AS usdt_receipts,
       coalesce(sum(amount) FILTER (WHERE asset = 'USDT' AND dir = -1), 0) AS usdt_out,
       count(*) FILTER (WHERE asset = 'USDT' AND dir = -1) AS usdt_sends,
       coalesce(sum(amount) FILTER (WHERE asset = 'TRX' AND dir = 1), 0) AS trx_in,
       count(DISTINCT other) FILTER (WHERE dir = 1) AS senders,
       count(DISTINCT other) FILTER (WHERE dir = -1) AS recipients,
       min(time_utc) AS first_seen, max(time_utc) AS last_seen
FROM legs g LEFT JOIN labels l ON l.address = g.address
GROUP BY g.address, l.label
ORDER BY usdt_in DESC, g.address;

-- name: 4. Flows: every sender-to-recipient pair, with the total, the count and the first and last time
SELECT from_addr, to_addr, asset, sum(amount) AS total, count(*) AS transfers, min(time_utc) AS first_utc,
       max(time_utc) AS last_utc
FROM tr
GROUP BY from_addr, to_addr, asset
ORDER BY first_utc;

-- name: 5. Everything each labelled address sent, oldest first
SELECT l.label AS sender, t.time_utc, t.asset, t.amount, t.to_addr, t.tx_id
FROM tr t JOIN labels l ON l.address = t.from_addr
ORDER BY l.label, t.block, t.seq;

-- name: 6. Each USDT send, with any TRX its sender received in the 30 minutes before (TRX pays the fee)
SELECT u.time_utc, u.from_addr, u.amount AS usdt_sent, u.to_addr, f.from_addr AS trx_from, f.amount AS trx,
       f.time_utc AS trx_utc
FROM tr u
LEFT JOIN tr f ON f.asset = 'TRX' AND f.to_addr = u.from_addr
              AND f.time_utc BETWEEN u.time_utc - INTERVAL 30 MINUTE AND u.time_utc
WHERE u.asset = 'USDT'
ORDER BY u.block, u.seq;

-- name: 7. USDT held and freeze status at the end of the snapshot, largest holdings first
SELECT f.address, l.label, f.usdt_balance, f.usdt_blacklisted, f.as_of_block, f.as_of_time_utc
FROM freeze_status f LEFT JOIN labels l ON l.address = f.address
ORDER BY f.usdt_balance DESC, f.address;
