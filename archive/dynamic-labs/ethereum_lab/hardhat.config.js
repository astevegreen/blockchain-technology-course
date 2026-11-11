import { defineConfig, overrideTask } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";
import hardhatEthersChaiMatchers from "@nomicfoundation/hardhat-ethers-chai-matchers";
import hardhatMocha from "@nomicfoundation/hardhat-mocha";
import hardhatNetworkHelpers from "@nomicfoundation/hardhat-network-helpers";

// The lab chain's in-process network. Hardhat 3 runs tests on `default` and `hardhat node` on `node`;
// both get the settings Hardhat 2's `hardhat` network had.
const labChain = {
  type: "edr-simulated",
  chainType: "l1",
  blockGasLimit: 300_000_000, // 300M - allows fillBotsAndStart with large pools
  // Local lab chain only: waive the 24KB EIP-170 contract-size limit so the
  // feature-rich BeaconChainLab (proposer/MEV/slashing/pivotal) can deploy.
  allowUnlimitedContractSize: true,
};

export default defineConfig({
  plugins: [hardhatEthers, hardhatEthersChaiMatchers, hardhatMocha, hardhatNetworkHelpers],
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
    default: labChain,
    node: labChain,
    localhost: { type: "http", chainType: "l1", url: "http://127.0.0.1:8545" },
    // For students: connects to instructor's node via RPC_URL env (set by Lab Terminal)
    instructor: {
      type: "http",
      chainType: "l1",
      url: process.env.RPC_URL || process.env.INSTRUCTOR_RPC_URL || "http://127.0.0.1:8545",
    },
  },
  tasks: [
    // Hardhat 3's console no longer puts `ethers` in scope. The lab guides have students type
    // `await ethers.getSigners()` there, so connect to the --network chain first and expose its
    // ethers object; the REPL copies globals into its context.
    overrideTask("console")
      .setInlineAction(async (taskArguments, hre, runSuper) => {
        const { ethers } = await hre.network.getOrCreate();
        globalThis.ethers = ethers;
        return runSuper(taskArguments);
      })
      .build(),
  ],
});
