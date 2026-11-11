-- Find the exchange (day 5 game): ready-made queries over ../snapshot/find, for DuckDB.
-- Design card: docs/lab-cards/find-the-exchange.md. The suspect is made up for the game; the addresses and transfers
-- are real, read from Tron for 25 Sep to 17 Oct 2023, plus one hour of the hot wallet's incoming USDT on 10 Oct 2023.
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

-- What a published source says about an address, with the date that source was updated.
CREATE OR REPLACE VIEW labels AS
SELECT address, string_agg(label || ' [' || source || ', updated ' || strftime(as_of, '%d %b %Y') || ']', '; ' ORDER BY source) AS label
FROM read_csv('labels.csv', header = true, columns = {
  'address': 'VARCHAR', 'label': 'VARCHAR', 'source': 'VARCHAR', 'as_of': 'DATE'})
GROUP BY address;

-- The four addresses the suspect paid, and the suspect's own address.
CREATE OR REPLACE VIEW game AS
SELECT * FROM (VALUES ('A', 'TJnkMwcXJWNKcH3oCBtVExmhWuCsUyZmwm'), ('B', 'TL8m2AvfXKx8aLeepKQvTUfPkb3mDvW4WJ'),
                      ('C', 'TLPCbtGepn9rVDqMor9Soh3ScAffEbfo38'), ('D', 'TNmgHJ1kkMgegpGMdC1SUhWTSi23UqyuL7')) v(seat, address);
CREATE OR REPLACE VIEW suspect AS SELECT 'TLXNfyvjUjkeaK8hybWMBnVd2Lu9wtNdoh' AS address;

-- Every USDT movement of the four, with the balance after it. The balance counts only the snapshot's window: an
-- address with older history held at least this much.
CREATE OR REPLACE VIEW moves AS
WITH m AS (
  SELECT g.seat, g.address, t.time_utc, t.block, t.seq, t.tx_id, t.energy_used, t.energy_fee_sun,
         CASE WHEN t.to_addr = g.address THEN t.amount ELSE -t.amount END AS signed,
         CASE WHEN t.to_addr = g.address THEN t.from_addr ELSE t.to_addr END AS counterparty
  FROM game g JOIN tr t ON g.address IN (t.from_addr, t.to_addr) AND t.asset = 'USDT')
SELECT *, sum(signed) OVER (PARTITION BY address ORDER BY block, seq) AS balance_after FROM m;

-- An outflow that leaves the address empty: the whole balance moved on at once.
CREATE OR REPLACE VIEW sweeps AS
SELECT seat, address, time_utc, block, tx_id, counterparty AS swept_to, -signed AS usdt, energy_used, energy_fee_sun
FROM moves WHERE signed < 0 AND balance_after = 0;

-- name: 1. The suspect's USDT payments to the four addresses
SELECT g.seat, t.to_addr AS paid_to, t.time_utc, t.amount AS usdt, t.tx_id
FROM tr t JOIN game g ON g.address = t.to_addr
WHERE t.asset = 'USDT' AND t.from_addr = (SELECT address FROM suspect)
ORDER BY g.seat, t.time_utc;

-- name: 2. What came in and what went out: every USDT movement of the four, with the balance after it
SELECT seat, address, time_utc,
       CASE WHEN signed > 0 THEN 'in'
            WHEN balance_after = 0 THEN 'out: empties the address'
            ELSE 'out: keeps a balance' END AS kind,
       counterparty, CASE WHEN counterparty = (SELECT address FROM suspect) THEN 'the suspect' ELSE '' END AS who,
       abs(signed) AS usdt, balance_after, tx_id
FROM moves ORDER BY seat, block, seq;

-- name: 3. Where each address's sweeps went, and what a published source says about that address
SELECT s.seat, s.address, s.swept_to, count(*) AS sweeps, sum(s.usdt) AS usdt_swept,
       min(s.time_utc) AS first_sweep, max(s.time_utc) AS last_sweep,
       coalesce(l.label, 'no published source names this address') AS what_a_source_says
FROM sweeps s LEFT JOIN labels l ON l.address = s.swept_to
GROUP BY s.seat, s.address, s.swept_to, l.label
ORDER BY s.seat;

-- name: 4. Who paid for each sweep: TRX or Energy sent to the address in the 30 minutes before
WITH paid AS (
  SELECT to_addr AS address, time_utc, from_addr AS payer,
         CASE asset WHEN 'ENERGY_DELEGATED' THEN 'lent Energy (staked TRX behind it)' ELSE 'sent TRX' END AS how,
         amount AS trx
  FROM tr WHERE asset IN ('ENERGY_DELEGATED', 'TRX') AND amount >= 1)
SELECT s.seat, s.address, s.time_utc AS sweep_time, s.usdt, s.energy_used,
       s.energy_fee_sun / 1e6 AS trx_burned_for_energy, p.payer, p.how, p.trx,
       date_diff('second', p.time_utc, s.time_utc) AS seconds_before_sweep
FROM sweeps s LEFT JOIN paid p
  ON p.address = s.address AND p.time_utc BETWEEN s.time_utc - INTERVAL 30 MINUTE AND s.time_utc
ORDER BY s.seat, s.time_utc;

-- name: 5. Every TRX transfer to the four, and who sent it
SELECT g.seat, t.to_addr AS address, t.time_utc, t.amount AS trx, t.from_addr AS sender,
       CASE WHEN t.from_addr = (SELECT address FROM suspect) THEN 'the suspect' ELSE '' END AS who
FROM tr t JOIN game g ON g.address = t.to_addr
WHERE t.asset = 'TRX'
ORDER BY g.seat, t.time_utc;

-- name: 6. The hot wallet's incoming USDT from 04:36 to 05:36 UTC on 10 Oct 2023: how many addresses swept into it
WITH hot AS (SELECT address FROM labels WHERE address = 'TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi'),
inbound AS (
  SELECT t.* FROM tr t JOIN hot h ON t.to_addr = h.address
  WHERE t.asset = 'USDT' AND t.time_utc >= TIMESTAMP '2023-10-10 04:36:00' AND t.time_utc < TIMESTAMP '2023-10-10 05:36:00')
SELECT count(*) AS transfers_in, count(DISTINCT from_addr) AS different_senders, sum(amount) AS usdt_in,
       min(time_utc) AS first, max(time_utc) AS last,
       count(*) FILTER (WHERE from_addr IN (SELECT address FROM game)) AS from_the_four
FROM inbound;

-- name: 7. The same hour, sender by sender (any of the four first): the hot wallet fits every customer who deposits there
SELECT t.from_addr AS sender, count(*) AS transfers, sum(t.amount) AS usdt, min(t.time_utc) AS first,
       coalesce('address ' || any_value(g.seat), '') AS one_of_the_four
FROM tr t LEFT JOIN game g ON g.address = t.from_addr
WHERE t.asset = 'USDT' AND t.to_addr = 'TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi'
  AND t.time_utc >= TIMESTAMP '2023-10-10 04:36:00' AND t.time_utc < TIMESTAMP '2023-10-10 05:36:00'
GROUP BY t.from_addr
ORDER BY any_value(g.seat) IS NULL, usdt DESC;
