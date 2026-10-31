-- Day 5 lab: ready-made queries over the Tron snapshot (../snapshot), for DuckDB.
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

-- An address that both received and sent USDT in the snapshot, with the address it sends most to.
CREATE OR REPLACE VIEW usdt_profile AS
WITH ins AS (
  SELECT to_addr AS address, count(*) AS deposits, count(DISTINCT from_addr) AS senders, sum(amount) AS usdt_in
  FROM tr WHERE asset = 'USDT' GROUP BY 1),
outs AS (
  SELECT from_addr AS address, count(*) AS outflows, count(DISTINCT to_addr) AS recipients,
         sum(amount) AS usdt_out, mode(to_addr) AS main_recipient
  FROM tr WHERE asset = 'USDT' GROUP BY 1)
SELECT * FROM ins JOIN outs USING (address);

-- Each USDT outflow that sends the address's whole balance to its main recipient.
CREATE OR REPLACE VIEW sweeps AS
WITH moves AS (
  SELECT p.address, p.main_recipient, t.*,
         sum(CASE WHEN t.to_addr = p.address THEN t.amount ELSE -t.amount END)
           OVER (PARTITION BY p.address ORDER BY t.block, t.seq) AS balance_after
  FROM usdt_profile p JOIN tr t ON p.address IN (t.from_addr, t.to_addr) AND t.asset = 'USDT')
SELECT * FROM moves WHERE from_addr = address AND to_addr = main_recipient AND balance_after = 0;

-- name: 1. One USDT transfer: who sent it, who received it, how much, when, and what it cost
SELECT t.tx_id, t.block, t.time_utc, t.asset, t.from_addr, t.to_addr, t.amount, t.signer AS signed_by,
       t.type, t.energy_used, t.energy_fee_sun / 1e6 AS trx_burned_for_energy, t.fee_sun / 1e6 AS fee_trx
FROM tr t
WHERE t.tx_id = 'd11ff48c97d846c4a92a94ebdec4ce58bce04028e0c4c6c74d18236337d956bd';

-- name: 2. Deposits and sweeps: every USDT movement of the two deposit addresses, with the running balance
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
       counterparty, abs(signed) AS usdt, balance_after, block, tx_id
FROM bal ORDER BY address, block, seq;

-- name: 3. Where the sweeps went, and what a published source says about that address
SELECT s.address AS deposit_address, s.to_addr AS swept_to, count(*) AS sweeps, sum(s.amount) AS usdt_swept,
       min(s.time_utc) AS first_sweep, max(s.time_utc) AS last_sweep,
       coalesce(l.label, 'no published source names this address') AS what_a_source_says
FROM sweeps s LEFT JOIN labels l ON l.address = s.to_addr
GROUP BY s.address, s.to_addr, l.label
ORDER BY first_sweep;

-- name: 4. Who paid for each sweep: Energy lent to the address, or TRX sent to it, in the 30 minutes before
WITH paid AS (
  SELECT to_addr AS address, time_utc, from_addr AS payer,
         CASE asset WHEN 'ENERGY_DELEGATED' THEN 'lent Energy (staked TRX behind it)' ELSE 'sent TRX' END AS how,
         amount AS trx
  FROM tr WHERE asset IN ('ENERGY_DELEGATED', 'TRX') AND amount >= 1)
SELECT s.address, s.time_utc AS sweep_time, s.amount AS usdt, s.energy_used,
       s.energy_fee_sun / 1e6 AS trx_burned_for_energy, p.payer, p.how, p.trx,
       date_diff('second', p.time_utc, s.time_utc) AS seconds_before_sweep
FROM sweeps s LEFT JOIN paid p
  ON p.address = s.address AND p.time_utc BETWEEN s.time_utc - INTERVAL 30 MINUTE AND s.time_utc
ORDER BY s.address, s.time_utc;

-- name: 5. Tether's blacklist events on 23 Apr 2026 (USDT contract on Tron)
SELECT b.time_utc, b.block, b.event, b.address, b.signed_by, b.tx_id,
       coalesce(l.label, '') AS what_a_source_says
FROM blacklist b LEFT JOIN labels l USING (address)
ORDER BY b.block, b.address;

-- name: 6. Freeze status as of the snapshot: is the address on USDT's blacklist, and what it holds
SELECT f.address, f.usdt_blacklisted, f.usdt_balance, f.as_of_block, f.as_of_time_utc,
       coalesce(l.label, '') AS what_a_source_says
FROM freeze_status f LEFT JOIN labels l USING (address)
WHERE f.usdt_blacklisted
ORDER BY f.usdt_balance DESC;

-- name: 7. Challenge: tokens and dust nobody asked for, sent to the deposit addresses
SELECT t.to_addr AS address, t.time_utc, t.asset, t.amount, t.from_addr AS sender
FROM tr t JOIN usdt_profile p ON t.to_addr = p.address
WHERE (t.asset = 'TRX' AND t.amount < 1) OR t.asset LIKE 'TRC10:%' OR t.asset LIKE 'TRC20:%'
ORDER BY address, time_utc;
