-- Ready-made queries over the cross-chain extract, for DuckDB: the Bybit theft (Ethereum, through THORChain, to
-- Bitcoin; Feb 2025) and the Kelp DAO rsETH release (Unichain claimed, Ethereum, Arbitrum; Apr 2026).
-- Students would run these and read the output; they never edit them. Run from the extract's folder.
-- Each query starts with a "-- name:" line; run_queries.py prints them one by one.
-- The Parquet files are cryo's, with hashes and addresses as '0x...' text. Amounts are exact decimals, never floats.
-- Times are UTC, from each block's own timestamp; heads.csv says how far each chain was read (the "as of").
-- Column types are declared, not guessed: guessed, a time becomes a zoned timestamp shown in the viewer's local time.

-- An integer held as decimal digits, in whole units: units('1500000000000000000', 18) = 1.5.
CREATE OR REPLACE MACRO units(raw, d) AS CAST(
  CASE WHEN length(raw) > d THEN left(raw, length(raw) - d) ELSE '0' END || '.'
  || right(lpad(raw, greatest(length(raw), d)::INTEGER, '0'), d)
  AS DECIMAL(38, 18));
-- Event data is a run of 32-byte words; word(data, 0) is the first, as 64 hex digits.
CREATE OR REPLACE MACRO word(data, i) AS substr(data, 3 + 64 * i, 64);
-- A word read as an unsigned integer (every amount here fits in 128 bits), or as an address.
CREATE OR REPLACE MACRO uint(w) AS
  ('0x' || substr(w, 33, 16))::UBIGINT::HUGEINT * 18446744073709551616 + ('0x' || substr(w, 49, 16))::UBIGINT::HUGEINT;
CREATE OR REPLACE MACRO addr(w) AS '0x' || right(w, 40);
-- A Bitcoin OP_RETURN output's text: the bytes after the opcode and its push length.
CREATE OR REPLACE MACRO op_return_text(script) AS
  decode(unhex(CASE WHEN substr(script, 3, 2) = '4c' THEN substr(script, 7) ELSE substr(script, 5) END));

-- LayerZero's endpoint IDs for the three chains (LayerZero's deployed-contracts list).
CREATE OR REPLACE VIEW eids AS
SELECT * FROM (VALUES (30101, 'ethereum'), (30110, 'arbitrum'), (30320, 'unichain')) v(eid, chain);

CREATE OR REPLACE VIEW heads AS
SELECT * FROM read_csv('heads.csv', header = true, columns = {
  'chain': 'VARCHAR', 'head_block': 'BIGINT', 'head_time_utc': 'TIMESTAMP'});

CREATE OR REPLACE VIEW labels AS
SELECT * FROM read_csv('labels.csv', header = true, columns = {
  'chain': 'VARCHAR', 'address': 'VARCHAR', 'label': 'VARCHAR', 'source': 'VARCHAR'});

CREATE OR REPLACE VIEW steps AS
SELECT * FROM read_csv('steps.csv', header = true, columns = {
  'step_no': 'INTEGER', 'incident': 'VARCHAR', 'chain': 'VARCHAR', 'transaction_hash': 'VARCHAR', 'step': 'VARCHAR'});

CREATE OR REPLACE VIEW reads AS
SELECT * FROM read_csv('reads.csv', header = true, columns = {
  'incident': 'VARCHAR', 'chain': 'VARCHAR', 'contract_address': 'VARCHAR', 'call_data': 'VARCHAR',
  'signature': 'VARCHAR', 'what': 'VARCHAR'});

CREATE OR REPLACE VIEW blocks AS
SELECT chain, block_number::BIGINT AS block_number, make_timestamp(timestamp::BIGINT * 1000000) AS time_utc
FROM (SELECT 'ethereum' AS chain, * FROM 'ethereum_blocks.parquet'
      UNION ALL BY NAME SELECT 'arbitrum' AS chain, * FROM 'arbitrum_blocks.parquet'
      UNION ALL BY NAME SELECT 'unichain' AS chain, * FROM 'unichain_blocks.parquet');

