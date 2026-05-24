require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    hardhat: {
      blockGasLimit: 300_000_000, // 300M - allows fillBotsAndStart with large pools
    },
    localhost: { url: "http://127.0.0.1:8545" },
    // For students: connects to instructor's node via RPC_URL env (set by Lab Terminal)
    instructor: { url: process.env.RPC_URL || process.env.INSTRUCTOR_RPC_URL || "http://127.0.0.1:8545" },
  },
};
