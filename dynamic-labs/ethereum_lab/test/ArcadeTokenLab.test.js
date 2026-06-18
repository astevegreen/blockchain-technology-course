const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Arcade Token Lab", function () {
  let token, vendor, vault, owner, alice, treasury;
  const price = ethers.parseEther("50");
  const oneArc = ethers.parseEther("1");

  beforeEach(async () => {
    [owner, alice, treasury] = await ethers.getSigners();
    token = await ethers.deployContract("ArcadeToken");
    await token.waitForDeployment();

    vendor = await ethers.deployContract("TokenVendor", [await token.getAddress(), price, treasury.address]);
    await vendor.waitForDeployment();
    await (await token.setMinter(await vendor.getAddress())).wait();

    vault = await ethers.deployContract("ArcadeVault", [await token.getAddress()]);
    await vault.waitForDeployment();
  });

  it("sells exactly one ARC for the configured ETH price and forwards ETH to treasury", async () => {
    await expect(vendor.connect(alice).buyToken({ value: price }))
      .to.emit(vendor, "TokenPurchased")
      .withArgs(alice.address, price, oneArc, price)
      .and.to.emit(token, "Transfer")
      .withArgs(ethers.ZeroAddress, alice.address, oneArc);

    expect(await token.balanceOf(alice.address)).to.equal(oneArc);
    expect(await token.totalSupply()).to.equal(oneArc);
    expect(await ethers.provider.getBalance(await vendor.getAddress())).to.equal(0n);
  });

  it("rejects the wrong purchase price", async () => {
    await expect(vendor.connect(alice).buyToken({ value: ethers.parseEther("49") }))
      .to.be.revertedWith("TokenVendor: wrong ETH amount");
    await expect(vendor.connect(alice).buyToken({ value: ethers.parseEther("51") }))
      .to.be.revertedWith("TokenVendor: wrong ETH amount");
  });

  it("allows only the owner to update the ARC price", async () => {
    const nextPrice = ethers.parseEther("25");
    await expect(vendor.connect(alice).setTokenPriceWei(nextPrice))
      .to.be.revertedWith("Ownable: caller is not the owner");
    await expect(vendor.setTokenPriceWei(nextPrice))
      .to.emit(vendor, "TokenPriceUpdated")
      .withArgs(price, nextPrice, owner.address);
    await expect(vendor.connect(alice).buyToken({ value: price }))
      .to.be.revertedWith("TokenVendor: wrong ETH amount");
    await vendor.connect(alice).buyToken({ value: nextPrice });
    expect(await token.balanceOf(alice.address)).to.equal(oneArc);
  });

  it("burns one ARC to start a game session and increments nonce", async () => {
    await vendor.connect(alice).buyToken({ value: price });
    await token.connect(alice).approve(await vault.getAddress(), oneArc);

    await expect(vault.connect(alice).playGame(1))
      .to.emit(token, "Transfer")
      .withArgs(alice.address, ethers.ZeroAddress, oneArc)
      .and.to.emit(vault, "SessionStarted");

    expect(await token.balanceOf(alice.address)).to.equal(0n);
    expect(await token.totalSupply()).to.equal(0n);
    expect(await vault.sessionNonce(alice.address)).to.equal(1n);
  });

  it("requires allowance and balance before play", async () => {
    await expect(vault.connect(alice).playGame(1))
      .to.be.reverted;

    await vendor.connect(alice).buyToken({ value: price });
    await expect(vault.connect(alice).playGame(1))
      .to.be.reverted;
  });
});
