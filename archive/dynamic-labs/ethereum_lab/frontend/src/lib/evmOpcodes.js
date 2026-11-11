/**
 * EVM opcode map for bytecode disassembly.
 * Maps byte (0x00-0xff) to mnemonic. PUSH1-PUSH32 consume additional bytes.
 * @see https://www.evm.codes/
 */
const OPCODES = {
  0x00: 'STOP',
  0x01: 'ADD',
  0x02: 'MUL',
  0x03: 'SUB',
  0x04: 'DIV',
  0x05: 'SDIV',
  0x06: 'MOD',
  0x07: 'SMOD',
  0x08: 'ADDMOD',
  0x09: 'MULMOD',
  0x0a: 'EXP',
  0x0b: 'SIGNEXTEND',
  0x0c: 'INVALID',
  0x0d: 'INVALID',
  0x0e: 'INVALID',
  0x0f: 'INVALID',
  0x10: 'LT',
  0x11: 'GT',
  0x12: 'SLT',
  0x13: 'SGT',
  0x14: 'EQ',
  0x15: 'ISZERO',
  0x16: 'AND',
  0x17: 'OR',
  0x18: 'XOR',
  0x19: 'NOT',
  0x1a: 'BYTE',
  0x1b: 'SHL',
  0x1c: 'SHR',
  0x1d: 'SAR',
  0x1e: 'INVALID',
  0x1f: 'INVALID',
  0x20: 'KECCAK256',
  0x21: 'INVALID',
  0x22: 'INVALID',
  0x23: 'INVALID',
  0x24: 'INVALID',
  0x25: 'INVALID',
  0x26: 'INVALID',
  0x27: 'INVALID',
  0x28: 'INVALID',
  0x29: 'INVALID',
  0x2a: 'INVALID',
  0x2b: 'INVALID',
  0x2c: 'INVALID',
  0x2d: 'INVALID',
  0x2e: 'INVALID',
  0x2f: 'INVALID',
  0x30: 'ADDRESS',
  0x31: 'BALANCE',
  0x32: 'ORIGIN',
  0x33: 'CALLER',
  0x34: 'CALLVALUE',
  0x35: 'CALLDATALOAD',
  0x36: 'CALLDATASIZE',
  0x37: 'CALLDATACOPY',
  0x38: 'CODESIZE',
  0x39: 'CODECOPY',
  0x3a: 'GASPRICE',
  0x3b: 'EXTCODESIZE',
  0x3c: 'EXTCODECOPY',
  0x3d: 'RETURNDATASIZE',
  0x3e: 'RETURNDATACOPY',
  0x3f: 'EXTCODEHASH',
  0x40: 'BLOCKHASH',
  0x41: 'COINBASE',
  0x42: 'TIMESTAMP',
  0x43: 'NUMBER',
  0x44: 'PREVRANDAO',
  0x45: 'GASLIMIT',
  0x46: 'CHAINID',
  0x47: 'SELFBALANCE',
  0x48: 'BASEFEE',
  0x49: 'INVALID',
  0x4a: 'INVALID',
  0x4b: 'INVALID',
  0x4c: 'INVALID',
  0x4d: 'INVALID',
  0x4e: 'INVALID',
  0x4f: 'INVALID',
  0x50: 'POP',
  0x51: 'MLOAD',
  0x52: 'MSTORE',
  0x53: 'MSTORE8',
  0x54: 'SLOAD',
  0x55: 'SSTORE',
  0x56: 'JUMP',
  0x57: 'JUMPI',
  0x58: 'PC',
  0x59: 'MSIZE',
  0x5a: 'GAS',
  0x5b: 'JUMPDEST',
  0x5c: 'INVALID',
  0x5d: 'INVALID',
  0x5e: 'INVALID',
  0x5f: 'PUSH0',
};
// PUSH1-PUSH32: 0x60-0x7f
for (let i = 0x60; i <= 0x7f; i++) {
  OPCODES[i] = 'PUSH' + (i - 0x5f);
}
// DUP1-DUP16: 0x80-0x8f
for (let i = 0x80; i <= 0x8f; i++) {
  OPCODES[i] = 'DUP' + (i - 0x7f);
}
// SWAP1-SWAP16: 0x90-0x9f
for (let i = 0x90; i <= 0x9f; i++) {
  OPCODES[i] = 'SWAP' + (i - 0x8f);
}
// LOG0-LOG4: 0xa0-0xa4
OPCODES[0xa0] = 'LOG0';
OPCODES[0xa1] = 'LOG1';
OPCODES[0xa2] = 'LOG2';
OPCODES[0xa3] = 'LOG3';
OPCODES[0xa4] = 'LOG4';
// 0xa5-0xaf
for (let i = 0xa5; i <= 0xaf; i++) OPCODES[i] = 'INVALID';
// 0xb0-0xbf
OPCODES[0xb0] = 'INVALID';
OPCODES[0xb1] = 'INVALID';
OPCODES[0xb2] = 'INVALID';
OPCODES[0xb3] = 'INVALID';
OPCODES[0xb4] = 'INVALID';
OPCODES[0xb5] = 'INVALID';
OPCODES[0xb6] = 'INVALID';
OPCODES[0xb7] = 'INVALID';
OPCODES[0xb8] = 'INVALID';
OPCODES[0xb9] = 'INVALID';
OPCODES[0xba] = 'INVALID';
OPCODES[0xbb] = 'INVALID';
OPCODES[0xbc] = 'INVALID';
OPCODES[0xbd] = 'INVALID';
OPCODES[0xbe] = 'INVALID';
OPCODES[0xbf] = 'INVALID';
// 0xc0-0xcf
OPCODES[0xc0] = 'INVALID';
OPCODES[0xc1] = 'INVALID';
OPCODES[0xc2] = 'INVALID';
OPCODES[0xc3] = 'INVALID';
OPCODES[0xc4] = 'INVALID';
OPCODES[0xc5] = 'INVALID';
OPCODES[0xc6] = 'INVALID';
OPCODES[0xc7] = 'INVALID';
OPCODES[0xc8] = 'INVALID';
OPCODES[0xc9] = 'INVALID';
OPCODES[0xca] = 'INVALID';
OPCODES[0xcb] = 'INVALID';
OPCODES[0xcc] = 'INVALID';
OPCODES[0xcd] = 'INVALID';
OPCODES[0xce] = 'INVALID';
OPCODES[0xcf] = 'INVALID';
// 0xd0-0xdf
OPCODES[0xd0] = 'INVALID';
OPCODES[0xd1] = 'INVALID';
OPCODES[0xd2] = 'INVALID';
OPCODES[0xd3] = 'INVALID';
OPCODES[0xd4] = 'INVALID';
OPCODES[0xd5] = 'INVALID';
OPCODES[0xd6] = 'INVALID';
OPCODES[0xd7] = 'INVALID';
OPCODES[0xd8] = 'INVALID';
OPCODES[0xd9] = 'INVALID';
OPCODES[0xda] = 'INVALID';
OPCODES[0xdb] = 'INVALID';
OPCODES[0xdc] = 'INVALID';
OPCODES[0xdd] = 'INVALID';
OPCODES[0xde] = 'INVALID';
OPCODES[0xdf] = 'INVALID';
// 0xe0-0xef
OPCODES[0xe0] = 'INVALID';
OPCODES[0xe1] = 'INVALID';
OPCODES[0xe2] = 'INVALID';
OPCODES[0xe3] = 'INVALID';
OPCODES[0xe4] = 'INVALID';
OPCODES[0xe5] = 'INVALID';
OPCODES[0xe6] = 'INVALID';
OPCODES[0xe7] = 'INVALID';
OPCODES[0xe8] = 'INVALID';
OPCODES[0xe9] = 'INVALID';
OPCODES[0xea] = 'INVALID';
OPCODES[0xeb] = 'INVALID';
OPCODES[0xec] = 'INVALID';
OPCODES[0xed] = 'INVALID';
OPCODES[0xee] = 'INVALID';
OPCODES[0xef] = 'INVALID';
// 0xf0-0xff
OPCODES[0xf0] = 'CREATE';
OPCODES[0xf1] = 'CALL';
OPCODES[0xf2] = 'CALLCODE';
OPCODES[0xf3] = 'RETURN';
OPCODES[0xf4] = 'DELEGATECALL';
OPCODES[0xf5] = 'CREATE2';
OPCODES[0xfa] = 'STATICCALL';
OPCODES[0xfd] = 'REVERT';
OPCODES[0xfe] = 'INVALID';
OPCODES[0xff] = 'SELFDESTRUCT';
for (let i = 0xf6; i <= 0xf9; i++) OPCODES[i] = 'INVALID';
for (let i = 0xfb; i <= 0xfc; i++) OPCODES[i] = 'INVALID';

