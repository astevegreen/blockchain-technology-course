/**
 * Contract Lab - Build & Deploy Scenario Tests
 *
 * Validates that contracts deployable from the platform (Contract Lab templates
 * and student contracts) can be built, deployed, and used correctly.
 * Mirrors the flows users perform in the UI: deploy → connect → interact.
 *
 * Run: npm run test:contractlab
 *
 * Coverage:
 *   - SimpleStorage: deploy, set, get
 *   - CarSale: full purchase flow, refund flow, admin participant setup
 *   - RansomPayment: deploy, payRansom, setAttacker
 *   - MyContract: custom Write tab equivalent
 *   - CarBuyerRole, CarSellerRole: student role contracts with CarSale
 *   - Multi-contract: CarSale + RansomPayment in same session
 */
const { expect } = require("chai");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("Contract Lab - Build & Deploy Scenarios", function () {
  async function deployFixture() {
    const [admin, seller, buyer, mechanic, victim, attacker] = await ethers.getSigners();
    return { admin, seller, buyer, mechanic, victim, attacker };
  }

  // ==================== SimpleStorage (Template) ====================
  describe("SimpleStorage template", function () {
    it("should deploy and set/get value", async function () {
      const { admin } = await loadFixture(deployFixture);
      const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
      const c = await SimpleStorage.deploy();
      await c.waitForDeployment();
      expect(await c.owner()).to.equal(admin.address);
      expect(await c.get()).to.equal(0);
      await c.set(42);
      expect(await c.get()).to.equal(42);
      await c.set(100);
      expect(await c.get()).to.equal(100);
    });

    it("should allow any address to set (no access control)", async function () {
      const { admin, buyer } = await loadFixture(deployFixture);
      const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
      const c = await SimpleStorage.deploy();
      await c.waitForDeployment();
      await c.connect(buyer).set(99);
      expect(await c.get()).to.equal(99);
    });
  });

  // ==================== CarSale (Template - defective-vehicle escrow) ====================
  describe("CarSale template - full purchase flow", function () {
    it("should deploy with seller, buyer, mechanic", async function () {
      const { admin, seller, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const sale = await CarSale.deploy(seller.address, buyer.address, mechanic.address);
      await sale.waitForDeployment();
      expect(await sale.admin()).to.equal(admin.address);
      expect(await sale.seller()).to.equal(seller.address);
      expect(await sale.buyer()).to.equal(buyer.address);
      expect(await sale.mechanic()).to.equal(mechanic.address);
      expect(await sale.salePrice()).to.equal(ethers.parseEther("2"));
      expect(await sale.depositAmount()).to.equal(ethers.parseEther("1"));
      expect(await sale.currentState()).to.equal(0); // Listed
    });

    it("should complete full purchase: deposit → inspection → complete", async function () {
      const { admin, seller, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const sale = await CarSale.deploy(seller.address, buyer.address, mechanic.address);
      await sale.waitForDeployment();

      await sale.connect(buyer).payDeposit({ value: ethers.parseEther("1") });
      expect(await sale.currentState()).to.equal(1); // DepositPaid

      await sale.connect(buyer).requestInspection();
      expect(await sale.currentState()).to.equal(2); // InspectionRequested

      await sale.connect(mechanic).mechanicInspect(true);
      expect(await sale.currentState()).to.equal(3); // InspectionPassed

      const sellerBalBefore = await ethers.provider.getBalance(seller.address);
      await sale.connect(buyer).completePurchase({ value: ethers.parseEther("1") });
      expect(await sale.currentState()).to.equal(5); // Completed
      const sellerBalAfter = await ethers.provider.getBalance(seller.address);
      expect(sellerBalAfter - sellerBalBefore).to.equal(ethers.parseEther("2"));
    });

    it("should complete refund flow: deposit → inspection failed → refund", async function () {
      const { admin, seller, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const sale = await CarSale.deploy(seller.address, buyer.address, mechanic.address);
      await sale.waitForDeployment();

      await sale.connect(buyer).payDeposit({ value: ethers.parseEther("1") });
      await sale.connect(buyer).requestInspection();
      await sale.connect(mechanic).mechanicInspect(false);
      expect(await sale.currentState()).to.equal(4); // InspectionFailed

      const buyerBalBefore = await ethers.provider.getBalance(buyer.address);
      const tx = await sale.connect(buyer).requestRefund();
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      expect(await sale.currentState()).to.equal(6); // Refunded
      const buyerBalAfter = await ethers.provider.getBalance(buyer.address);
      expect(buyerBalAfter).to.equal(buyerBalBefore + ethers.parseEther("1") - gasUsed);
    });

    it("should allow admin to set participants before deposit", async function () {
      const { admin, seller, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const sale = await CarSale.deploy(admin.address, ethers.ZeroAddress, ethers.ZeroAddress);
      await sale.waitForDeployment();

      await sale.setSeller(seller.address);
      await sale.setBuyer(buyer.address);
      await sale.setMechanic(mechanic.address);
      expect(await sale.seller()).to.equal(seller.address);
      expect(await sale.buyer()).to.equal(buyer.address);
      expect(await sale.mechanic()).to.equal(mechanic.address);
    });

    it("should allow buyer to self-assign when deployer uses ZeroAddress", async function () {
      const { admin, seller, mechanic } = await loadFixture(deployFixture);
      const [buyer] = await ethers.getSigners(3);
      const CarSale = await ethers.getContractFactory("CarSale");
      const sale = await CarSale.deploy(seller.address, ethers.ZeroAddress, mechanic.address);
      await sale.waitForDeployment();

      await sale.connect(buyer).payDeposit({ value: ethers.parseEther("1") });
      expect(await sale.buyer()).to.equal(buyer.address);
    });
  });

  // ==================== RansomPayment (Ransomware scenario) ====================
  describe("RansomPayment template", function () {
    it("should deploy with attacker address", async function () {
      const { admin, attacker } = await loadFixture(deployFixture);
      const RansomPayment = await ethers.getContractFactory("RansomPayment");
      const ransom = await RansomPayment.deploy(attacker.address);
      await ransom.waitForDeployment();
      expect(await ransom.admin()).to.equal(admin.address);
      expect(await ransom.attacker()).to.equal(attacker.address);
    });

    it("should forward ransom from victim to attacker", async function () {
      const { admin, victim, attacker } = await loadFixture(deployFixture);
      const RansomPayment = await ethers.getContractFactory("RansomPayment");
      const ransom = await RansomPayment.deploy(attacker.address);
      await ransom.waitForDeployment();

      const attackerBalBefore = await ethers.provider.getBalance(attacker.address);
      await ransom.connect(victim).payRansom({ value: ethers.parseEther("0.5") });
      const attackerBalAfter = await ethers.provider.getBalance(attacker.address);
      expect(attackerBalAfter - attackerBalBefore).to.equal(ethers.parseEther("0.5"));
    });

    it("should allow admin to setAttacker", async function () {
      const { admin, attacker, victim } = await loadFixture(deployFixture);
      const RansomPayment = await ethers.getContractFactory("RansomPayment");
      const ransom = await RansomPayment.deploy(attacker.address);
      await ransom.waitForDeployment();
      await ransom.setAttacker(victim.address);
      expect(await ransom.attacker()).to.equal(victim.address);
    });
  });

  // ==================== Custom contract (Write & Compile equivalent) ====================
  describe("Custom contract (MyContract - Write tab equivalent)", function () {
    it("should deploy and interact like Contract Lab Write tab", async function () {
      const { admin } = await loadFixture(deployFixture);
      const MyContract = await ethers.getContractFactory("MyContract");
      const c = await MyContract.deploy();
      await c.waitForDeployment();
      expect(await c.value()).to.equal(0);
      await c.set(123);
      expect(await c.value()).to.equal(123);
      expect(await c.get()).to.equal(123);
    });
  });

  // ==================== Student role contracts (CarBuyerRole, CarSellerRole, MechanicRole) ====================
  describe("Student role contracts with CarSale", function () {
    it("should complete CarSale flow using CarBuyerRole proxy", async function () {
      const { admin, seller, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const CarBuyerRole = await ethers.getContractFactory("CarBuyerRole");

      const sale = await CarSale.deploy(seller.address, ethers.ZeroAddress, mechanic.address);
      await sale.waitForDeployment();
      const buyerRole = await CarBuyerRole.connect(buyer).deploy(sale.target);
      await buyerRole.waitForDeployment();
      await sale.setBuyer(buyerRole.target);

      await buyer.sendTransaction({ to: buyerRole.target, value: ethers.parseEther("2") });
      await buyerRole.connect(buyer).payDeposit();
      await buyerRole.connect(buyer).requestInspection();
      await sale.connect(mechanic).mechanicInspect(true);
      await buyerRole.connect(buyer).completePurchase();
      expect(await sale.currentState()).to.equal(5);
    });

    it("should complete CarSale with CarSellerRole receiving proceeds", async function () {
      const { admin, buyer, mechanic } = await loadFixture(deployFixture);
      const CarSale = await ethers.getContractFactory("CarSale");
      const CarSellerRole = await ethers.getContractFactory("CarSellerRole");
      const CarBuyerRole = await ethers.getContractFactory("CarBuyerRole");

      const sellerRole = await CarSellerRole.connect(admin).deploy();
      await sellerRole.waitForDeployment();
      const sale = await CarSale.deploy(sellerRole.target, ethers.ZeroAddress, mechanic.address);
      await sale.waitForDeployment();
      const buyerRole = await CarBuyerRole.connect(buyer).deploy(sale.target);
      await buyerRole.waitForDeployment();
      await sale.setBuyer(buyerRole.target);

      await buyer.sendTransaction({ to: buyerRole.target, value: ethers.parseEther("2") });
      await buyerRole.connect(buyer).payDeposit();
      await buyerRole.connect(buyer).requestInspection();
      await sale.connect(mechanic).mechanicInspect(true);
      const sellerBalBefore = await ethers.provider.getBalance(sellerRole.target);
      await buyerRole.connect(buyer).completePurchase();
      const sellerBalAfter = await ethers.provider.getBalance(sellerRole.target);
      expect(sellerBalAfter - sellerBalBefore).to.equal(ethers.parseEther("2"));
    });
  });

  // ==================== Multi-contract scenario ====================
  describe("Complex scenario: CarSale + RansomPayment in same session", function () {
    it("should deploy both and run independent flows", async function () {
      const { admin, seller, buyer, mechanic, victim, attacker } = await loadFixture(deployFixture);

      const CarSale = await ethers.getContractFactory("CarSale");
      const RansomPayment = await ethers.getContractFactory("RansomPayment");

      const sale = await CarSale.deploy(seller.address, buyer.address, mechanic.address);
      await sale.waitForDeployment();
      const ransom = await RansomPayment.deploy(attacker.address);
      await ransom.waitForDeployment();

      await sale.connect(buyer).payDeposit({ value: ethers.parseEther("1") });
      await ransom.connect(victim).payRansom({ value: ethers.parseEther("0.1") });

      expect(await sale.currentState()).to.equal(1);
      expect(await ethers.provider.getBalance(attacker.address)).to.be.gte(ethers.parseEther("0.1"));
    });
  });
});
