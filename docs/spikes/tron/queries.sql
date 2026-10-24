-- Ready-made queries over a Tron extract (transactions.csv, transfers.csv), for DuckDB.
-- Students would run these and read the output; they never edit them. Run from the extract's folder.
-- Each query starts with a "-- name:" line; run_queries.py prints them one by one.
-- Column types are declared, not guessed: guessed, time_utc becomes a zoned timestamp shown in the viewer's local time.

CREATE OR REPLACE VIEW tx AS
SELECT * FROM read_csv('transactions.csv', header = true, columns = {
  'tx_id': 'VARCHAR', 'block': 'BIGINT', 'time_utc': 'TIMESTAMP', 'type': 'VARCHAR', 'signer': 'VARCHAR',
  'result': 'VARCHAR', 'fee_sun': 'BIGINT', 'energy_used': 'BIGINT', 'energy_fee_sun': 'BIGINT', 'bandwidth_used': 'BIGINT'});

CREATE OR REPLACE VIEW tr AS
SELECT r.*, t.block, t.time_utc, t.type, t.fee_sun, t.energy_used
FROM read_csv('transfers.csv', header = true, columns = {
  'tx_id': 'VARCHAR', 'seq': 'INTEGER', 'asset': 'VARCHAR', 'from_addr': 'VARCHAR', 'to_addr': 'VARCHAR',
  'amount': 'DECIMAL(38,6)'}) r
JOIN tx t USING (tx_id);

-- An address that both received and sent USDT in the extract, with the wallet it sends most to.
CREATE OR REPLACE VIEW usdt_profile AS
WITH ins AS (
  SELECT to_addr AS address, count(*) AS deposits, count(DISTINCT from_addr) AS senders, sum(amount) AS usdt_in
  FROM tr WHERE asset = 'USDT' GROUP BY 1),
outs AS (
  SELECT from_addr AS address, count(*) AS outflows, count(DISTINCT to_addr) AS recipients,
         sum(amount) AS usdt_out, mode(to_addr) AS main_recipient
  FROM tr WHERE asset = 'USDT' GROUP BY 1)
SELECT * FROM ins JOIN outs USING (address);

-- name: 1. Profile: does each address behave like an exchange deposit address?
SELECT p.*, round(100 * m.to_main / p.usdt_out, 1) AS pct_to_main
FROM usdt_profile p
JOIN (SELECT from_addr AS address, to_addr, sum(amount) AS to_main FROM tr WHERE asset = 'USDT' GROUP BY 1, 2) m
  ON m.address = p.address AND m.to_addr = p.main_recipient
ORDER BY p.address;

-- name: 2. Deposits and sweeps, told apart: each USDT movement with the address's running balance
WITH moves AS (
  SELECT p.address, t.time_utc, t.block, t.seq, t.tx_id,
         CASE WHEN t.to_addr = p.address THEN t.amount ELSE -t.amount END AS signed,
         CASE WHEN t.to_addr = p.address THEN t.from_addr ELSE t.to_addr END AS counterparty,
         p.main_recipient
  FROM usdt_profile p JOIN tr t ON p.address IN (t.from_addr, t.to_addr) AND t.asset = 'USDT'),
bal AS (
  SELECT *, sum(signed) OVER (PARTITION BY address ORDER BY block, seq) AS balance_after FROM moves)
SELECT address, time_utc,
       CASE WHEN signed > 0 THEN 'deposit'
            WHEN counterparty = main_recipient AND balance_after = 0 THEN 'sweep: empties the address'
            ELSE 'other outflow' END AS kind,
       counterparty, abs(signed) AS usdt, balance_after, left(tx_id, 12) AS tx
FROM bal ORDER BY address, block, seq;

-- name: 3. Who paid for each sweep: energy lent to the address in the 10 minutes before it
WITH sweeps AS (
  SELECT t.from_addr AS address, t.to_addr, t.amount, t.time_utc, t.fee_sun, t.energy_used, t.tx_id
  FROM tr t JOIN usdt_profile p ON t.from_addr = p.address AND t.to_addr = p.main_recipient
  WHERE t.asset = 'USDT'),
lent AS (
  SELECT to_addr AS address, from_addr AS lender, amount AS trx_staked, time_utc FROM tr WHERE asset = 'ENERGY_DELEGATED')
SELECT s.address, s.time_utc AS sweep_time, s.amount AS usdt, s.energy_used, s.fee_sun / 1e6 AS fee_trx,
       l.lender, l.trx_staked, date_diff('second', l.time_utc, s.time_utc) AS lent_seconds_before
FROM sweeps s LEFT JOIN lent l
  ON l.address = s.address AND l.time_utc BETWEEN s.time_utc - INTERVAL 10 MINUTE AND s.time_utc
ORDER BY s.address, s.time_utc;

-- name: 4. Noise: dust and unrequested tokens sent to the addresses
SELECT t.to_addr AS address, t.time_utc, t.asset, t.amount, t.from_addr AS sender
FROM tr t JOIN usdt_profile p ON t.to_addr = p.address
WHERE (t.asset = 'TRX' AND t.amount < 1) OR t.asset LIKE 'TRC10:%' OR (t.asset LIKE 'TRC20:%')
ORDER BY address, time_utc;

-- name: 5. Fan-in: how many addresses sweep to each main recipient
SELECT main_recipient, count(*) AS deposit_addresses, sum(usdt_out) AS usdt_swept
FROM usdt_profile GROUP BY 1 ORDER BY 2 DESC;