-- Every transaction in the cases, with its step, its block's time, and its ETH value.
CREATE OR REPLACE VIEW tx AS
SELECT s.step_no, s.incident, s.step, t.chain, b.time_utc, b.block_number, t.transaction_hash, t.transaction_type,
       t.from_address, t.to_address, units(t.value_string, 18) AS eth, t.success, left(t.input, 10) AS selector
FROM (SELECT 'ethereum' AS chain, * FROM 'ethereum_transactions.parquet'
      UNION ALL BY NAME SELECT 'arbitrum' AS chain, * FROM 'arbitrum_transactions.parquet') t
JOIN steps s ON s.chain = t.chain AND s.transaction_hash = t.transaction_hash
JOIN blocks b ON b.chain = t.chain AND b.block_number = t.block_number;

CREATE OR REPLACE VIEW logs AS
SELECT t.step_no, t.incident, t.step, t.chain, t.time_utc, t.block_number, l.transaction_hash, l.log_index,
       l.address, l.topic0, l.topic1, l.topic2, l.topic3, l.data
FROM (SELECT 'ethereum' AS chain, * FROM 'ethereum_logs.parquet'
      UNION ALL BY NAME SELECT 'arbitrum' AS chain, * FROM 'arbitrum_logs.parquet') l
JOIN tx t ON t.chain = l.chain AND t.transaction_hash = l.transaction_hash;

-- Each token's name and decimals, as its own contract reports them (symbol() and decimals()).
CREATE OR REPLACE VIEW tokens AS
SELECT chain, contract_address AS token,
       max(CASE WHEN call_data = '0x95d89b41'
                THEN decode(unhex(substr(output_data, 3 + 128, 2 * uint(word(output_data, 1))::INTEGER))) END) AS symbol,
       max(CASE WHEN call_data = '0x313ce567' THEN uint(word(output_data, 0))::INTEGER END) AS decimals
FROM (SELECT 'ethereum' AS chain, * FROM 'ethereum_token_calls.parquet'
      UNION ALL BY NAME SELECT 'arbitrum' AS chain, * FROM 'arbitrum_token_calls.parquet')
GROUP BY ALL;

-- Every call in the cases, on both chains, in one shape. A call path is '' for the transaction's own call, then
-- '0', '0_1'... for the calls it makes. A call that reverted undoes every call beneath it, so those are flagged too.
CREATE OR REPLACE VIEW calls AS
WITH c AS (
  SELECT 'ethereum' AS chain, transaction_hash, trace_address AS call_path,
         CASE WHEN action_type = 'create' THEN 'create' ELSE action_call_type END AS call_type,
         action_from AS from_address, coalesce(action_to, result_address) AS to_address, action_value AS value_string,
         left(action_input, 10) AS selector, action_input AS input, error
  FROM 'ethereum_traces.parquet'
  UNION ALL
  SELECT 'arbitrum', transaction_hash, trace_address,
         CASE typ WHEN 'CALL' THEN 'call' WHEN 'DELEGATECALL' THEN 'delegate_call' WHEN 'STATICCALL' THEN 'static_call'
                  ELSE lower(typ) END,
         from_address, to_address, coalesce(value_string, '0'), left(input, 10), input, error
  FROM 'arbitrum_geth_calls.parquet')
SELECT c.*, EXISTS (
  SELECT 1 FROM c e WHERE e.chain = c.chain AND e.transaction_hash = c.transaction_hash AND e.error IS NOT NULL
    AND (e.call_path = '' OR c.call_path = e.call_path OR starts_with(c.call_path, e.call_path || '_'))) AS undone
FROM c;

-- Every movement of value that stuck: ETH (calls that carried value) and tokens (Transfer events). A delegate call
-- runs another contract's code in the caller's own account, so the value it shows is not a second payment.
CREATE OR REPLACE VIEW moves AS
SELECT t.step_no, t.incident, t.step, m.chain, t.time_utc, t.block_number, m.transaction_hash, m.pos, m.asset,
       m.from_address, coalesce(fl.label, CASE WHEN m.from_address = '0x' || repeat('0', 40) THEN '(none: new tokens)' END,
                                fk.symbol || ' token contract') AS from_label,
       m.to_address, coalesce(tl.label, CASE WHEN m.to_address = '0x' || repeat('0', 40) THEN '(none: tokens destroyed)' END,
                              tk.symbol || ' token contract') AS to_label, m.amount
