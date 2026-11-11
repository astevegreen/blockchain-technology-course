import { network } from "hardhat";

const { ethers } = await network.getOrCreate();

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  const MyContract = await ethers.getContractFactory("MyContract");
  const contract = await MyContract.deploy();
  await contract.waitForDeployment();

  console.log("Deployed to:", contract.target);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});