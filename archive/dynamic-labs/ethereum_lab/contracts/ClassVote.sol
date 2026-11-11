// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ClassVote {
    struct Proposal {
        string name;
        uint256 voteCount;
    }

    address public chairperson;
    mapping(address => bool) public hasVoted;
    Proposal[] public proposals;

    event Voted(address voter, uint256 proposal);
    event ProposalAdded(string name);

    constructor() {
        chairperson = msg.sender;
    }

    function addProposal(string memory name) public {
        require(msg.sender == chairperson, "Only chairperson");
        proposals.push(Proposal(name, 0));
        emit ProposalAdded(name);
    }

    function vote(uint256 proposalIndex) public {
        require(!hasVoted[msg.sender], "Already voted");
        require(proposalIndex < proposals.length, "Invalid proposal");
        hasVoted[msg.sender] = true;
        proposals[proposalIndex].voteCount++;
        emit Voted(msg.sender, proposalIndex);
    }

    function getProposal(uint256 index) public view returns (string memory name, uint256 voteCount) {
        require(index < proposals.length, "Invalid index");
        Proposal storage p = proposals[index];
        return (p.name, p.voteCount);
    }

    function proposalCount() public view returns (uint256) {
        return proposals.length;
    }

    function winner() public view returns (string memory name, uint256 voteCount) {
        require(proposals.length > 0, "No proposals");
        uint256 winIdx = 0;
        for (uint256 i = 1; i < proposals.length; i++) {
            if (proposals[i].voteCount > proposals[winIdx].voteCount) {
                winIdx = i;
            }
        }
        return (proposals[winIdx].name, proposals[winIdx].voteCount);
    }
}