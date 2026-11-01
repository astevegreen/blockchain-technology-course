-- Day 9 lab: ready-made queries over the day-9 part of the Tron snapshot (../snapshot/d9), for DuckDB.
-- Students run these on the query page and read the output; they never edit them.
-- Each query starts with a "-- name:" line; the query page shows them in this order.
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

-- What a published source says about an address, one line per address (labels.csv cites a source for each).
CREATE OR REPLACE VIEW labels AS
SELECT address, string_agg(label || ' [' || source || ']', '; ' ORDER BY source) AS label
FROM read_csv('labels.csv', header = true, columns = {
  'address': 'VARCHAR', 'label': 'VARCHAR', 'source': 'VARCHAR', 'as_of': 'DATE'})
GROUP BY address;

CREATE OR REPLACE VIEW freeze_status AS
SELECT * FROM read_csv('freeze.csv', header = true, columns = {
  'address': 'VARCHAR', 'usdt_blacklisted': 'BOOLEAN', 'usdt_balance': 'DECIMAL(38,6)', 'as_of_block': 'BIGINT',
  'as_of_time_utc': 'TIMESTAMP'});

CREATE OR REPLACE VIEW blacklist AS
SELECT * FROM read_csv('blacklist_events.csv', header = true, columns = {
  'time_utc': 'TIMESTAMP', 'block': 'BIGINT', 'event': 'VARCHAR', 'address': 'VARCHAR', 'destroyed_usdt': 'DECIMAL(38,2)',
  'signed_by': 'VARCHAR', 'tx_id': 'VARCHAR'});

-- The case: the deposit address OFAC listed for one Tren de Aragua designee.
CREATE OR REPLACE VIEW case_address AS SELECT 'TDxZ1XTZCmqkJJW2eJT362z6omRchJyGBX' AS address;

-- The USDT the case address held when the window opens on 1 Sep 2023, summed from its history since March 2022.
CREATE OR REPLACE VIEW opening AS
SELECT * FROM read_csv('opening_balance.csv', header = true, columns = {
  'address': 'VARCHAR', 'window_start_utc': 'TIMESTAMP', 'usdt': 'DECIMAL(38,6)', 'movements_before': 'INTEGER',
  'first_movement_utc': 'TIMESTAMP'});

-- Every USDT movement of the case address, with its balance after the movement.
CREATE OR REPLACE VIEW moves AS
WITH m AS (
  SELECT t.time_utc, t.block, t.seq, t.tx_id, t.signer,
         CASE WHEN t.to_addr = c.address THEN t.amount ELSE -t.amount END AS signed,
         CASE WHEN t.to_addr = c.address THEN t.from_addr ELSE t.to_addr END AS counterparty
  FROM tr t JOIN case_address c ON c.address IN (t.from_addr, t.to_addr) AND t.asset = 'USDT')
SELECT m.*, o.usdt + sum(m.signed) OVER (ORDER BY m.block, m.seq) AS balance_after
FROM m JOIN case_address c ON true JOIN opening o ON o.address = c.address;

-- An outflow that leaves the case address holding no USDT.
CREATE OR REPLACE VIEW sweeps AS
SELECT time_utc, block, tx_id, signer, counterparty AS swept_to, -signed AS usdt FROM moves
WHERE signed < 0 AND balance_after = 0;

-- name: 1. The case address in one row: what came in, from how many senders, what went out, and to how many places
SELECT c.address, count(*) FILTER (WHERE m.signed > 0) AS deposits,
       count(DISTINCT m.counterparty) FILTER (WHERE m.signed > 0) AS senders,
       sum(m.signed) FILTER (WHERE m.signed > 0) AS usdt_in,
       count(*) FILTER (WHERE m.signed < 0) AS outflows,
       count(DISTINCT m.counterparty) FILTER (WHERE m.signed < 0) AS recipients,
       -sum(m.signed) FILTER (WHERE m.signed < 0) AS usdt_out,
       min(m.time_utc) AS first_seen, max(m.time_utc) AS last_seen,
       coalesce(l.label, '') AS what_a_source_says
FROM case_address c JOIN moves m ON true LEFT JOIN labels l USING (address)
GROUP BY c.address, l.label;

