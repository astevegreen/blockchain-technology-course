// Hashing and Merkle Trees Lab - JavaScript Controller
// Augments the "Hashing and Merkle Trees" lesson

let pyodide = null;
let isReady = false;
let currentStep = 0;
let merkleTree = null;
let leafData = [];

// Initialize Pyodide
async function initPyodide() {
    try {
        pyodide = await loadPyodide({
            indexURL: "../../vendor/pyodide/v0.24.1/full/"
        });
        
        // Load hashlib for SHA-256
        await pyodide.runPythonAsync(`
import hashlib

def sha256_hash(data):
    """Compute SHA-256 hash of input string"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def compare_bits(hash1, hash2):
    """Compare two hex strings bit by bit and return statistics"""
    # Convert hex to binary
    def hex_to_bits(h):
        return ''.join(format(int(c, 16), '04b') for c in h)
    
    bits1 = hex_to_bits(hash1)
    bits2 = hex_to_bits(hash2)
    
    total_bits = len(bits1)
    matching = sum(1 for a, b in zip(bits1, bits2) if a == b)
    different = total_bits - matching
    
    return {
        'total': total_bits,
        'matching': matching,
        'different': different,
        'percentage_changed': (different / total_bits) * 100,
        'bits1': bits1,
        'bits2': bits2
    }

print("Hash functions initialized!")
        `);
        
        isReady = true;
        document.getElementById('loading-overlay').style.display = 'none';
        console.log('Pyodide ready!');
        
    } catch (error) {
        console.error('Error initializing Pyodide:', error);
        document.getElementById('loading-overlay').querySelector('div > div').textContent = 'Error loading Pyodide. Please refresh.';
    }
}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    initPyodide();
    showStep(0);
});

// Navigation
function showStep(step) {
    // Hide all steps
    document.querySelectorAll('.step-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Show current step
    const stepCard = document.querySelector(`.step-card[data-step="${step}"]`);
    if (stepCard) {
        stepCard.classList.add('active');
    }
    
    // Update step indicators
    document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
        if (index <= step) {
            indicator.classList.remove('bg-gray-600', 'text-gray-300');
            indicator.classList.add('bg-blue-600', 'text-white');
        } else {
            indicator.classList.remove('bg-blue-600', 'text-white');
            indicator.classList.add('bg-gray-600', 'text-gray-300');
        }
    });
    
    // Update navigation buttons
    document.getElementById('prev-btn').disabled = step === 0;
    document.getElementById('prev-btn').classList.toggle('opacity-50', step === 0);
    document.getElementById('prev-btn').classList.toggle('cursor-not-allowed', step === 0);
    
    const nextBtn = document.getElementById('next-btn');
    nextBtn.disabled = step >= 4;
    nextBtn.classList.toggle('opacity-50', step >= 4);
    nextBtn.classList.toggle('cursor-not-allowed', step >= 4);
    
    // Step-specific initialization
    if (step === 1) {
        // Initialize avalanche demo
        const input1 = document.getElementById('hash-input-1');
        const input2 = document.getElementById('hash-input-2');
        if (input1 && input2) {
            input1.value = 'Hello';
            input2.value = 'Helmo';
            updateDemoArea(`
                <div class="text-center">
                    <h3 class="text-white font-bold mb-2">🔍 Try This Experiment:</h3>
                    <p class="text-gray-300 mb-2">Hash "Hello" and "Helmo" - notice they're almost identical (just one letter different!)</p>
                    <p class="text-yellow-300">Watch how the hashes are COMPLETELY different - that's the avalanche effect!</p>
                    <p class="text-xs text-gray-400 mt-2">This is why hashes can detect tampering - even a tiny change shows up instantly.</p>
                </div>
            `);
        }
    } else if (step === 2) {
        updateDemoArea(`
            <div class="text-center">
                <h3 class="text-white font-bold mb-2">🌳 Building Your Block's Merkle Tree</h3>
                <p class="text-gray-300 mb-2">Enter transactions like a Bitcoin miner would. Watch the tree build level-by-level:</p>
                <ol class="text-left text-sm text-gray-400 space-y-1 inline-block">
                    <li>1. Each transaction gets hashed (creates leaves)</li>
                    <li>2. Leaves are paired and hashed together (creates branches)</li>
                    <li>3. Process repeats until ONE root hash remains</li>
                </ol>
                <p class="text-yellow-300 mt-2">That root hash goes in the block header - it commits to ALL transactions!</p>
            </div>
        `);
    } else if (step === 3) {
        updateDemoArea(`
            <div class="text-center">
                <h3 class="text-white font-bold mb-2">💡 Light Wallet Magic</h3>
                <p class="text-gray-300 mb-2">You only have the block header (root hash). Can you verify a transaction without downloading all of them?</p>
                <p class="text-yellow-300">YES! With a Merkle proof - just a few sibling hashes showing the path to root.</p>
                <p class="text-xs text-gray-400 mt-2">This is how your phone wallet verifies transactions efficiently!</p>
            </div>
        `);
        updateProofSelect();
    } else if (step === 4) {
        updateDemoArea(`
            <div class="text-center">
                <h3 class="text-white font-bold mb-2 text-sm">⚠️ Why Specifications Matter</h3>
                <p class="text-gray-300 mb-2 text-xs">Same two hashes, different order = completely different result. This is why everyone must use the same convention!</p>
            </div>
        `);
        // Auto-run the demonstration
        setTimeout(() => {
            demonstrateOrdering();
        }, 500);
    }
}