/**
 * Disassemble EVM bytecode into opcodes.
 * @param {string} hexBytecode - Hex string (with or without 0x prefix)
 * @returns {Array<{offset: number, byte: number, mnemonic: string, immediate?: string}>}
 */
export function disassemble(hexBytecode) {
  const hex = hexBytecode.startsWith('0x') ? hexBytecode.slice(2) : hexBytecode;
  const bytes = [];
  for (let i = 0; i < hex.length; i += 2) {
    bytes.push(parseInt(hex.slice(i, i + 2), 16));
  }
  const result = [];
  let i = 0;
  while (i < bytes.length) {
    const offset = i;
    const byte = bytes[i];
    const mnemonic = OPCODES[byte] ?? 'INVALID';
    let immediate;
    if (byte === 0x5f) {
      immediate = '0x';
    } else if (byte >= 0x60 && byte <= 0x7f) {
      const pushLen = byte - 0x5f;
      const immBytes = bytes.slice(i + 1, i + 1 + pushLen);
      immediate = '0x' + immBytes.map((b) => b.toString(16).padStart(2, '0')).join('');
      i += pushLen;
    }
    result.push({ offset, byte, mnemonic, immediate });
    i++;
  }
  return result;
}

/**
 * Format disassembled output as text (e.g. "0x0000: 60 PUSH1 0x80").
 * @param {Array} ops - Output from disassemble()
 * @returns {string}
 */
export function formatDisassembly(ops) {
  return ops
    .map((op) => {
      const addr = '0x' + op.offset.toString(16).padStart(4, '0');
      const hex = op.byte.toString(16).padStart(2, '0');
      const imm = op.immediate ? ' ' + op.immediate : '';
      return `${addr}: ${hex} ${op.mnemonic}${imm}`;
    })
    .join('\n');
}