FROM (
  SELECT chain, transaction_hash, row_number() OVER (PARTITION BY chain, transaction_hash ORDER BY call_path) AS pos,
         'ETH' AS asset, from_address, to_address, units(value_string, 18) AS amount
  FROM calls WHERE call_type IN ('call', 'create') AND value_string <> '0' AND NOT undone
  UNION ALL
  SELECT e.chain, e.transaction_hash, e.log_index, k.symbol, e.from_address, e.to_address,
         units(e.value_string, k.decimals)
  FROM (SELECT 'ethereum' AS chain, * FROM 'ethereum_erc20_transfers.parquet'
        UNION ALL BY NAME SELECT 'arbitrum' AS chain, * FROM 'arbitrum_erc20_transfers.parquet') e
  JOIN tokens k ON k.chain = e.chain AND k.token = e.erc20) m
JOIN tx t ON t.chain = m.chain AND t.transaction_hash = m.transaction_hash AND t.success
LEFT JOIN labels fl ON fl.chain = m.chain AND fl.address = m.from_address
LEFT JOIN labels tl ON tl.chain = m.chain AND tl.address = m.to_address
LEFT JOIN tokens fk ON fk.chain = m.chain AND fk.token = m.from_address
LEFT JOIN tokens tk ON tk.chain = m.chain AND tk.token = m.to_address;

-- THORChain Deposit events: the vault, the asset (0x0 is ETH), the amount, and the memo saying what to pay out where.
CREATE OR REPLACE VIEW thorchain_deposits AS
SELECT l.time_utc, l.block_number, l.transaction_hash, t.from_address AS depositor, addr(l.topic1) AS vault,
       CASE WHEN addr(l.topic2) = '0x0000000000000000000000000000000000000000' THEN 'ETH' ELSE addr(l.topic2) END AS asset,
       units(uint(word(l.data, 0))::VARCHAR, 18) AS amount,
       decode(unhex(substr(l.data, 3 + 64 * 3, 2 * uint(word(l.data, 2))::INTEGER))) AS memo
FROM logs l JOIN tx t ON t.chain = l.chain AND t.transaction_hash = l.transaction_hash
WHERE l.topic0 = '0xef519b7eb82aaf6ac376a6df2d793843ebfd593de5f1a0601d3cc6ab49ebb395';

CREATE OR REPLACE VIEW btc_tx AS
SELECT txid, block_height, make_timestamp(block_time * 1000000) AS time_utc, fee_sat
FROM 'bitcoin_transactions.parquet';

-- name: 1. Bybit: the code the cold wallet runs, before and after the takeover (its delegate calls)
SELECT t.time_utc, left(t.transaction_hash, 10) AS tx, t.step, c.call_path, c.to_address AS runs_code_of,
       l.label, c.selector
FROM calls c
JOIN tx t ON t.chain = c.chain AND t.transaction_hash = c.transaction_hash
LEFT JOIN labels l ON l.chain = c.chain AND l.address = c.to_address
WHERE t.incident = 'bybit' AND c.call_type = 'delegate_call'
  AND c.from_address = (SELECT address FROM labels WHERE label LIKE 'Bybit ETH cold wallet%')
ORDER BY t.block_number, t.transaction_hash, c.call_path;

-- name: 2. Bybit: what left the cold wallet
SELECT time_utc, left(transaction_hash, 10) AS tx, asset, amount, to_address, to_label
FROM moves
WHERE incident = 'bybit' AND from_address = (SELECT address FROM labels WHERE label LIKE 'Bybit ETH cold wallet%')
ORDER BY block_number, transaction_hash, pos;

-- name: 3. Bybit: the ETH receiver splits its ETH into tranches
SELECT time_utc, left(transaction_hash, 10) AS tx, from_label, to_address, to_label, amount AS eth
FROM moves WHERE step = 'a 10,000 ETH tranche from the sweep receiver' AND asset = 'ETH'
ORDER BY block_number, transaction_hash, pos;