-- name: 2. Deposits and sweeps: every USDT movement of the case address, with the running balance
SELECT time_utc,
       CASE WHEN signed > 0 THEN 'deposit'
            WHEN balance_after = 0 THEN 'sweep: empties the address'
            ELSE 'other outflow' END AS kind,
       counterparty, abs(signed) AS usdt, balance_after, signer AS signed_by, block, tx_id
FROM moves ORDER BY block, seq;

-- name: 3. Where the sweeps went, and what a published source says about each address
SELECT s.swept_to, count(*) AS sweeps, sum(s.usdt) AS usdt_swept,
       min(s.time_utc) AS first_sweep, max(s.time_utc) AS last_sweep,
       coalesce(l.label, 'no published source names this address') AS what_a_source_says
FROM sweeps s LEFT JOIN labels l ON l.address = s.swept_to
GROUP BY s.swept_to, l.label
ORDER BY first_sweep;

-- name: 4. Who paid for each sweep: the Energy it used, the TRX it burned, and TRX sent to the case address in the 30 minutes before
WITH paid AS (
  SELECT t.time_utc, t.from_addr AS payer, t.amount AS trx
  FROM tr t JOIN case_address c ON t.to_addr = c.address
  WHERE t.asset = 'TRX' AND t.amount >= 1)
SELECT s.time_utc AS sweep_time, s.swept_to, s.usdt, s.signer AS signed_by, t.energy_used,
       t.energy_fee_sun / 1e6 AS trx_burned_for_energy, p.payer, p.trx,
       date_diff('second', p.time_utc, s.time_utc) AS seconds_before_sweep
FROM sweeps s JOIN tx t USING (tx_id) LEFT JOIN paid p
  ON p.time_utc BETWEEN s.time_utc - INTERVAL 30 MINUTE AND s.time_utc
ORDER BY s.time_utc;

-- name: 5. Who paid in: each sender's deposits, and whether USDT's blacklist holds that sender today
SELECT m.counterparty AS sender, count(*) AS deposits, sum(m.signed) AS usdt,
       min(m.time_utc) AS first_deposit, max(m.time_utc) AS last_deposit,
       f.usdt_blacklisted, f.usdt_balance
FROM moves m LEFT JOIN freeze_status f ON f.address = m.counterparty
WHERE m.signed > 0
GROUP BY m.counterparty, f.usdt_blacklisted, f.usdt_balance
ORDER BY usdt DESC;

-- name: 6. Tether's freeze: the blacklist events of 30 Sep 2026, 16:14 UTC (USDT contract on Tron)
SELECT b.time_utc, b.block, b.event, b.address, b.signed_by, b.tx_id,
       coalesce(l.label, '') AS what_a_source_says
FROM blacklist b LEFT JOIN labels l USING (address)
ORDER BY b.block;

-- name: 7. Freeze status as of the snapshot: which addresses USDT's blacklist holds, and what each holds
SELECT f.address, f.usdt_blacklisted, f.usdt_balance, f.as_of_block, f.as_of_time_utc,
       coalesce(l.label, '') AS what_a_source_says
FROM freeze_status f LEFT JOIN labels l USING (address)
WHERE f.usdt_blacklisted
ORDER BY f.usdt_balance DESC, f.address;

-- name: 8. How fast: the window's last sweep, Tether's blacklisting of the case address, and what it held when read
SELECT s.last_sweep_in_window, b.time_utc AS blacklisted, date_diff('day', s.last_sweep_in_window, b.time_utc) AS days_between,
       f.usdt_blacklisted, f.usdt_balance AS usdt_held_when_read, f.as_of_time_utc AS read_at
FROM (SELECT max(time_utc) AS last_sweep_in_window FROM sweeps) s
CROSS JOIN case_address c
JOIN blacklist b ON b.address = c.address AND b.event = 'AddedBlackList'
JOIN freeze_status f ON f.address = c.address;

-- name: 9. Challenge: tokens nobody asked for, sent to the case address
SELECT t.time_utc, t.asset, t.amount, t.from_addr AS sender
FROM tr t JOIN case_address c ON t.to_addr = c.address
WHERE (t.asset = 'TRX' AND t.amount < 1) OR t.asset LIKE 'TRC10:%' OR t.asset LIKE 'TRC20:%'
ORDER BY t.time_utc;
