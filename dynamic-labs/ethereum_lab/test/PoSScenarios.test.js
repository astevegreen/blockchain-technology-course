/**
 * PoS Simulator - Scenario Tests
 *
 * Each test maps to a UI button/action and validates the underlying contract behavior.
 * Uses multiple signers (instructor, v1, v2, v3, v4) to simulate different users and scenarios.
 *
 * UI → Contract mapping:
 *   Stake ETH          → stake()
 *   Request Withdrawal → requestWithdrawal()
 *   Withdraw           → withdraw()
 *   Cancel Withdrawal  → cancelWithdrawal()
 *   Attest to Block    → attest() / attest(uint256)
 *   Propose Block      → proposeBlock() [instructor]
 *   Slash              → slash(validator, reason) [instructor]
 *   Check Missed Att.  → checkMissedAttestations() [instructor]
 *   Set Role           → setRole(), setRolesBatch(), setRolePool() [instructor]
 *   Register Contract  → registerRoleContract()
 *   Send Message       → sendMessage()
 */
const { expect } = require("chai");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("PoS Simulator - UI Action Scenarios", function () {
  async function deployFixture() {
    const [instructor, v1, v2, v3, v4] = await ethers.getSigners();
    const PoS = await ethers.getContractFactory("PoSSimulator");
    const pos = await PoS.deploy();
    await pos.waitForDeployment();
    await instructor.sendTransaction({ to: pos.target, value: ethers.parseEther("200") });
    return { pos, instructor, v1, v2, v3, v4 };
  }

  // ==================== STAKE (Student: "Stake ETH" button) ====================
  describe("Stake", function () {
    it("should allow validator to stake 32 ETH", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      expect(await pos.stakes(v1.address)).to.equal(ethers.parseEther("32"));
      expect(await pos.totalStaked()).to.equal(ethers.parseEther("32"));
      expect(await pos.getValidatorCount()).to.equal(1);
    });

    it("should allow multiple validators to stake", async function () {
      const { pos, v1, v2, v3 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.connect(v2).stake({ value: ethers.parseEther("64") });
      await pos.connect(v3).stake({ value: ethers.parseEther("32") });
      expect(await pos.totalStaked()).to.equal(ethers.parseEther("128"));
      expect(await pos.getValidatorCount()).to.equal(3);
    });

    it("should revert when stake below minimum", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await expect(pos.connect(v1).stake({ value: ethers.parseEther("31") }))
        .to.be.revertedWith("Minimum stake is 32 ETH");
    });

    it("should revert when already a validator", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await expect(pos.connect(v1).stake({ value: ethers.parseEther("32") }))
        .to.be.revertedWith("Already a validator - withdraw first");
    });
  });

  // ==================== PROPOSE BLOCK (Instructor: "Propose Block" button) ====================
  describe("Propose Block", function () {
    it("should allow instructor to propose block when no validators", async function () {
      const { pos, instructor } = await loadFixture(deployFixture);
      const tx = await pos.proposeBlock();
      const receipt = await tx.wait();
      expect(await pos.lastProposedBlockNumber()).to.be.gt(0);
      const event = receipt.logs.find((l) => {
        try {
          const parsed = pos.interface.parseLog({ topics: l.topics, data: l.data });
          return parsed?.name === "BlockProposed";
        } catch { return false; }
      });
      expect(event).to.not.be.undefined;
    });

    it("should select validator when validators exist (stake-weighted)", async function () {
      const { pos, instructor, v1, v2 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("64") });
      await pos.connect(v2).stake({ value: ethers.parseEther("32") });
      await pos.proposeBlock();
      const lastBlock = await pos.lastProposedBlockNumber();
      expect(lastBlock).to.be.gt(0);
      const count = await pos.getValidatorCount();
      expect(count).to.equal(2);
    });

    it("should revert when non-instructor proposes", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await expect(pos.connect(v1).proposeBlock()).to.be.revertedWith("Only instructor can call this");
    });
  });

  // ==================== ATTEST (Student: "Attest to Block" button) ====================
  describe("Attest", function () {
    it("should allow validator to attest after block proposed", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.proposeBlock();
      const blockNum = await pos.lastProposedBlockNumber();
      await pos.connect(v1).getFunction("attest(uint256)")(blockNum);
      expect(await pos.hasAttestedThisEpoch(v1.address)).to.be.true;
    });

    it("should revert when no block proposed yet", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await expect(pos.connect(v1).getFunction("attest()")()).to.be.revertedWith("No block proposed yet - wait for next block");
    });

    it("should revert when non-validator attests", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.proposeBlock();
      await expect(pos.connect(v1).getFunction("attest()")()).to.be.revertedWith("Not a validator");
    });

    it("should revert when double attest same epoch", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.proposeBlock();
      await pos.connect(v1).getFunction("attest()")();
      await expect(pos.connect(v1).getFunction("attest()")()).to.be.revertedWith("Already attested this epoch");
    });

    it("should allow multiple validators to attest", async function () {
      const { pos, instructor, v1, v2, v3 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.connect(v2).stake({ value: ethers.parseEther("32") });
      await pos.connect(v3).stake({ value: ethers.parseEther("32") });
      await pos.proposeBlock();
      await pos.connect(v1).getFunction("attest()")();
      await pos.connect(v2).getFunction("attest()")();
      await pos.connect(v3).getFunction("attest()")();
      expect(await pos.hasAttestedThisEpoch(v1.address)).to.be.true;
      expect(await pos.hasAttestedThisEpoch(v2.address)).to.be.true;
      expect(await pos.hasAttestedThisEpoch(v3.address)).to.be.true;
    });
  });

  // ==================== SLASH (Instructor: "Slash" button) ====================
  describe("Slash", function () {
    it("should allow instructor to slash validator", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("100") });
      await pos.slash(v1.address, "Double signing");
      const [stake] = await pos.getValidatorStats(v1.address);
      expect(stake).to.equal(ethers.parseEther("95"));
      expect(await pos.slashCount(v1.address)).to.equal(1);
    });

    it("should revert when non-instructor slashes", async function () {
      const { pos, v1, v2 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await expect(pos.connect(v2).slash(v1.address, "Fake")).to.be.revertedWith("Only instructor can call this");
    });

    it("should revert when slashing non-validator", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await expect(pos.slash(v1.address, "Not staked")).to.be.revertedWith("Address is not a validator");
    });
  });

  // ==================== ROLE ASSIGNMENT (Instructor: setRole, setRolesBatch, setRolePool) ====================
  describe("Role Assignment", function () {
    it("should allow instructor to setRole", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.setRole(v1.address, "Car Buyer");
      expect(await pos.roleAssignment(v1.address)).to.equal("Car Buyer");
    });

    it("should allow instructor to setRolesBatch", async function () {
      const { pos, instructor, v1, v2, v3 } = await loadFixture(deployFixture);
      await pos.setRolesBatch(
        [v1.address, v2.address, v3.address],
        ["Car Seller", "Car Buyer", "Mechanic"]
      );
      expect(await pos.roleAssignment(v1.address)).to.equal("Car Seller");
      expect(await pos.roleAssignment(v2.address)).to.equal("Car Buyer");
      expect(await pos.roleAssignment(v3.address)).to.equal("Mechanic");
    });

    it("should auto-assign role from pool on first stake", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.setRolePool(["Car Seller", "Car Buyer", "Mechanic"]);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      expect(await pos.roleAssignment(v1.address)).to.equal("Car Seller");
    });

    it("should auto-assign role from pool on first chat", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.setRolePool(["Victim", "Attacker", "Investigator"]);
      await pos.connect(v1).sendMessage("Hello");
      expect(await pos.roleAssignment(v1.address)).to.equal("Victim");
    });

    it("should allow validator to registerRoleContract", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.setRole(v1.address, "Car Buyer");
      const fakeContract = "0x0000000000000000000000000000000000000001";
      await pos.connect(v1).registerRoleContract(fakeContract);
      expect(await pos.roleContractAddress(v1.address)).to.equal(fakeContract);
    });

    it("should revert registerRoleContract when no role assigned", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await expect(pos.connect(v1).registerRoleContract(v1.address)).to.be.revertedWith("No role assigned");
    });
  });

  // ==================== CHAT (Student: sendMessage) ====================
  describe("Chat", function () {
    it("should emit NewMessage on sendMessage", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      const tx = await pos.connect(v1).sendMessage("Hello class!");
      const receipt = await tx.wait();
      const event = receipt.logs.find((l) => {
        try {
          const parsed = pos.interface.parseLog({ topics: l.topics, data: l.data });
          return parsed?.name === "NewMessage";
        } catch { return false; }
      });
      expect(event).to.not.be.undefined;
    });
  });

  // ==================== WITHDRAWAL FLOW (Student: Request Withdrawal -> Withdraw) ====================
  describe("Withdrawal", function () {
    it("should revert requestWithdrawal before min stake duration", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await expect(pos.connect(v1).requestWithdrawal()).to.be.revertedWith(
        "Must stake for minimum duration (30 seconds)"
      );
    });

    it("should allow requestWithdrawal after min duration", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await time.increase(31);
      await pos.connect(v1).requestWithdrawal();
      expect(await pos.withdrawalRequestTime(v1.address)).to.be.gt(0);
    });

    it("should revert withdraw before unbonding complete", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await time.increase(31);
      await pos.connect(v1).requestWithdrawal();
      await expect(pos.connect(v1).withdraw()).to.be.revertedWith(
        "Unbonding period not complete (60 seconds)"
      );
    });

    it("should allow full withdrawal after unbonding", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await time.increase(31);
      await pos.connect(v1).requestWithdrawal();
      await time.increase(61);
      await pos.connect(v1).withdraw();
      expect(await pos.stakes(v1.address)).to.equal(0);
      expect(await pos.getValidatorCount()).to.equal(0);
    });

    it("should allow cancelWithdrawal", async function () {
      const { pos, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await time.increase(31);
      await pos.connect(v1).requestWithdrawal();
      await pos.connect(v1).cancelWithdrawal();
      expect(await pos.withdrawalRequestTime(v1.address)).to.equal(0);
    });
  });

  // ==================== EPOCH ADVANCE ====================
  describe("Epoch Advance", function () {
    it("should advance epoch when time elapsed", async function () {
      const { pos } = await loadFixture(deployFixture);
      expect(await pos.currentEpoch()).to.equal(1);
      await time.increase(31);
      await pos.advanceEpoch();
      expect(await pos.currentEpoch()).to.equal(2);
    });

    it("should revert advanceEpoch when time not elapsed", async function () {
      const { pos } = await loadFixture(deployFixture);
      await expect(pos.advanceEpoch()).to.be.revertedWith("Epoch duration not elapsed (30 seconds)");
    });
  });

  // ==================== CHECK MISSED ATTESTATIONS (Instructor) ====================
  describe("Check Missed Attestations", function () {
    it("should penalize validator who missed attestation", async function () {
      const { pos, instructor, v1, v2 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("100") });
      await pos.connect(v2).stake({ value: ethers.parseEther("100") });
      await pos.proposeBlock();
      await pos.connect(v1).getFunction("attest()")();
      await time.increase(31);
      await pos.checkMissedAttestations();
      const [stakeV2] = await pos.getValidatorStats(v2.address);
      expect(stakeV2).to.be.lt(ethers.parseEther("100"));
      expect(await pos.missedAttestations(v2.address)).to.equal(1);
    });
  });

  // ==================== MULTI-USER SCENARIOS ====================
  describe("Multi-User Scenarios", function () {
    it("scenario: 3 validators stake, propose, all attest, one slashed", async function () {
      const { pos, instructor, v1, v2, v3 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("64") });
      await pos.connect(v2).stake({ value: ethers.parseEther("96") });
      await pos.connect(v3).stake({ value: ethers.parseEther("32") });
      expect(await pos.getValidatorCount()).to.equal(3);
      await pos.proposeBlock();
      await pos.connect(v1).getFunction("attest()")();
      await pos.connect(v2).getFunction("attest()")();
      await pos.connect(v3).getFunction("attest()")();
      const [stakeBefore] = await pos.getValidatorStats(v2.address);
      await pos.slash(v2.address, "Misbehavior");
      const [stakeV2] = await pos.getValidatorStats(v2.address);
      expect(stakeV2).to.be.lt(stakeBefore);
      expect(stakeV2).to.be.gte(ethers.parseEther("91")); // 96 ETH - 5% slash
      expect(await pos.slashCount(v2.address)).to.equal(1);
    });

    it("scenario: full lifecycle - stake, attest, request withdrawal, withdraw", async function () {
      const { pos, instructor, v1 } = await loadFixture(deployFixture);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.proposeBlock();
      await pos.connect(v1).getFunction("attest()")();
      await time.increase(31);
      await pos.connect(v1).requestWithdrawal();
      await time.increase(61);
      await pos.connect(v1).withdraw();
      expect(await pos.stakes(v1.address)).to.equal(0);
      expect(await pos.getValidatorCount()).to.equal(0);
    });

    it("scenario: role pool + stake + chat order", async function () {
      const { pos, instructor, v1, v2 } = await loadFixture(deployFixture);
      await pos.setRolePool(["Seller", "Buyer", "Mechanic"]);
      await pos.connect(v1).stake({ value: ethers.parseEther("32") });
      await pos.connect(v2).sendMessage("Hi");
      expect(await pos.roleAssignment(v1.address)).to.equal("Seller");
      expect(await pos.roleAssignment(v2.address)).to.equal("Buyer");
    });
  });
});
