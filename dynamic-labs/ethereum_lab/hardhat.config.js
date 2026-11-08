require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    // OpenZeppelin Contracts 5 needs Solidity 0.8.24 or later and the Cancun opcodes (mcopy), which the
    // Hardhat lab chain runs.
    version: "0.8.28",
    settings: {
      evmVersion: "cancun",
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    hardhat: {
      blockGasLimit: 300_000_000, // 300M - allows fillBotsAndStart with large pools
      // Local lab chain only: waive the 24KB EIP-170 contract-size limit so the
      // feature-rich BeaconChainLab (proposer/MEV/slashing/pivotal) can deploy.
      allowUnlimitedContractSize: true,
    },
    localhost: { url: "http://127.0.0.1:8545" },
    // For students: connects to instructor's node via RPC_URL env (set by Lab Terminal)
    instructor: { url: process.env.RPC_URL || process.env.INSTRUCTOR_RPC_URL || "http://127.0.0.1:8545" },
  },
};