-- name: 4. Bybit: pooling at the hub: who paid in, how often, how much
SELECT coalesce(m.from_label, s.kind) AS sender, m.from_address, count(*) AS payments, sum(m.amount) AS eth,
       min(m.time_utc) AS first_utc, max(m.time_utc) AS last_utc
FROM moves m
JOIN (SELECT transaction_hash, regexp_extract(step, 'from (an? .*)$', 1) AS kind FROM steps) s USING (transaction_hash)
WHERE m.step LIKE '%into the hub%' AND m.asset = 'ETH' AND m.to_label LIKE 'hub:%'
GROUP BY ALL ORDER BY eth DESC, sender, from_address;

-- name: 5. Bybit: address poisoning: each dust sender beside the address it imitates
WITH paid AS (
  SELECT to_address AS real, block_number AS paid_block, time_utc AS paid_utc, amount AS paid_eth
  FROM moves WHERE incident = 'bybit' AND from_label LIKE 'hub:%' AND asset = 'ETH'),
dust AS (
  SELECT from_address AS lookalike, block_number AS dust_block, time_utc AS dust_utc, eth AS dust_eth
  FROM tx WHERE step = 'dust into the hub from a lookalike address')
SELECT d.lookalike, p.real AS imitates, p.paid_utc, p.paid_eth, d.dust_utc, d.dust_eth,
       d.dust_block - p.paid_block AS blocks_later,
       d.lookalike IN (SELECT real FROM paid) AS hub_paid_the_lookalike
FROM dust d
LEFT JOIN paid p ON substr(p.real, 3, 4) = substr(d.lookalike, 3, 4) AND right(p.real, 4) = right(d.lookalike, 4)
                AND p.paid_block < d.dust_block
ORDER BY d.dust_block, d.lookalike, p.paid_block;

-- name: 6. Bybit: deposits to THORChain, and what each memo asks for
SELECT time_utc, left(transaction_hash, 10) AS tx, depositor, vault, asset, amount,
       split_part(memo, ':', 2) AS asks_for, split_part(memo, ':', 3) AS pay_to, memo
FROM thorchain_deposits ORDER BY block_number, transaction_hash;

-- name: 7. Bybit: THORChain pays out on Bitcoin, each payout naming the Ethereum deposit it answers
WITH outs AS (
  SELECT txid, op_return_text(script_hex) AS memo FROM 'bitcoin_outputs.parquet' WHERE script_type = 'op_return')
SELECT d.time_utc AS deposited_utc, left(d.transaction_hash, 10) AS eth_tx, d.amount AS eth_in,
       b.time_utc AS paid_utc, date_diff('minute', d.time_utc, b.time_utc) AS minutes_later,
       left(o.txid, 10) AS btc_tx, p.address AS paid_to, p.address = d.memo_pay_to AS as_the_memo_asked,
       units(p.value_sat::VARCHAR, 8) AS btc_out
FROM (SELECT *, split_part(memo, ':', 3) AS memo_pay_to FROM thorchain_deposits) d
JOIN outs o ON upper(o.memo) = 'OUT:' || upper(substr(d.transaction_hash, 3))
JOIN btc_tx b ON b.txid = o.txid
JOIN 'bitcoin_outputs.parquet' p ON p.txid = o.txid AND p.script_type <> 'op_return'
-- leave out the change the vault pays back to itself
WHERE p.address NOT IN (SELECT address FROM 'bitcoin_inputs.parquet' i WHERE i.txid = o.txid)
ORDER BY d.block_number, d.transaction_hash, p.vout;

-- name: 8. Bybit: the Bitcoin address the memos named, in sum, as of the Bitcoin head
WITH a AS (SELECT address FROM labels WHERE chain = 'bitcoin' AND label LIKE 'BTC address the deposit memos%'),
flows AS (
  SELECT txid, value_sat AS in_sat, 0 AS out_sat FROM 'bitcoin_outputs.parquet' WHERE address IN (FROM a)
  UNION ALL
  SELECT txid, 0, value_sat FROM 'bitcoin_inputs.parquet' WHERE address IN (FROM a)),