function nextStep() {
    if (currentStep < 4) {
        currentStep++;
        showStep(currentStep);
    }
}

function previousStep() {
    if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
    }
}

function updateDemoArea(message) {
    const demoArea = document.getElementById('demo-area');
    if (demoArea) {
        if (typeof message === 'string' && message.includes('<')) {
            // HTML content
            demoArea.innerHTML = message;
        } else {
            // Plain text
            demoArea.innerHTML = `<div class="text-gray-300">${message}</div>`;
        }
    }
}

// Hash and display result
async function hashAndDisplay(inputId, outputId) {
    if (!isReady) {
        alert('System not ready yet. Please wait...');
        return;
    }
    
    const input = document.getElementById(inputId);
    const output = document.getElementById(outputId);
    const explanationDiv = document.getElementById('hash-explanation-1');
    
    if (!input || !output) return;
    
    const message = input.value;
    if (!message) {
        alert('Please enter a message');
        return;
    }
    
    // Show computing state
    output.innerHTML = '<div class="text-yellow-400"><i class="fas fa-spinner fa-spin"></i> Computing SHA-256 hash...</div>';
    
    try {
        const hash = await pyodide.runPythonAsync(`
sha256_hash(${JSON.stringify(message)})
        `);
        
        const inputLength = message.length;
        const hashLength = hash.length;
        const bitLength = hashLength * 4; // Each hex char = 4 bits
        
        output.innerHTML = `
            <div class="text-green-400 font-bold mb-1"><i class="fas fa-check-circle"></i> SHA-256 Hash:</div>
            <div class="text-blue-300 break-all font-mono text-xs">${hash}</div>
            <div class="text-xs text-gray-400 mt-2">
                <div>Input: "${message}" (${inputLength} characters)</div>
                <div>Output: ${hashLength} hex characters = ${bitLength} bits (fixed size!)</div>
                <div class="text-yellow-300 mt-1"><strong>Note:</strong> Output is always 256 bits, regardless of input size</div>
            </div>
        `;
        
        if (explanationDiv && inputId === 'hash-input-1') {
            explanationDiv.style.display = 'block';
            explanationDiv.innerHTML = `
                <div class="p-2 bg-blue-500/10 rounded text-xs">
                    <strong>What happened:</strong> Your text was converted to bytes, processed through SHA-256's 64 rounds of operations (compression function), 
                    and produced a unique 256-bit fingerprint. Every unique input produces a unique output!
                </div>
            `;
        }
        
        // If both hashes are computed, compare them
        if (outputId === 'hash-output-2') {
            compareHashes();
        }
        
    } catch (error) {
        console.error('Error hashing:', error);
        output.innerHTML = '<div class="text-red-400">Error computing hash</div>';
    }
}

