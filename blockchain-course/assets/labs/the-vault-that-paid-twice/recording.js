/* Written by recording/record.py from the node's answers (dynamic-labs/explorer/chain/vault-recording/README.md). Do not edit by hand. */
var RECORDING = {
 "node": "anvil/v1.8.6",
 "drain": {
  "tx": "0xb17bc7915b2433be0e54a0803bbd832711e594d3f7a26453bfdb85350f8aab5a",
  "block": 4,
  "time": 1789999248,
  "from": "0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc",
  "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
  "eth": 1.0,
  "vault": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
  "caller": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
  "vaultBefore": 4.0,
  "vaultAfter": 0.0,
  "earlierDeposits": 4,
  "calls": [
   {
    "depth": 0,
    "type": "CALL",
    "from": "0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "run()",
    "input": "0xc0406226",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 1,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "deposit()",
    "input": "0xd0e30db0",
    "eth": 1.0,
    "logs": 1
   },
   {
    "depth": 1,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "withdraw()",
    "input": "0x3ccfd60b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 2,
    "type": "CALL",
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 3,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "withdraw()",
    "input": "0x3ccfd60b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 4,
    "type": "CALL",
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 5,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "withdraw()",
    "input": "0x3ccfd60b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 6,
    "type": "CALL",
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 7,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "withdraw()",
    "input": "0x3ccfd60b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 8,
    "type": "CALL",
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 9,
    "type": "CALL",
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "fn": "withdraw()",
    "input": "0x3ccfd60b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 10,
    "type": "CALL",
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   }
  ],
  "logs": [
   {
    "address": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "event": "Deposit",
    "account": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   }
  ],
  "internal": [
   {
    "from": "0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   },
   {
    "from": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "to": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "eth": 1.0
   },
   {
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   },
   {
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   },
   {
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   },
   {
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   },
   {
    "from": "0x5fbdb2315678afecb367f032d93f642f64180aa3",
    "to": "0x0116686e2291dbd5e317f47fadbfb43b599786ef",
    "eth": 1.0
   }
  ]
 },
 "twist": {
  "tx": "0xc05f43c194b4aca43b123e2083fe08c039acd063db8750fdbb9afdb466fa439e",
  "block": 8,
  "time": 1789999296,
  "from": "0x976ea74026e726554db657fa54763abd0c3a0aa9",
  "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
  "eth": 3.0,
  "vault": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
  "caller": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
  "vaultBefore": 4.0,
  "vaultAfter": 4.0,
  "earlierDeposits": 4,
  "calls": [
   {
    "depth": 0,
    "type": "CALL",
    "from": "0x976ea74026e726554db657fa54763abd0c3a0aa9",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "fn": "run()",
    "input": "0xc0406226",
    "eth": 3.0,
    "logs": 0
   },
   {
    "depth": 1,
    "type": "CALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "deposit()",
    "input": "0xd0e30db0",
    "eth": 3.0,
    "logs": 1
   },
   {
    "depth": 1,
    "type": "CALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "withdraw(uint256)",
    "input": "0x2e1a7d4d0000000000000000000000000000000000000000000000000de0b6b3a7640000",
    "eth": 0.0,
    "logs": 0,
    "amount": 1.0
   },
   {
    "depth": 2,
    "type": "CALL",
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 3,
    "type": "STATICCALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "balanceOf(address)",
    "input": "0x70a082310000000000000000000000007ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 3,
    "type": "CALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "withdraw(uint256)",
    "input": "0x2e1a7d4d0000000000000000000000000000000000000000000000000de0b6b3a7640000",
    "eth": 0.0,
    "logs": 0,
    "amount": 1.0
   },
   {
    "depth": 4,
    "type": "CALL",
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 5,
    "type": "STATICCALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "balanceOf(address)",
    "input": "0x70a082310000000000000000000000007ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 0.0,
    "logs": 0
   },
   {
    "depth": 5,
    "type": "CALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "withdraw(uint256)",
    "input": "0x2e1a7d4d0000000000000000000000000000000000000000000000000de0b6b3a7640000",
    "eth": 0.0,
    "logs": 0,
    "amount": 1.0
   },
   {
    "depth": 6,
    "type": "CALL",
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "fn": "",
    "input": "0x",
    "eth": 1.0,
    "logs": 0
   },
   {
    "depth": 7,
    "type": "STATICCALL",
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "fn": "balanceOf(address)",
    "input": "0x70a082310000000000000000000000007ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 0.0,
    "logs": 0
   }
  ],
  "logs": [
   {
    "address": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "event": "Deposit",
    "account": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 3.0
   }
  ],
  "internal": [
   {
    "from": "0x976ea74026e726554db657fa54763abd0c3a0aa9",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 3.0
   },
   {
    "from": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "to": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "eth": 3.0
   },
   {
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 1.0
   },
   {
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 1.0
   },
   {
    "from": "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",
    "to": "0x7ef8e99980da5bcedcf7c10f41e55f759f6a174b",
    "eth": 1.0
   }
  ]
 }
};
