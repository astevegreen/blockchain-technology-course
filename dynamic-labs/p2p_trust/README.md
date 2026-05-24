# ReliefLedger & ReliefFS: P2P Network Lab

## Access

When this lab runs behind the shared outer router, use `/labs/p2p_trust/student1/` and `/labs/p2p_trust/instructor/`.

For standalone access without the outer router, the lab router publishes `http://localhost:8085/` by default.

## Scenario Overview
You have been deployed to help coordinate humanitarian relief in a dynamic and resource-constrained conflict zone. A wide array of NGOs operate in your area of operations, supporting logistics, medical care, food distribution, and displaced-person assistance. 

To improve efficiency, higher headquarters implemented two peer-to-peer systems:

1. **ReliefLedger**: A reputation system allowing NGOs to endorse one another based on positive cooperation.
2. **ReliefFS**: A new distributed file system designed to share critical supply manifests and operational data across the network.

Your mission is to audit both systems, identify vulnerabilities, test mitigations, and ensure the network can withstand adversarial conditions.

---

## Part 1: Reputation System Audit (ReliefLedger)

### Phase 1: Unusual NGO Activity
At first, the ReliefLedger system worked reasonably well. Trusted NGOs accumulated endorsements naturally. However, a recent anomaly has raised serious concerns:

* A surge of previously unknown NGOs appeared in the system within a short timespan.
* One well-established NGO’s endorsement total skyrocketed to an implausibly high number.
* Personnel from the field insist they did not create these new NGOs or issue the endorsements.

You have been given a snapshot of the system files taken *just before* these anomalies began, along with a local copy of the Python-based interface (`ngo_sim.py`) that NGOs use to interact with the system. 

**Your Task:** Determine how such an endorsement spike and flood of new NGOs could occur. Inspect current scores and experiment with registration and endorsement behavior to replicate the suspicious pattern.

* `python3 ngo_sim.py score`
* `python3 ngo_sim.py register`
* `python3 ngo_sim.py endorse`

**Discussion Questions:**

1. Why is an open, costless registration system dangerous for a decentralized reputation ledger? 
2. In a real-world network, what is the difference between a high volume of legitimate new users and a coordinated Sybil attack?

### Phase 2: Illicit Endorsements Continue
Once you have identified the registration vulnerability, HQ will authorize a patch. Apply it to your local simulation by running:

* `python3 ngo_sim.py patch`

This patch prevents recently created and unverified NGOs from issuing endorsements. However, the situation has taken another concerning turn:

* One particular NGO is receiving endorsements from *every verified NGO* in the system.
* Representatives from these legitimate NGOs claim they never endorsed the organization.
* All endorsing NGOs are verified, pre-existing, and unaffected by the recent patch.

**Your Task:** Determine how attackers are bypassing the patch. Use the provided interface to reproduce the anomaly. 

**Discussion Questions:**

1. The patch successfully restricted *Authorization* (who is allowed to endorse), but it failed to secure *Authentication*. Explain the difference between these two concepts in the context of this system.
2. What cryptographic mechanism is missing from the endorsement packets that allows this spoofing to occur?

### Phase 3: Strengthening the Trust Model
Your investigation has exposed flaws in the naive reputation model. To address these issues, HQ engineers are evaluating more resilient trust propagation mechanisms, specifically **EigenTrust** and **PeerTrust**.

These models spread trust through the network based on historical interactions and normalize influence to limit the impact of malicious nodes. 

**Your Task:** Analyze how these trust-propagation models perform under adversarial conditions. 

* `python3 ngo_sim.py audit` (Observe the advanced metrics)
* `python3 ngo_sim.py score` (Find and record the numeric ID for your suspicious `BadActor` row if you did not capture it during creation)
* `python3 ngo_sim.py audit --trace 123456` (Trace the flow of trust to your attacker by replacing the example `123456` with that numeric ID)

Evaluate how quickly scores converge, whether malicious behavior still leads to extreme outliers, and assess which model provides the most resilience for field deployment.

**Discussion Questions:**

1. How does EigenTrust's use of a "Pre-Trusted" anchor neutralize the closed-loop Sybil attacks you conducted in Phase 1? 
2. In a degraded or disconnected operational environment (e.g., cut off from headquarters), what is the operational risk of relying on these pre-trusted anchor nodes?

---

## Part 2: Distributed File System (ReliefFS)

Higher headquarters was highly impressed with your forensic analysis of the ReliefLedger reputation system. They have now requested your expertise to evaluate **ReliefFS**, the network's decentralized file-sharing protocol. 

Currently, the network is debating between two different architectures for locating files across nodes: an unstructured "Gossip" protocol, and a structured Distributed Hash Table (DHT) based on the Chord protocol.

### Phase 4: Gossip vs. DHT (Chord)
In an unstructured network, nodes don't know exactly where files live. They must ask their neighbors, who ask their neighbors, creating a flood of network traffic. In a structured DHT, files and nodes are placed on a logical "ring," and each node maintains a "finger table" (a set of shortcuts) that allows them to quickly route requests to the correct destination.

**Your Task:** 1. **Explore Unstructured Routing:** Run the gossip simulation. Observe how many messages are required to find a target file or broadcast information across the network.
   * `python3 gossip_demo.py --mode lookup`
   * `python3 gossip_demo.py --mode broadcast`
2. **Master Structured Routing (Chord):** Run the DHT simulation. You will be placed at a random node on the ring. Using *only* your node's finger table, manually select the next hop to successfully route a request to a target file's hash. 
   * `python3 dht_demo.py`
   * Can you beat the "optimal" path? Try to reach the target in the fewest hops possible by intelligently selecting the furthest valid node in your finger table that does not overshoot the target.

**Discussion Questions:**

1. What happens to network bandwidth during a flood search if every node in a 1,000-node network requests a file simultaneously? 
2. Conversely, why might a rigid, structured DHT fail if nodes are highly mobile and constantly dropping offline?

---

## Part 3: Advanced Routing (Pastry)

### Phase 5: Fixing the Pastry Router
*This is an advanced exercise for teams that have completed the previous phases.*

A partner organization operating in an adjacent sector is using a different DHT protocol called **Pastry**. While Chord uses a simple numeric ring and finger tables, Pastry routes by matching the hexadecimal prefixes of node IDs (e.g., routing a message for `A4B...` to a node starting with `A4...`).

Unfortunately, their implementation is broken. Nodes are occasionally failing to route messages, causing critical supply requests to be dropped. 

**Your Task:**
Run the simulation to trigger the failure:

* `python3 pastry.py`

The simulation will stress-test the network until it finds a scenario where a node gets "stuck." Open `pastry.py` and inspect the `get_next_hop(self, key)` method. 

**The Bug:** The implementation successfully checks the Routing Table for a prefix match. However, when routing to a key that does not correspond exactly to known prefixes, the logic hits a "hole" in the routing table and simply returns `None`, dropping the message.

**The Fix:** Based on your understanding of the Pastry protocol's fallback mechanisms, implement the correct logic to ensure the message continues moving toward the target key even when the prefix table misses. Update the code so the network passes the stress test.

**Discussion Questions:**

1. In Pastry, why is the routing table alone insufficient for guaranteed message delivery? 
2. What secondary structure ensures the ring remains contiguous and allows for successful delivery when prefix routing fails?