// Compare two hashes for avalanche effect
async function compareHashes() {
    const output1 = document.getElementById('hash-output-1');
    const output2 = document.getElementById('hash-output-2');
    const comparison = document.getElementById('avalanche-comparison');
    
    if (!output1 || !output2 || !comparison) return;
    
    const hash1Match = output1.textContent.match(/[a-f0-9]{64}/);
    const hash2Match = output2.textContent.match(/[a-f0-9]{64}/);
    
    if (!hash1Match || !hash2Match) return;
    
    const hash1 = hash1Match[0];
    const hash2 = hash2Match[0];
    
    try {
        const result = await pyodide.runPythonAsync(`
compare_bits(${JSON.stringify(hash1)}, ${JSON.stringify(hash2)})
        `);
        
        const stats = result.toJs({dict_converter: Object.fromEntries});
        
        comparison.style.display = 'block';
        
        // Display bit-by-bit comparison for first 32 bits
        let bitComparison = '';
        const bits1 = stats.bits1.substring(0, 128); // First 32 hex chars = 128 bits
        const bits2 = stats.bits2.substring(0, 128);
        
        for (let i = 0; i < 128; i++) {
            if (bits1[i] !== bits2[i]) {
                bitComparison += `<span class="bit-change">${bits1[i]}</span>`;
            } else {
                bitComparison += `<span class="bit-match">${bits1[i]}</span>`;
            }
            if ((i + 1) % 8 === 0) bitComparison += ' ';
            if ((i + 1) % 32 === 0) bitComparison += '<br>';
        }
        
        document.getElementById('bit-comparison').innerHTML = `
            <div class="mb-2">
                <strong>Total bits:</strong> ${stats.total}<br>
                <strong>Bits changed:</strong> <span class="text-red-400">${stats.different}</span><br>
                <strong>Bits unchanged:</strong> <span class="text-green-400">${stats.matching}</span><br>
                <strong>Percentage changed:</strong> <span class="text-yellow-400 font-bold">${stats.percentage_changed.toFixed(1)}%</span>
            </div>
            <div class="mt-2">
                <strong>First 128 bits comparison:</strong><br>
                <div class="font-mono text-xs mt-1">${bitComparison}</div>
                <div class="text-xs mt-1 text-gray-400">
                    <span class="bit-match">Green</span> = unchanged, <span class="bit-change">Red</span> = changed
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error comparing hashes:', error);
    }
}

// Build Merkle tree
async function buildMerkleTree() {
    if (!isReady) {
        alert('System not ready yet. Please wait...');
        return;
    }
    
    const input = document.getElementById('tree-data-input');
    if (!input) return;
    
    const lines = input.value.trim().split('\n').filter(line => line.trim());
    
    if (lines.length === 0) {
        alert('Please enter at least one data item');
        return;
    }
    
    leafData = lines;
    
    // Show building status
    const container = document.getElementById('tree-visualization');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-10">
                <div class="text-yellow-400 mb-2"><i class="fas fa-spinner fa-spin text-2xl"></i></div>
                <div class="text-sm">Building Merkle tree...</div>
                <div class="text-xs text-gray-400 mt-2">
                    <div>Step 1: Hashing ${lines.length} data items (creating leaves)</div>
                    <div>Step 2: Pairing and hashing to create branches</div>
                    <div>Step 3: Repeating until root is computed</div>
                </div>
            </div>
        `;
    }
    
    try {
        // Build tree using Python
        const treeData = await pyodide.runPythonAsync(`
import hashlib

def hash_data(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def build_merkle_tree(items):
    """Build a Merkle tree from a list of items"""
    if len(items) == 0:
        return None
    
    # Hash all leaves
    leaves = [hash_data(item) for item in items]
    tree = {
        'levels': [leaves.copy()],
        'structure': []
    }
    
    current_level = leaves
    level_index = 0
    
    while len(current_level) > 1:
        next_level = []
        structure = []
        
        i = 0
        while i < len(current_level):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
            
            # If odd number and not at last pair, duplicate the last one
            if i + 1 >= len(current_level) and len(current_level) % 2 == 1:
                right = current_level[i]  # Duplicate
            
            # Concatenate and hash: H(left || right)
            combined = left + right
            parent_hash = hash_data(combined)
            
            next_level.append(parent_hash)
            structure.append({
                'left': left,
                'right': right,
                'parent': parent_hash,
                'left_idx': i,
                'right_idx': i + 1 if i + 1 < len(current_level) else i
            })
            
            i += 2
        
        tree['levels'].append(next_level.copy())
        tree['structure'].append(structure)
        current_level = next_level
        level_index += 1
    
    tree['root'] = current_level[0] if len(current_level) > 0 else None
    return tree

items = ${JSON.stringify(lines)}
tree = build_merkle_tree(items)
import json
json.dumps(tree)
        `);
        
        merkleTree = JSON.parse(treeData);
        
        // Visualize the tree
        visualizeMerkleTree();
        updateProofSelect();
        
        const numLevels = merkleTree.levels.length;
        const numLeaves = leafData.length;
        updateDemoArea(`✓ Tree built successfully! ${numLeaves} leaves organized into ${numLevels} levels. Root: ${merkleTree.root.substring(0, 16)}...`);
        
        // Add explanation after tree is built
        const container = document.getElementById('tree-visualization');
        if (container) {
            const explanation = document.createElement('div');
            explanation.className = 'mt-4 p-3 bg-green-500/20 rounded border border-green-500/50 text-xs';
            explanation.innerHTML = `
                <div class="font-bold text-green-300 mb-2"><i class="fas fa-check-circle"></i> Tree Built Successfully!</div>
                <div class="text-gray-300 space-y-1 text-xs">
                    <div><strong>🌿 Photos in Album (Leaves):</strong> ${merkleTree.levels[0].length} data items, each with its own fingerprint (hash)</div>
                    <div><strong>🌳 Group Photos (Branches):</strong> ${numLevels - 1} levels of grouped hashes working their way up</div>
                    <div><strong>👑 Master Photo (Root):</strong> One single hash that represents ALL ${numLeaves} items</div>
                    <div class="mt-2 p-2 bg-yellow-500/10 rounded border border-yellow-500/30">
                        <div class="text-yellow-300 font-bold text-xs mb-1">💡 Key Insight:</div>
                        <div class="text-xs text-gray-300">
                            The root hash is like a unique fingerprint of your ENTIRE photo album. If someone changes, adds, or removes even ONE photo (leaf), 
                            the master photo fingerprint (root) will be completely different. This means you can instantly detect any tampering!
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(explanation);
        }
        
    } catch (error) {
        console.error('Error building tree:', error);
        alert('Error building tree: ' + error.message);
        if (container) {
            container.innerHTML = '<div class="text-red-400">Error building tree. Please check your input.</div>';
        }
    }
}

// Visualize Merkle tree
function visualizeMerkleTree() {
    const container = document.getElementById('tree-visualization');
    if (!container || !merkleTree) return;
    
    container.innerHTML = '';
    
    // Display levels from root to leaves (reverse)
    const levels = merkleTree.levels.slice().reverse();
    
    levels.forEach((level, levelIndex) => {
        const levelDiv = document.createElement('div');
        levelDiv.className = 'tree-level mb-4';
        levelDiv.style.textAlign = 'center';
        
        level.forEach((hash, idx) => {
            const node = document.createElement('div');
            const isRoot = levelIndex === 0 && level.length === 1;
            const isLeaf = levelIndex === levels.length - 1;
            
            node.className = 'merkle-node';
            if (isRoot) {
                node.classList.add('root');
                node.innerHTML = `
                    <div class="font-bold text-yellow-400 mb-1">ROOT</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                `;
            } else if (isLeaf) {
                node.classList.add('leaf');
                node.innerHTML = `
                    <div class="text-green-400 font-bold mb-1">${leafData[idx] || 'Leaf'}</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                    <div class="text-xs text-gray-400 mt-1">Index: ${idx}</div>
                `;
            } else {
                node.classList.add('branch');
                node.innerHTML = `
                    <div class="text-blue-400 font-bold mb-1">Branch</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                `;
            }
            
            node.dataset.level = levelIndex;
            node.dataset.index = idx;
            node.dataset.hash = hash;
            
            levelDiv.appendChild(node);
        });
        
        container.appendChild(levelDiv);
        
        // Add level label
        if (levelIndex === 0) {
            levelDiv.insertAdjacentHTML('beforebegin', '<div class="text-center text-yellow-400 font-bold mb-2">Root Level</div>');
        } else if (levelIndex === levels.length - 1) {
            levelDiv.insertAdjacentHTML('beforebegin', '<div class="text-center text-green-400 font-bold mb-2">Leaf Level</div>');
        } else {
            levelDiv.insertAdjacentHTML('beforebegin', `<div class="text-center text-blue-400 font-bold mb-2">Level ${levelIndex}</div>`);
        }
    });
}

// Update proof select dropdown
function updateProofSelect() {
    const select = document.getElementById('proof-leaf-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a leaf...</option>';
    
    if (leafData && leafData.length > 0) {
        leafData.forEach((data, idx) => {
            const option = document.createElement('option');
            option.value = idx;
            option.textContent = `Leaf ${idx}: "${data}"`;
            select.appendChild(option);
        });
    }
}

// Generate and verify inclusion proof
async function generateProof() {
    if (!merkleTree || !isReady) {
        alert('Please build a tree first (Step 3)');
        return;
    }
    
    const select = document.getElementById('proof-leaf-select');
    if (!select || !select.value) {
        alert('Please select a leaf to verify');
        return;
    }
    
    const leafIndex = parseInt(select.value);
    
    // Show proof generation status
    const proofContainer = document.getElementById('proof-visualization');
    const stepsContainer = document.getElementById('proof-steps');
    
    if (proofContainer) {
        proofContainer.innerHTML = `
            <div class="text-center py-10">
                <div class="text-purple-400 mb-2"><i class="fas fa-spinner fa-spin text-2xl"></i></div>
                <div class="text-sm">Generating inclusion proof for "${leafData[leafIndex]}"...</div>
                <div class="text-xs text-gray-400 mt-2">
                    <div>Collecting sibling hashes from each level</div>
                    <div>Preparing verification path...</div>
                </div>
            </div>
        `;
    }
    
    try {
        // Generate proof path
        const proofData = await pyodide.runPythonAsync(`
import hashlib
import json

def hash_data(data):
    if isinstance(data, str):
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

tree_structure = ${JSON.stringify(merkleTree.structure)}
tree_levels = ${JSON.stringify(merkleTree.levels)}
target_index = ${leafIndex}
root_hash = ${JSON.stringify(merkleTree.root)}

# Generate proof path
proof_path = []
current_index = target_index
level_index = 0

while level_index < len(tree_levels) - 1:
    current_level = tree_levels[level_index]
    sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
    
    if sibling_index >= len(current_level):
        sibling_index = current_index  # Duplicate if odd
    
    sibling_hash = current_level[sibling_index]
    is_left = current_index % 2 == 0
    
    proof_path.append({
        'sibling_hash': sibling_hash,
        'position': 'left' if not is_left else 'right',  # Position of sibling
        'level': level_index
    })
    
    # Move to parent
    current_index = current_index // 2
    level_index += 1

# Now verify the proof
leaf_hash = tree_levels[0][target_index]
current_hash = leaf_hash

verification_steps = []

for step in proof_path:
    sibling = step['sibling_hash']
    position = step['position']
    
    if position == 'right':
        # We are left, sibling is right: H(current || sibling)
        combined = current_hash + sibling
    else:
        # We are right, sibling is left: H(sibling || current)
        combined = sibling + current_hash
    
    parent_hash = hash_data(combined)
    verification_steps.append({
        'left': current_hash if position == 'right' else sibling,
        'right': sibling if position == 'right' else current_hash,
        'combined': combined,
        'parent_hash': parent_hash
    })
    current_hash = parent_hash

result = {
    'proof_path': proof_path,
    'verification_steps': verification_steps,
    'computed_root': current_hash,
    'matches_root': current_hash == root_hash,
    'leaf_hash': leaf_hash,
    'root_hash': root_hash
}

json.dumps(result)
        `);
        
        const proof = JSON.parse(proofData);
        
        // Visualize proof
        visualizeProof(leafIndex, proof);
        displayProofSteps(proof);
        
        // Add summary explanation
        if (stepsContainer) {
            const summary = document.createElement('div');
            summary.className = 'mt-3 p-3 bg-purple-900/30 rounded border border-purple-500/50';
            summary.innerHTML = `
                <div class="font-bold text-purple-300 mb-2"><i class="fas fa-info-circle"></i> What Just Happened:</div>
                <div class="text-xs text-gray-300 space-y-1">
                    <div><strong>1. Proof Path Collected:</strong> ${proof.proof_path.length} sibling hashes representing the path from leaf to root</div>
                    <div><strong>2. Root Recomputed:</strong> Starting with your leaf, we used each sibling to compute parent hashes</div>
                    <div><strong>3. Verification:</strong> Our computed root ${proof.matches_root ? 'matches' : 'does NOT match'} the published root</div>
                    ${proof.matches_root ? 
                        '<div class="mt-2 text-green-300 font-bold">✓ This proves your leaf is authentic and unchanged!</div>' :
                        '<div class="mt-2 text-red-300 font-bold">✗ Verification failed - the leaf may have been tampered with!</div>'
                    }
                    <div class="mt-2 text-yellow-300">
                        <strong>Efficiency:</strong> We verified with only ${proof.proof_path.length} hashes (O(log n)) instead of all ${leafData.length} items (O(n))!
                    </div>
                </div>
            `;
            stepsContainer.appendChild(summary);
        }
        
        if (proof.matches_root) {
            updateDemoArea(`✓ Proof verified! Computed root matches published root: ${proof.computed_root.substring(0, 16)}...`);
        } else {
            updateDemoArea(`✗ Proof verification failed! Computed: ${proof.computed_root.substring(0, 16)}..., Expected: ${proof.root_hash.substring(0, 16)}...`);
        }
        
    } catch (error) {
        console.error('Error generating proof:', error);
        alert('Error generating proof: ' + error.message);
    }
}

// Visualize proof path
function visualizeProof(leafIndex, proof) {
    const container = document.getElementById('proof-visualization');
    if (!container || !merkleTree) return;
    
    // Rebuild visualization but highlight proof path
    container.innerHTML = '';
    
    const levels = merkleTree.levels.slice().reverse();
    
    levels.forEach((level, levelIndex) => {
        const levelDiv = document.createElement('div');
        levelDiv.className = 'tree-level mb-4';
        levelDiv.style.textAlign = 'center';
        
        level.forEach((hash, idx) => {
            const node = document.createElement('div');
            const isRoot = levelIndex === 0 && level.length === 1;
            const isLeaf = levelIndex === levels.length - 1;
            
            // Check if this node is in the proof path
            let inPath = false;
            if (levelIndex === levels.length - 1 && idx === leafIndex) {
                inPath = true; // This is the target leaf
            } else {
                // Check if this is a sibling in the proof path
                for (const step of proof.proof_path) {
                    if (step.level === (levels.length - 1 - levelIndex - 1)) {
                        // Need to check if this hash matches a sibling in proof
                        if (step.level >= 0 && step.level < merkleTree.levels.length - 1) {
                            const proofLevel = merkleTree.levels[step.level];
                            if (proofLevel.includes(hash) && hash === step.sibling_hash) {
                                inPath = true;
                            }
                        }
                    }
                }
                
                // Check if we're on the path to root
                if (levelIndex === 0) {
                    inPath = true; // Root is always in path
                }
            }
            
            node.className = 'merkle-node';
            if (inPath) {
                node.classList.add('proof-path');
            }
            
            if (isRoot) {
                node.classList.add('root');
                node.innerHTML = `
                    <div class="font-bold text-yellow-400 mb-1">ROOT</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                `;
            } else if (isLeaf) {
                node.classList.add('leaf');
                const highlight = idx === leafIndex ? 'border-4 border-purple-400' : '';
                node.className += ' ' + highlight;
                node.innerHTML = `
                    <div class="text-green-400 font-bold mb-1">${leafData[idx] || 'Leaf'}</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                    <div class="text-xs text-gray-400 mt-1">Index: ${idx}</div>
                    ${idx === leafIndex ? '<div class="text-xs text-purple-400 font-bold mt-1">← Target</div>' : ''}
                `;
            } else {
                node.classList.add('branch');
                node.innerHTML = `
                    <div class="text-blue-400 font-bold mb-1">Branch</div>
                    <div class="text-xs">${hash.substring(0, 16)}...</div>
                `;
            }
            
            levelDiv.appendChild(node);
        });
        
        container.appendChild(levelDiv);
    });
}

// Display proof verification steps
function displayProofSteps(proof) {
    const container = document.getElementById('proof-steps');
    if (!container) return;
    
    let html = `
        <div class="font-bold text-purple-300 mb-2">
            <i class="fas fa-list-ol"></i> Step-by-Step Verification:
        </div>
        <div class="text-xs text-gray-400 mb-3 italic">
            Starting from the leaf hash, we'll combine it with sibling hashes at each level to rebuild the root.
        </div>
    `;
    
    proof.verification_steps.forEach((step, idx) => {
        const levelNum = proof.verification_steps.length - idx;
        html += `
            <div class="mb-3 p-2 bg-black/30 rounded border-l-4 border-purple-500">
                <div class="font-bold text-xs mb-1">
                    Step ${idx + 1} - Level ${levelNum}:
                    <span class="text-purple-300 ml-2">Computing parent hash</span>
                </div>
                <div class="text-xs space-y-1">
                    <div>
                        <span class="text-blue-400">Left child:</span> 
                        <span class="font-mono text-blue-300">${step.left.substring(0, 16)}...</span>
                    </div>
                    <div>
                        <span class="text-blue-400">Right child:</span> 
                        <span class="font-mono text-blue-300">${step.right.substring(0, 16)}...</span>
                    </div>
                    <div class="mt-2 p-2 bg-yellow-500/10 rounded">
                        <div class="text-yellow-300 font-bold">Concatenation:</div>
                        <div class="font-mono text-xs mt-1 text-yellow-200">${step.combined.substring(0, 48)}...</div>
                        <div class="text-xs text-gray-400 mt-1">Formula: H(left || right)</div>
                    </div>
                    <div class="mt-2">
                        <span class="text-green-400 font-bold">Parent hash:</span> 
                        <span class="font-mono text-green-300">${step.parent_hash.substring(0, 16)}...</span>
                    </div>
                    <div class="text-xs text-gray-400 mt-1">
                        <i class="fas fa-arrow-up"></i> This parent becomes the child for the next level
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
        <div class="mt-3 p-3 rounded ${proof.matches_root ? 'bg-green-500/20 border border-green-500' : 'bg-red-500/20 border border-red-500'}">
            <div class="font-bold ${proof.matches_root ? 'text-green-300' : 'text-red-300'}">
                ${proof.matches_root ? '✓ Verification Successful!' : '✗ Verification Failed!'}
            </div>
            <div class="text-xs mt-1">
                Computed Root: <span class="font-mono">${proof.computed_root.substring(0, 16)}...</span><br>
                Published Root: <span class="font-mono">${proof.root_hash.substring(0, 16)}...</span>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Demonstrate ordering matters
async function demonstrateOrdering() {
    if (!isReady) {
        alert('System not ready yet. Please wait...');
        return;
    }
    
    const correctDiv = document.getElementById('correct-order-demo');
    const wrongDiv = document.getElementById('wrong-order-demo');
    
    if (!correctDiv || !wrongDiv) {
        console.error('Could not find demo divs');
        return;
    }
    
    // Show loading state
    correctDiv.innerHTML = '<div class="text-yellow-400 text-xs"><i class="fas fa-spinner fa-spin"></i> Computing...</div>';
    wrongDiv.innerHTML = '<div class="text-yellow-400 text-xs"><i class="fas fa-spinner fa-spin"></i> Computing...</div>';
    
    try {
        const result = await pyodide.runPythonAsync(`
import hashlib
import json

def hash_data(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Use example hash values (simulating two child hashes in a tree)
left_hash = hash_data("alpha")  # Simulated left child hash
right_hash = hash_data("beta")   # Simulated right child hash

# Correct order: H(left || right)
correct_order = hash_data(left_hash + right_hash)

# Wrong order: H(right || left)
wrong_order = hash_data(right_hash + left_hash)

result = {
    'left': left_hash,
    'right': right_hash,
    'correct_combined': left_hash + right_hash,
    'wrong_combined': right_hash + left_hash,
    'correct_hash': correct_order,
    'wrong_hash': wrong_order,
    'are_different': correct_order != wrong_order
}

json.dumps(result)
        `);
        
        const demo = JSON.parse(result);
        
        correctDiv.innerHTML = `
            <div class="text-xs mb-2">
                <div class="text-gray-400 mb-1">Example: Two child hashes</div>
                <div>Left hash: <span class="text-blue-300 font-mono text-xs">${demo.left.substring(0, 16)}...</span></div>
                <div>Right hash: <span class="text-blue-300 font-mono text-xs">${demo.right.substring(0, 16)}...</span></div>
                <div class="mt-2 p-2 bg-green-500/10 rounded">
                    <div class="text-green-400 font-bold mb-1">H(left || right):</div>
                    <div class="text-green-300 font-mono break-all text-xs">${demo.correct_hash}</div>
                </div>
            </div>
        `;
        
        wrongDiv.innerHTML = `
            <div class="text-xs mb-2">
                <div class="text-gray-400 mb-1">Same two hashes</div>
                <div>Left hash: <span class="text-blue-300 font-mono text-xs">${demo.left.substring(0, 16)}...</span></div>
                <div>Right hash: <span class="text-blue-300 font-mono text-xs">${demo.right.substring(0, 16)}...</span></div>
                <div class="mt-2 p-2 bg-red-500/10 rounded">
                    <div class="text-red-400 font-bold mb-1">H(right || left):</div>
                    <div class="text-red-300 font-mono break-all text-xs">${demo.wrong_hash}</div>
                </div>
            </div>
        `;
        
        if (demo.are_different) {
            updateDemoArea('✓ Notice: Same inputs, different order = COMPLETELY different hashes! This is why protocol specifications must be precise - everyone must use the same order.');
            
            // Add a comparison note
            setTimeout(() => {
                const comparisonNote = document.createElement('div');
                comparisonNote.className = 'mt-3 p-2 bg-yellow-500/20 rounded border border-yellow-500/50 text-xs';
                comparisonNote.innerHTML = `
                    <div class="font-bold text-yellow-300 mb-1"><i class="fas fa-exclamation-triangle"></i> See the Difference!</div>
                    <div class="text-gray-300">
                        Even though we're using the <strong>exact same two hashes</strong>, just swapping their order produces 
                        a <strong>completely different result</strong>. In blockchain, if one implementation uses H(left||right) 
                        and another uses H(right||left), they'll never agree on the root hash!
                    </div>
                `;
                wrongDiv.parentElement.parentElement.appendChild(comparisonNote);
            }, 500);
        }
        
    } catch (error) {
        console.error('Error demonstrating ordering:', error);
        correctDiv.innerHTML = '<div class="text-red-400 text-xs">Error computing hash</div>';
        wrongDiv.innerHTML = '<div class="text-red-400 text-xs">Error computing hash</div>';
    }
}
