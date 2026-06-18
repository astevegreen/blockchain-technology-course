const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("LabNFT", function () {
  let nft, alice, bob;

  beforeEach(async () => {
    [, alice, bob] = await ethers.getSigners();
    nft = await ethers.deployContract("LabNFT", ["Test", "T"]);
    await nft.waitForDeployment();
  });

  it("enforces a five-token mint limit per recipient wallet", async () => {
    for (let i = 1; i <= 5; i += 1) {
      await (await nft.connect(alice).mint(alice.address, `ipfs://alice-${i}`)).wait();
    }

    expect(await nft.mintedCount(alice.address)).to.equal(5n);
    await expect(nft.connect(alice).mint(alice.address, "ipfs://alice-6"))
      .to.be.revertedWith("LabNFT: recipient mint limit reached");
  });

  it("enforces globally unique token URIs", async () => {
    await (await nft.connect(alice).mint(alice.address, "ipfs://shared-image")).wait();

    expect(await nft.tokenURIExists("ipfs://shared-image")).to.equal(true);
    await expect(nft.connect(bob).mint(bob.address, "ipfs://shared-image"))
      .to.be.revertedWith("LabNFT: token URI already minted");
  });

  it("rejects empty token URIs", async () => {
    await expect(nft.connect(alice).mint(alice.address, ""))
      .to.be.revertedWith("LabNFT: token URI required");
  });
});