per_tx AS (SELECT txid, sum(in_sat) AS in_sat, sum(out_sat) AS out_sat FROM flows GROUP BY 1)
SELECT (FROM a) AS address, count(*) AS transactions, count(*) FILTER (in_sat > 0) AS paid_in,
       count(*) FILTER (out_sat > 0) AS paid_out, units(sum(in_sat)::VARCHAR, 8) AS btc_in,
       units(sum(out_sat)::VARCHAR, 8) AS btc_out, units((sum(in_sat) - sum(out_sat))::VARCHAR, 8) AS btc_held,
       min(b.time_utc) AS first_utc, max(b.time_utc) AS last_utc,
       any_value(h.head_block) AS as_of_block, any_value(h.head_time_utc) AS as_of_utc
FROM per_tx f JOIN btc_tx b USING (txid) CROSS JOIN (FROM heads WHERE chain = 'bitcoin') h;

-- name: 9. Kelp: the delivery that released rsETH: what it claimed, against what Unichain had sent
WITH d AS (
  SELECT time_utc, block_number, uint(word(data, 0)) AS src_eid, addr(word(data, 1)) AS sender,
         uint(word(data, 2)) AS nonce
  FROM logs
  WHERE topic0 = '0x3cd5e48f9730b129dc7550f0fcea9c767b7be37837cd10e55eb35f734f4bca04'
    AND step = 'a delivery claiming to come from Unichain releases rsETH'),
calls AS (
  SELECT 'ethereum' AS chain, * FROM 'ethereum_eth_calls.parquet'
  UNION ALL BY NAME SELECT 'unichain' AS chain, * FROM 'unichain_eth_calls.parquet')
SELECT 'ethereum' AS chain, d.block_number, d.time_utc,
       'the delivery says: from ' || e.chain || ' (endpoint ' || d.src_eid || '), sender ' || d.sender AS what,
       d.nonce AS nonce
FROM d JOIN eids e ON e.eid = d.src_eid
UNION ALL
SELECT c.chain, c.block_number, b.time_utc, r.what, uint(word(c.output_data, 0))
FROM calls c
JOIN reads r ON r.chain = c.chain AND r.contract_address = c.contract_address AND r.call_data = c.call_data
JOIN blocks b ON b.chain = c.chain AND b.block_number = c.block_number
ORDER BY time_utc, chain, what;

-- name: 10. Kelp: where the released rsETH went on Ethereum
SELECT time_utc, left(transaction_hash, 10) AS tx, step, from_address, from_label, to_address, to_label, amount
FROM moves
WHERE incident = 'kelp' AND chain = 'ethereum' AND asset = 'rsETH'
  AND (step LIKE 'a delivery claiming%' OR step LIKE 'split%')
ORDER BY block_number, transaction_hash, pos;

-- name: 11. Kelp: Aave on Ethereum: rsETH supplied, ETH borrowed, and where the ETH went
SELECT time_utc, left(transaction_hash, 10) AS tx, step, asset, amount, from_label, from_address, to_label, to_address
FROM moves
WHERE incident = 'kelp' AND chain = 'ethereum' AND (step LIKE 'Aave on Ethereum%' OR step LIKE 'the borrowed ETH%')
ORDER BY block_number, transaction_hash, pos;

