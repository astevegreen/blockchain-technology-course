const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
}

async function verifyCode(ethers, label, address) {
  const code = await ethers.provider.getCode(address);
  if (code === "0x") {
    throw new Error(`${label} deployment verification failed: bytecode missing at ${address}`);
  }
}

async function main() {
  const { ethers } = hre;
  const [deployer] = await ethers.getSigners();

  const entropyLotteryInitialPoolEth = "1000";
  const vulnerableBankPrefillEth = "500";
  const timelockRugVaultPrefillEth = "10";
  const timelockUnlockDelaySeconds = 0;
  const timelockWithdrawFeeBps = 500;

  const entropyLotteryInitialPoolWei = ethers.parseEther(entropyLotteryInitialPoolEth);
  const vulnerableBankPrefillWei = ethers.parseEther(vulnerableBankPrefillEth);
  const timelockRugVaultPrefillWei = ethers.parseEther(timelockRugVaultPrefillEth);

  console.log(`\nDeploying DeFi Risk Garden contracts with deployer: ${deployer.address}`);

  const entropyLottery = await ethers.deployContract("EntropyLottery", [], {
    value: entropyLotteryInitialPoolWei,
  });
  await entropyLottery.waitForDeployment();
  const entropyLotteryAddress = await entropyLottery.getAddress();

  const thousandEthDoubler = await ethers.deployContract("ThousandEthDoubler");
  await thousandEthDoubler.waitForDeployment();
  const thousandEthDoublerAddress = await thousandEthDoubler.getAddress();

  const vulnerableBankVault = await ethers.deployContract("VulnerableBankVault");
  await vulnerableBankVault.waitForDeployment();
  const vulnerableBankVaultAddress = await vulnerableBankVault.getAddress();

  const honeypotToken = await ethers.deployContract("HoneypotToken");
  await honeypotToken.waitForDeployment();
  const honeypotTokenAddress = await honeypotToken.getAddress();

  const approvalDrainer = await ethers.deployContract("ApprovalDrainer");
  await approvalDrainer.waitForDeployment();
  const approvalDrainerAddress = await approvalDrainer.getAddress();

  const fakeAirdropClaimer = await ethers.deployContract("FakeAirdropClaimer");
  await fakeAirdropClaimer.waitForDeployment();
  const fakeAirdropClaimerAddress = await fakeAirdropClaimer.getAddress();

  const timelockRugVault = await ethers.deployContract("TimelockRugVault", [
    timelockUnlockDelaySeconds,
    timelockWithdrawFeeBps,
    deployer.address,
  ]);
  await timelockRugVault.waitForDeployment();
  const timelockRugVaultAddress = await timelockRugVault.getAddress();

  await (
    await deployer.sendTransaction({
      to: vulnerableBankVaultAddress,
      value: vulnerableBankPrefillWei,
    })
  ).wait();

  await (
    await timelockRugVault.deposit({
      value: timelockRugVaultPrefillWei,
    })
  ).wait();

  await Promise.all([
    verifyCode(ethers, "EntropyLottery", entropyLotteryAddress),
    verifyCode(ethers, "ThousandEthDoubler", thousandEthDoublerAddress),
    verifyCode(ethers, "VulnerableBankVault", vulnerableBankVaultAddress),
    verifyCode(ethers, "HoneypotToken", honeypotTokenAddress),
    verifyCode(ethers, "ApprovalDrainer", approvalDrainerAddress),
    verifyCode(ethers, "FakeAirdropClaimer", fakeAirdropClaimerAddress),
    verifyCode(ethers, "TimelockRugVault", timelockRugVaultAddress),
  ]);

  const config = {
    entropyLotteryAddress,
    thousandEthDoublerAddress,
    vulnerableBankVaultAddress,
    honeypotTokenAddress,
    approvalDrainerAddress,
    fakeAirdropClaimerAddress,
    timelockRugVaultAddress,
    updatedAt: new Date().toISOString(),
    deployer: deployer.address,
    prefillAmounts: {
      entropyLotteryInitialPoolEth,
      entropyLotteryInitialPoolWei: entropyLotteryInitialPoolWei.toString(),
      vulnerableBankVaultEth: vulnerableBankPrefillEth,
      vulnerableBankVaultWei: vulnerableBankPrefillWei.toString(),
      timelockRugVaultEth: timelockRugVaultPrefillEth,
      timelockRugVaultWei: timelockRugVaultPrefillWei.toString(),
    },
    timelockRugVault: {
      unlockDelaySeconds: timelockUnlockDelaySeconds,
      withdrawFeeBps: timelockWithdrawFeeBps,
      treasury: deployer.address,
    },
  };

  const root = path.join(__dirname, "..");
  const publicPath = path.join(root, "frontend", "public", "labs", "ethereum_lab", "defi-risk-config.json");
  const distPath = path.join(root, "frontend", "dist", "labs", "ethereum_lab", "defi-risk-config.json");

  writeJson(publicPath, config);
  writeJson(distPath, config);

  console.log(`EntropyLottery deployed to: ${entropyLotteryAddress}`);
  console.log(`ThousandEthDoubler deployed to: ${thousandEthDoublerAddress}`);
  console.log(`VulnerableBankVault deployed to: ${vulnerableBankVaultAddress}`);
  console.log(`HoneypotToken deployed to: ${honeypotTokenAddress}`);
  console.log(`ApprovalDrainer deployed to: ${approvalDrainerAddress}`);
  console.log(`FakeAirdropClaimer deployed to: ${fakeAirdropClaimerAddress}`);
  console.log(`TimelockRugVault deployed to: ${timelockRugVaultAddress}`);
  console.log(`EntropyLottery funded with: ${entropyLotteryInitialPoolEth} ETH`);
  console.log(`VulnerableBankVault prefilled with: ${vulnerableBankPrefillEth} ETH`);
  console.log(`TimelockRugVault deployer deposit: ${timelockRugVaultPrefillEth} ETH`);
  console.log("DeFi risk config saved to frontend public and dist paths");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
