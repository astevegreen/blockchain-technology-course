const { expect } = require("chai");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

const MIN_STAKE = ethers.parseEther("32");

describe("BeaconChainLab", function () {
  async function deployBeaconFixture() {
    const [instructor, human, human2, ...bots] = await ethers.getSigners();
    const BeaconChainLab = await ethers.getContractFactory("BeaconChainLab");
    const lab = await BeaconChainLab.deploy(1, 4, 2);
    await lab.waitForDeployment();
    await lab.setBotMisbehaviorChance(0, 0);
    return { lab, instructor, human, human2, bots };
  }

  async function startWithHumanFixture() {
    const fixture = await deployBeaconFixture();
    const { lab, human, bots } = fixture;
    await lab.connect(human).join({ value: MIN_STAKE });
    await lab.fillBotsAndStart(bots.slice(0, 8).map((b) => b.address), false);
    return fixture;
  }

  function countAddress(addrs, target) {
    return addrs.filter((a) => a.toLowerCase() === target.toLowerCase()).length;
  }

  it("exits and rejoins without duplicating or wedging the validator", async function () {
    const { lab, human } = await loadFixture(startWithHumanFixture);

    expect(countAddress(await lab.getCommittee(), human.address)).to.equal(1);

    await expect(lab.connect(human).exit())
      .to.emit(lab, "ValidatorExited");

    expect(await lab.inPool(human.address)).to.equal(false);
    expect(await lab.exited(human.address)).to.equal(true);
    expect(await lab.stakes(human.address)).to.equal(0);
    expect(countAddress(await lab.getCommittee(), human.address)).to.equal(0);

    await expect(lab.connect(human).join({ value: MIN_STAKE }))
      .to.be.revertedWith("Use rejoin");

    await expect(lab.connect(human).rejoin({ value: MIN_STAKE }))
      .to.emit(lab, "Joined")
      .withArgs(human.address, MIN_STAKE);

    expect(await lab.inPool(human.address)).to.equal(true);
    expect(await lab.exited(human.address)).to.equal(false);
    expect(countAddress(await lab.getCommittee(), human.address)).to.equal(1);

    await expect(lab.connect(human).exit())
      .to.emit(lab, "ValidatorExited");
  });

  it("resets with virtual bot stake without refunding bots", async function () {
    const { lab, human, bots } = await loadFixture(deployBeaconFixture);
    await lab.connect(human).join({ value: MIN_STAKE });
    await lab.fillBotsAndStart(bots.slice(0, 8).map((b) => b.address), false);

    const totalStaked = await lab.totalStaked();
    const contractBalance = await ethers.provider.getBalance(lab.target);
    expect(totalStaked).to.be.gt(contractBalance);

    await expect(lab.resetSession())
      .to.emit(lab, "SessionReset");

    expect(await lab.getSessionState()).to.equal(0);
    expect(await lab.getCommitteeSize()).to.equal(0);
    expect(await lab.totalStaked()).to.equal(0);
    expect(await lab.inPool(human.address)).to.equal(false);
    expect(await lab.exited(human.address)).to.equal(false);
    expect(await lab.stakes(human.address)).to.equal(0);
  });

  it("finalizes checkpoints in idle pivotal mode and keeps lastFinalizedIndex forward", async function () {
    const { lab, bots } = await loadFixture(deployBeaconFixture);
    await lab.fillBotsAndStart(bots.slice(0, 8).map((b) => b.address), false);

    for (let i = 0; i < 5; i++) {
      await lab.proposeBlock();
    }

    const epoch1Checkpoint = await lab.getBlockInfo(1);
    expect(epoch1Checkpoint.finalized).to.equal(true);
    expect(await lab.lastFinalizedIndex()).to.equal(1);
  });

  it("does not treat the same slot in a new epoch as a double vote", async function () {
    const { lab, human } = await loadFixture(startWithHumanFixture);

    await lab.proposeBlock(); // epoch 1, slot 1
    const b0 = await lab.getBlockInfo(0);
    await expect(lab.connect(human).attest(0, b0.blockHash))
      .to.emit(lab, "Attested")
      .withArgs(human.address, 0);

    await lab.proposeBlock(); // epoch 1, slot 2
    await lab.proposeBlock(); // epoch 2, slot 1
    const b2 = await lab.getBlockInfo(2);
    expect(b2.epoch).to.equal(2);
    expect(b2.slot).to.equal(1);

    await expect(lab.connect(human).attest(2, b2.blockHash))
      .to.emit(lab, "Attested")
      .withArgs(human.address, 2);

    expect(await lab.hasPendingSlash(human.address)).to.equal(false);
  });

  it("emits the block's own epoch for boundary block proposals", async function () {
    const { lab, bots } = await loadFixture(deployBeaconFixture);
    await lab.fillBotsAndStart(bots.slice(0, 8).map((b) => b.address), false);

    await lab.proposeBlock();
    await expect(lab.proposeBlock())
      .to.emit(lab, "BlockProposed")
      .withArgs(1, anyValue, 1);
  });
});