-- name: 12. Kelp: across the LayerZero bridge: each rsETH send matched to its arrival by message id (guid)
-- OFTSent comes in two versions: Kelp's rsETH contracts emit the older one, with a single amount. A message can also
-- be cleared at the far end without running (LayerZero's clear()): it then arrives, but nothing is released.
WITH sent AS (
  SELECT l.topic1 AS guid, l.chain AS from_chain, l.time_utc AS sent_utc, l.transaction_hash AS sent_tx,
         t.from_address AS sent_by, uint(word(l.data, 0)) AS dst_eid, units(uint(word(l.data, 1))::VARCHAR, 18) AS rseth_sent
  FROM logs l JOIN tx t ON t.chain = l.chain AND t.transaction_hash = l.transaction_hash
  WHERE l.topic0 IN ('0xfff873bb909b73d08a8c1af4b21779e87103bb8ea8cf3b3a0067eb8526b8b80a',  -- 4 fields
                     '0x85496b760a4b7f8d66384b9df21b381f5d1b1e79f229a47aaf4c232edc2fe59a')), -- 5 fields
got AS (
  SELECT topic1 AS guid, chain AS to_chain, uint(word(data, 0)) AS src_eid, 'released' AS arrival,
         time_utc AS arrived_utc, transaction_hash AS arrival_tx, addr(topic2) AS receiver,
         units(uint(word(data, 1))::VARCHAR, 18) AS rseth_received
  FROM logs WHERE topic0 = '0xefed6d3500546b29533b128a29e3a94d70788727f0507505ac12eaf2e578fd9c'
  UNION ALL
  -- clear(oapp, (srcEid, sender, nonce), guid, message): the guid is the fifth word after the selector
  SELECT '0x' || substr(c.input, 11 + 64 * 4, 64), c.chain, uint(substr(c.input, 11 + 64, 64)), 'cleared: nothing released',
         t.time_utc, c.transaction_hash, NULL, NULL
  FROM calls c JOIN tx t ON t.chain = c.chain AND t.transaction_hash = c.transaction_hash
  WHERE c.selector = '0x2a56c1b0' AND NOT c.undone)
SELECT left(guid, 10) AS guid, coalesce(s.from_chain, (SELECT chain FROM eids WHERE eid = g.src_eid)) AS from_chain,
       coalesce(g.to_chain, (SELECT chain FROM eids WHERE eid = s.dst_eid)) AS to_chain,
       s.sent_utc, left(s.sent_tx, 10) AS sent_tx, s.sent_by, s.rseth_sent, coalesce(g.arrival, 'not in the extract') AS arrival,
       g.arrived_utc, left(g.arrival_tx, 10) AS arrival_tx, g.receiver, g.rseth_received,
       date_diff('second', s.sent_utc, g.arrived_utc) AS seconds_across
FROM sent s FULL JOIN got g USING (guid)
ORDER BY coalesce(s.sent_utc, g.arrived_utc), guid;

-- name: 13. Kelp: ETH in and out of the collecting address, on each chain (in these transactions only)
SELECT chain, CASE WHEN to_label LIKE 'collecting address%' THEN 'in' ELSE 'out' END AS direction,
       count(*) AS payments, sum(amount) AS eth, min(time_utc) AS first_utc, max(time_utc) AS last_utc
FROM moves
WHERE incident = 'kelp' AND asset = 'ETH' AND (to_label LIKE 'collecting address%' OR from_label LIKE 'collecting address%')
GROUP BY ALL ORDER BY chain, direction;

-- name: 14. Kelp: the freeze and the release on Arbitrum: who sent each transaction, and the ETH it moved
SELECT t.time_utc, t.block_number, left(t.transaction_hash, 10) AS tx, t.step, t.transaction_type, t.from_address,
       m.from_label, m.to_address, m.to_label, m.amount AS eth
FROM tx t LEFT JOIN moves m ON m.chain = t.chain AND m.transaction_hash = t.transaction_hash
WHERE t.step LIKE 'freeze%' OR t.step LIKE 'release%'
ORDER BY t.time_utc, t.transaction_hash, m.pos;

-- name: 15. Kelp: ETH held at each address on Arbitrum, block by block, read from the chain's own state
SELECT b.block_number, b.time_utc, l.label, x.address, units(x.balance_string, 18) AS eth
FROM 'arbitrum_balances.parquet' x
JOIN blocks b ON b.chain = 'arbitrum' AND b.block_number = x.block_number
LEFT JOIN labels l ON l.chain = 'arbitrum' AND l.address = x.address
ORDER BY b.block_number, l.label, x.address;

-- name: 16. As of: how far each chain was read
SELECT chain, head_block, head_time_utc FROM heads ORDER BY chain;
