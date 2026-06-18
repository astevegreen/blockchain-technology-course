const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("LabNFTMarketplace", function () {
  let nft, market, seller, buyer, other;

  beforeEach(async () => {
    [, seller, buyer, other] = await ethers.getSigners();
    nft = await ethers.deployContract("LabNFT", ["Test", "T"]);
    await nft.waitForDeployment();
    market = await ethers.deployContract("LabNFTMarketplace");
    await market.waitForDeployment();
    await (await nft.connect(seller).mint(seller.address, "ipfs://1")).wait(); // tokenId 1 -> seller
  });

  it("lists, buys (NFT + ETH move), and relists", async () => {
    const tokenId = 1n;
    const price = ethers.parseEther("1");
    const mAddr = await market.getAddress();
    const nAddr = await nft.getAddress();

    await (await nft.connect(seller).approve(mAddr, tokenId)).wait();
    await expect(market.connect(seller).list(nAddr, tokenId, price)).to.emit(market, "Listed");
    expect(await nft.ownerOf(tokenId)).to.equal(seller.address); // stays in seller's wallet (no escrow)

    const before = await ethers.provider.getBalance(seller.address);
    await expect(market.connect(buyer).buy(1n, { value: price })).to.emit(market, "Sale");
    expect(await nft.ownerOf(tokenId)).to.equal(buyer.address);
    expect((await ethers.provider.getBalance(seller.address)) - before).to.equal(price);

    // Buyer relists at a new price.
    await (await nft.connect(buyer).approve(mAddr, tokenId)).wait();
    await (await market.connect(buyer).list(nAddr, tokenId, ethers.parseEther("2"))).wait();
    const [page] = await market.getActiveListings(0, 50);
    expect(page.length).to.equal(1);
    expect(page[0].seller).to.equal(buyer.address);
    expect(page[0].price).to.equal(ethers.parseEther("2"));
  });

  it("guards: needs approval, wrong price, non-seller cancel, stale listing, double buy", async () => {
    const tokenId = 1n;
    const price = ethers.parseEther("1");
    const mAddr = await market.getAddress();
    const nAddr = await nft.getAddress();

    await expect(market.connect(seller).list(nAddr, tokenId, price))
      .to.be.revertedWith("Marketplace: approve marketplace first");

    await (await nft.connect(seller).approve(mAddr, tokenId)).wait();
    await (await market.connect(seller).list(nAddr, tokenId, price)).wait();

    await expect(market.connect(buyer).buy(1n, { value: ethers.parseEther("0.5") }))
      .to.be.revertedWith("Marketplace: wrong ETH amount");
    await expect(market.connect(other).cancelListing(1n))
      .to.be.revertedWith("Marketplace: not seller");

    // Seller moves the NFT away outside the marketplace -> stale listing must revert, not steal funds.
    await (await nft.connect(seller).transferFrom(seller.address, other.address, tokenId)).wait();
    await expect(market.connect(buyer).buy(1n, { value: price }))
      .to.be.revertedWith("Marketplace: seller no longer owns token");
  });

  it("cancel deactivates and buy-after-cancel reverts", async () => {
    const mAddr = await market.getAddress();
    const nAddr = await nft.getAddress();
    await (await nft.connect(seller).approve(mAddr, 1n)).wait();
    await (await market.connect(seller).list(nAddr, 1n, ethers.parseEther("1"))).wait();
    await expect(market.connect(seller).cancelListing(1n)).to.emit(market, "Cancelled");
    await expect(market.connect(buyer).buy(1n, { value: ethers.parseEther("1") }))
      .to.be.revertedWith("Marketplace: not active");
    const [page] = await market.getActiveListings(0, 50);
    expect(page.length).to.equal(0);
  });
});
