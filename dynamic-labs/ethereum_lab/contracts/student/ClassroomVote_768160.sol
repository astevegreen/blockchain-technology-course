// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ClassroomVote
 * @dev Simple classroom voting demonstration
 * 
 * Question: What should our lunch break policy be?
 * Option A: Keep lunch at 1 hour 30 minutes
 * Option B: Change to 1 hour lunch, leave 30 minutes early
 * 
 * Features:
 * - Open voting (any address can vote once)
 * - Instructor controls (open/close voting)
 * - Live results display
 */
contract ClassroomVote {
    // ===== STATE VARIABLES =====
    address public instructor;
    string public question;
    string public optionA;
    string public optionB;
    
    uint256 public votesForA;
    uint256 public votesForB;
    bool public votingOpen;
    
    mapping(address => bool) public hasVoted;
    mapping(address => string) public voterChoice;
    address[] public voters;
    
    // ===== EVENTS =====
    event VotingOpened(string question);
    event VoteCast(address indexed voter, string choice);
    event VotingClosed(string winner, uint256 winnerVotes, uint256 totalVotes);
    
    // ===== MODIFIERS =====
    modifier onlyInstructor() {
        require(msg.sender == instructor, "Only instructor can call this");
        _;
    }
    
    modifier whenVotingOpen() {
        require(votingOpen, "Voting is not open");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor() {
        instructor = msg.sender;
        question = "What should our lunch break policy be?";
        optionA = "Keep lunch at 1 hour 30 minutes";
        optionB = "Change to 1 hour lunch, leave 30 minutes early";
        votingOpen = false;
    }
    
    // ===== INSTRUCTOR FUNCTIONS =====
    
    /// @notice Open voting for students
    function openVoting() external onlyInstructor {
        require(!votingOpen, "Voting already open");
        votingOpen = true;
        emit VotingOpened(question);
    }
    
    /// @notice Close voting and announce winner
    function closeVoting() external onlyInstructor {
        require(votingOpen, "Voting not open");
        votingOpen = false;
        
        string memory winner;
        uint256 winnerVotes;
        
        if (votesForA > votesForB) {
            winner = optionA;
            winnerVotes = votesForA;
        } else if (votesForB > votesForA) {
            winner = optionB;
            winnerVotes = votesForB;
        } else {
            winner = "TIE";
            winnerVotes = votesForA;
        }
        
        emit VotingClosed(winner, winnerVotes, voters.length);
    }
    
    /// @notice Reset voting for a new round
    function resetVoting() external onlyInstructor {
        require(!votingOpen, "Close voting first");
        
        // Clear all votes
        for (uint256 i = 0; i < voters.length; i++) {
            delete hasVoted[voters[i]];
            delete voterChoice[voters[i]];
        }
        delete voters;
        votesForA = 0;
        votesForB = 0;
    }
    
    // ===== STUDENT VOTING =====
    
    /// @notice Vote for Option A
    function voteA() external whenVotingOpen {
        require(!hasVoted[msg.sender], "Already voted");
        
        hasVoted[msg.sender] = true;
        voterChoice[msg.sender] = "A";
        voters.push(msg.sender);
        votesForA++;
        
        emit VoteCast(msg.sender, optionA);
    }
    
    /// @notice Vote for Option B
    function voteB() external whenVotingOpen {
        require(!hasVoted[msg.sender], "Already voted");
        
        hasVoted[msg.sender] = true;
        voterChoice[msg.sender] = "B";
        voters.push(msg.sender);
        votesForB++;
        
        emit VoteCast(msg.sender, optionB);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    /// @notice Get current results (can be called anytime)
    function getResults() external view returns (
        string memory _question,
        string memory _optionA,
        uint256 _votesA,
        string memory _optionB,
        uint256 _votesB,
        uint256 _totalVoters,
        bool _isOpen
    ) {
        return (question, optionA, votesForA, optionB, votesForB, voters.length, votingOpen);
    }
    
    /// @notice Get the current winner (or leading option)
    function getWinner() external view returns (string memory winner, uint256 votes, string memory status) {
        if (votesForA > votesForB) {
            return (optionA, votesForA, votesForA == votesForB ? "TIE" : "LEADING");
        } else if (votesForB > votesForA) {
            return (optionB, votesForB, "LEADING");
        } else {
            return ("TIE", votesForA, "TIE");
        }
    }
    
    /// @notice Get formatted results for display
    function getFormattedResults() external view returns (string memory) {
        // Returns a simple summary string
        return string(abi.encodePacked(
            "Question: ", question,
            " | Option A: ", _uint2str(votesForA), " votes",
            " | Option B: ", _uint2str(votesForB), " votes",
            " | Total: ", _uint2str(voters.length), " voters"
        ));
    }
    
    /// @notice Check if an address has voted
    function checkVoter(address voter) external view returns (bool voted, string memory choice) {
        return (hasVoted[voter], voterChoice[voter]);
    }
    
    /// @notice Get total number of voters
    function getTotalVoters() external view returns (uint256) {
        return voters.length;
    }
    
    // Helper to convert uint to string
    function _uint2str(uint256 _i) internal pure returns (string memory) {
        if (_i == 0) return "0";
        uint256 j = _i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
}
