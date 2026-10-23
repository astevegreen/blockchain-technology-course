// Crypto Primitives Lab - JavaScript Controller
// This lab demonstrates public key encryption and shared secret key exchange

let pyodide = null;
let isReady = false;
let currentStep = 0;
let cryptoState = {
    alice: { privateKey: null, publicKey: null },
    recipient: { privateKey: null, publicKey: null, name: 'Bob' },
    sharedSecret: null,
    encryptedSecret: null
};

// Initialize Pyodide
async function initPyodide() {
    try {
        pyodide = await loadPyodide({
            indexURL: "../../vendor/pyodide/v0.24.1/full/"
        });
        
        // Load crypto implementation
        await pyodide.runPythonAsync(`
import hashlib
import secrets
import base64
import json

# Simplified encryption for educational purposes
# WARNING: This is NOT secure crypto for production use!
# It's simplified for educational demonstration only
class SimpleCrypto:
    def __init__(self):
        pass
    
    # Public-key encryption is hashed ElGamal over the 2048-bit RFC 3526 group 14.
    # The public key is G^x mod P, so only the holder of the private x can decrypt.
    P = int(
        "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74"
        "020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F1437"
        "4FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
        "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF05"
        "98DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB"
        "9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
        "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718"
        "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)
    G = 2

    def _random_exponent(self):
        return secrets.randbits(256) | (1 << 255)

    def _keystream_xor(self, shared, data):
        """XOR data with SHA-256(shared || counter) blocks"""
        shared_bytes = shared.to_bytes(256, 'big')
        out = bytearray()
        for block in range(0, len(data), 32):
            pad = hashlib.sha256(shared_bytes + block.to_bytes(4, 'big')).digest()
            out.extend(b ^ k for b, k in zip(data[block:block + 32], pad))
        return bytes(out)

    def generate_key_pair(self):
        """Generate an ElGamal key pair: private x, public G^x mod P"""
        x = self._random_exponent()
        return format(x, '064x'), format(pow(self.G, x, self.P), '0512x')

    def encrypt_with_public_key(self, message, public_key):
        """Encrypt to a public key: a fresh k gives G^k and the shared value y^k"""
        y = int(public_key, 16)
        k = self._random_exponent()
        ciphertext = self._keystream_xor(pow(y, k, self.P), message.encode('utf-8'))
        result = {
            'ephemeral': format(pow(self.G, k, self.P), '0512x'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'method': 'hashed_elgamal'
        }
        return json.dumps(result)

    def decrypt_with_private_key(self, encrypted_data, private_key, public_key):
        """Decrypt with the private key: (G^k)^x equals the sender's y^k"""
        data = json.loads(encrypted_data)
        shared = pow(int(data['ephemeral'], 16), int(private_key, 16), self.P)
        plaintext = self._keystream_xor(shared, base64.b64decode(data['ciphertext']))
        return plaintext.decode('utf-8')
    
    def generate_shared_secret(self):
        """Generate a random shared secret"""
        return secrets.token_hex(32)
    
    def encrypt_symmetric(self, message, shared_secret):
        """Encrypt message using shared secret (symmetric encryption)"""
        message_bytes = message.encode('utf-8')
        key_bytes = hashlib.sha256(shared_secret.encode()).digest()
        
        ciphertext = bytearray()
        for i, byte in enumerate(message_bytes):
            ciphertext.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return base64.b64encode(bytes(ciphertext)).decode('utf-8')
    
    def decrypt_symmetric(self, encrypted_message, shared_secret):
        """Decrypt message using shared secret"""
        ciphertext = base64.b64decode(encrypted_message)
        key_bytes = hashlib.sha256(shared_secret.encode()).digest()
        
        plaintext = bytearray()
        for i, byte in enumerate(ciphertext):
            plaintext.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return plaintext.decode('utf-8')

# Create global crypto instance
crypto = SimpleCrypto()
print("Crypto primitives initialized!")
        `);
        
        isReady = true;
        document.getElementById('loadingOverlay').style.display = 'none';
        console.log('Pyodide and crypto primitives initialized');
        
    } catch (error) {
        console.error('Error initializing Pyodide:', error);
        document.getElementById('loadingOverlay').innerHTML = 
            '<div class="text-white text-center"><h3 class="text-red-400">Error Loading</h3><p>' + error + '</p></div>';
    }
}

// Clean up all visual elements
function cleanupAllVisuals() {
    // Hide all visual containers
    const secretGen = document.getElementById('secret-generation');
    const wrappingVisual = document.getElementById('wrapping-visual');
    const unwrappingVisual = document.getElementById('unwrapping-visual');
    const secretBox = document.getElementById('secret-box');
    const publicKeyWrapper = document.getElementById('public-key-wrapper');
    const keyRepo = document.getElementById('key-repository');
    const actionIndicator = document.getElementById('action-indicator');
    
    if (secretGen) {
        secretGen.style.display = 'none';
        const secretVisual = document.getElementById('secret-visual');
        if (secretVisual) secretVisual.textContent = '';
    }
    
    if (wrappingVisual) {
        wrappingVisual.style.display = 'none';
        wrappingVisual.style.left = '';
        wrappingVisual.style.top = '';
    }
    
    if (unwrappingVisual) {
        unwrappingVisual.style.display = 'none';
        unwrappingVisual.style.left = '';
    }
    
    if (secretBox) {
        secretBox.style.display = 'none';
        secretBox.classList.remove('sparkling');
        secretBox.style.position = '';
        secretBox.style.left = '';
        secretBox.style.top = '';
        secretBox.style.transform = '';
        const secretValueDisplay = document.getElementById('secret-value-display');
        if (secretValueDisplay) secretValueDisplay.textContent = '';
    }
    
    if (publicKeyWrapper) {
        publicKeyWrapper.style.display = 'none';
        publicKeyWrapper.classList.remove('wrapping', 'unwrapping');
    }
    
    if (keyRepo) {
        keyRepo.style.display = 'none';
        const repoKeyDisplay = document.getElementById('repo-key-display');
        if (repoKeyDisplay) repoKeyDisplay.textContent = '';
    }
    
    if (actionIndicator) {
        actionIndicator.style.display = 'none';
        actionIndicator.style.left = '';
        actionIndicator.style.transform = '';
    }
    
    // Clean up envelopes
    const envelopePubkey = document.getElementById('envelope-pubkey');
    const envelopeEncrypted = document.getElementById('envelope-encrypted');
    const envelopeAck = document.getElementById('envelope-acknowledgment');
    
    if (envelopePubkey) {
        envelopePubkey.style.display = 'none';
        envelopePubkey.classList.remove('glowing');
        envelopePubkey.style.transition = '';
        envelopePubkey.style.left = '';
        envelopePubkey.style.top = '';
    }
    
    if (envelopeEncrypted) {
        envelopeEncrypted.style.display = 'none';
        envelopeEncrypted.classList.remove('glowing');
        envelopeEncrypted.style.transition = '';
        envelopeEncrypted.style.left = '';
        envelopeEncrypted.style.top = '';
    }
    
    if (envelopeAck) {
        envelopeAck.style.display = 'none';
        envelopeAck.classList.remove('glowing');
        envelopeAck.style.transition = '';
        envelopeAck.style.left = '';
        envelopeAck.style.top = '';
    }
    
    // Clean up message bubbles
    const msgAliceToBob = document.getElementById('message-alice-to-bob');
    const msgBobToAlice = document.getElementById('message-bob-to-alice');
    
    if (msgAliceToBob) {
        msgAliceToBob.style.display = 'none';
        msgAliceToBob.style.transition = '';
        msgAliceToBob.style.left = '';
        msgAliceToBob.style.top = '';
    }
    
    if (msgBobToAlice) {
        msgBobToAlice.style.display = 'none';
        msgBobToAlice.style.transition = '';
        msgBobToAlice.style.left = '';
        msgBobToAlice.style.top = '';
    }
}

// Show notification toast
function showNotification(message, type = 'info') {
    // Remove existing notification if any
    const existing = document.getElementById('toast-notification');
    if (existing) {
        existing.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.id = 'toast-notification';
    notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg text-white transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-3"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Initialize recipient to Bob (no selection needed)
function initRecipient() {
    cryptoState.recipient.name = 'Bob';
    updateStepInfo('Ready to begin key exchange with Bob');
    
    // Update Step 0 instruction
    const step0Instruction = document.getElementById('step0-instruction');
    if (step0Instruction) {
        step0Instruction.innerHTML = '<strong class="text-green-400">✓ Ready to begin!</strong><br><span class="text-gray-300">Click "Next Step" below to continue</span>';
    }
    
    // Enable next step button
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.disabled = false;
        nextBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Generate keys
async function generateKeys() {
    if (!isReady) {
        updateStepInfo('Error: Crypto system not ready yet. Please wait...');
        return;
    }
    
    try {
        // Ensure recipient object exists
        if (!cryptoState.recipient) {
            cryptoState.recipient = { name: selectedRecipient ? selectedRecipient.charAt(0).toUpperCase() + selectedRecipient.slice(1) : 'Bob' };
        }
        
        // Update status in frame
        updateFrameStatus('Generating keys...', 'alice');
        updateFrameStatus('Generating keys...', 'recipient');
        
        // Generate Alice's keys
        const aliceKeys = await pyodide.runPythonAsync(`
import json
private, public = crypto.generate_key_pair()
json.dumps({"private": private, "public": public})
        `);
        const aliceKeysObj = JSON.parse(aliceKeys);
        cryptoState.alice = aliceKeysObj;
        
        // Generate recipient's keys
        const recipientKeys = await pyodide.runPythonAsync(`
import json
private, public = crypto.generate_key_pair()
json.dumps({"private": private, "public": public})
        `);
        const recipientKeysObj = JSON.parse(recipientKeys);
        
        // Merge recipient keys into existing recipient object (preserving name)
        cryptoState.recipient = { 
            ...cryptoState.recipient, 
            privateKey: recipientKeysObj.private,
            publicKey: recipientKeysObj.public
        };
        
        console.log('Keys generated:', {
            alice: { hasPrivate: !!cryptoState.alice?.private, hasPublic: !!cryptoState.alice?.public },
            recipient: { 
                name: cryptoState.recipient.name,
                hasPrivate: !!cryptoState.recipient.privateKey, 
                hasPublic: !!cryptoState.recipient.publicKey 
            }
        });
        
        // Update UI
        const alicePrivateEl = document.getElementById('alice-private');
        const alicePublicEl = document.getElementById('alice-public');
        const recipientPrivateEl = document.getElementById('recipient-private');
        const recipientPublicEl = document.getElementById('recipient-public');
        const recipientNameEl = document.getElementById('recipient-name');
        
        if (alicePrivateEl) alicePrivateEl.textContent = aliceKeysObj.private.substring(0, 64) + '...';
        if (alicePublicEl) alicePublicEl.textContent = aliceKeysObj.public.substring(0, 64) + '...';
        if (recipientPrivateEl) recipientPrivateEl.textContent = '*** KEPT SECRET ***';
        if (recipientPublicEl) recipientPublicEl.textContent = recipientKeysObj.public.substring(0, 64) + '...';
        if (recipientNameEl) recipientNameEl.textContent = cryptoState.recipient.name + "'s";
        
        // Show in frame: Alice queries for Bob's public key
        setTimeout(() => {
            animatePublicKeyRequest();
        }, 500);
        
    } catch (error) {
        console.error('Error generating keys:', error);
        updateStepInfo('Error generating keys: ' + error.message);
        alert('Error generating keys: ' + error);
    }
}

// Update status in communication frame
function updateFrameStatus(message, person) {
    const statusEl = person === 'alice' 
        ? document.getElementById('alice-status')
        : document.getElementById('recipient-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = 'text-xs text-yellow-400 mt-1';
    }
}

// Update step info display
function updateStepInfo(message) {
    const stepInfo = document.getElementById('step-info-text');
    if (stepInfo) {
        stepInfo.textContent = message;
    }
}

// Animate: Alice queries Bob's public key
function animatePublicKeyRequest() {
    // Clean up any existing visuals first
    cleanupAllVisuals();
    
    updateStepInfo('Step 2: Alice looks up Bob\'s public key in the directory');
    updateFrameStatus('Querying directory...', 'alice');
    
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const startX = 80; // Alice
    const endX = containerWidth - 140; // Bob
    const centerY = 160;
    
    const pathLine = document.getElementById('communication-path');
    pathLine.setAttribute('x1', startX);
    pathLine.setAttribute('y1', centerY);
    pathLine.setAttribute('x2', endX);
    pathLine.setAttribute('y2', centerY);
    
    // Show key repository at top center
    const keyRepo = document.getElementById('key-repository');
    const repoKeyDisplay = document.getElementById('repo-key-display');
    keyRepo.style.display = 'block';
    keyRepo.style.left = '50%';
    keyRepo.style.transform = 'translateX(-50%)';
    repoKeyDisplay.textContent = cryptoState.recipient.name + '\'s Public Key Available';
    
    // Animate request arrow from Alice to repository
    setTimeout(() => {
        // Show envelope/key coming from repository to Alice
        const envelope = document.getElementById('envelope-pubkey');
        envelope.style.display = 'flex';
        envelope.style.left = (containerWidth / 2) + 'px';
        envelope.style.top = '40px';
        envelope.querySelector('.envelope-label').textContent = 'Public Key';
        
        // Animate key moving from repository down to Alice
        setTimeout(() => {
            envelope.style.transition = 'left 1.5s ease-in-out, top 1.5s ease-in-out';
            envelope.style.left = startX + 'px';
            envelope.style.top = (centerY - 20) + 'px';
        }, 300);
        
        // Key arrives at Alice
        setTimeout(() => {
            envelope.style.display = 'none';
            envelope.classList.remove('glowing');
            // Clean up repository
            keyRepo.style.display = 'none';
            const repoKeyDisplay = document.getElementById('repo-key-display');
            if (repoKeyDisplay) repoKeyDisplay.textContent = '';
            updateFrameStatus('Public key retrieved ✓', 'alice');
            updateStepInfo('Step 2 Complete: Alice retrieved Bob\'s public key from directory');
        }, 2100);
        
    }, 500);
}

// Generate shared secret
async function generateSharedSecret() {
    if (!isReady) {
        updateStepInfo('Error: Crypto system not ready yet. Please wait...');
        return;
    }
    
    try {
        // Clean up any existing visuals first
        cleanupAllVisuals();
        
        updateStepInfo('Step 3: Alice generates a random shared secret');
        updateFrameStatus('Generating secret...', 'alice');
        
        // Show generation visual at Alice's position
        const secretGen = document.getElementById('secret-generation');
        const secretVisual = document.getElementById('secret-visual');
        if (secretGen) {
            secretGen.style.display = 'block';
            secretGen.style.left = '80px';
        }
        
        // Animate generation
        let chars = '';
        const charsToShow = '0123456789abcdef';
        for (let i = 0; i < 16; i++) {
            setTimeout(() => {
                chars += charsToShow[Math.floor(Math.random() * charsToShow.length)];
                if (secretVisual) secretVisual.textContent = chars + '...';
            }, i * 50);
        }
        
        const secret = await pyodide.runPythonAsync(`
crypto.generate_shared_secret()
        `);
        cryptoState.sharedSecret = secret;
        
        console.log('Shared secret generated:', {
            hasSecret: !!cryptoState.sharedSecret,
            length: cryptoState.sharedSecret?.length,
            preview: cryptoState.sharedSecret?.substring(0, 20) + '...'
        });
        
        const sharedSecretEl = document.getElementById('shared-secret');
        if (sharedSecretEl) sharedSecretEl.textContent = secret.substring(0, 64) + '...';
        
        setTimeout(() => {
            if (secretVisual) secretVisual.textContent = secret.substring(0, 16) + '...';
            setTimeout(() => {
                // Clean up generation visual
                if (secretGen) secretGen.style.display = 'none';
                const secretVisualEl = document.getElementById('secret-visual');
                if (secretVisualEl) secretVisualEl.textContent = '';
                updateFrameStatus('Shared secret ready ✓', 'alice');
                updateStepInfo('Step 3 Complete: Random shared secret generated!');
            }, 500);
        }, 900);
    } catch (error) {
        console.error('Error generating shared secret:', error);
        updateStepInfo('Error generating shared secret: ' + error.message);
    }
}

// Encrypt shared secret
async function encryptSharedSecret() {
    if (!isReady) {
        updateStepInfo('Error: Crypto system not ready yet. Please wait...');
        return;
    }
    if (!cryptoState.sharedSecret) {
        updateStepInfo('Error: Shared secret not generated yet. Please go back to Step 3 to generate it first.');
        return;
    }
    if (!cryptoState.recipient?.publicKey) {
        updateStepInfo('Error: Recipient public key not available. Please go back to Step 2 to generate keys first.');
        return;
    }
    
    try {
        // Clean up any existing visuals first
        cleanupAllVisuals();
        
        updateStepInfo('Step 4: Alice wraps the shared secret with ' + cryptoState.recipient.name + '\'s public key');
        updateFrameStatus('Wrapping with public key...', 'alice');
        
        const container = document.querySelector('.communication-frame');
        const containerWidth = container.offsetWidth;
        const centerY = 160;
        
        // Show shared secret box at Alice's position
        const wrappingVisual = document.getElementById('wrapping-visual');
        const secretBox = document.getElementById('secret-box');
        const publicKeyWrapper = document.getElementById('public-key-wrapper');
        
        wrappingVisual.style.display = 'block';
        wrappingVisual.style.left = '80px';
        wrappingVisual.style.top = (centerY - 40) + 'px';
        secretBox.style.display = 'block';
        publicKeyWrapper.style.display = 'none';
        
        // Show the secret first
        setTimeout(() => {
            // Safety check before accessing
            if (!cryptoState.sharedSecret) {
                console.error('Shared secret missing in encryptSharedSecret');
                updateStepInfo('Error: Shared secret is missing. Please go back to Step 3 to generate it.');
                return;
            }
            if (!cryptoState.recipient || !cryptoState.recipient.publicKey) {
                console.error('Public key missing in encryptSharedSecret:', cryptoState.recipient);
                updateStepInfo('Error: Recipient public key is missing. Please go back to Step 2 to generate keys.');
                return;
            }
            
            const sharedSecretJs = cryptoState.sharedSecret;
            const publicKeyJs = cryptoState.recipient.publicKey;
            
            // Show secret value in the box
            const secretValueDisplay = document.getElementById('secret-value-display');
            if (secretValueDisplay) {
                secretValueDisplay.textContent = sharedSecretJs.substring(0, 16) + '...';
            }
            
            // Animate wrapping - public key wrapper appears around secret
            setTimeout(() => {
                publicKeyWrapper.style.display = 'block';
                publicKeyWrapper.classList.add('wrapping');
                
                updateStepInfo('Step 4: The public key wrapper is closing around the secret...');
            }, 300);
            
            // Complete wrapping animation
            setTimeout(() => {
                updateStepInfo('Step 4: Secret is now wrapped! Ready to send securely.');
            }, 1300);
            
            // Encrypt
            setTimeout(async () => {
                // Double-check we have what we need
                if (!sharedSecretJs || !publicKeyJs) {
                    console.error('Missing data for encryption:', { sharedSecretJs: !!sharedSecretJs, publicKeyJs: !!publicKeyJs });
                    updateStepInfo('Error: Missing shared secret or public key for encryption. Please try going back and forward again.');
                    return;
                }
                
                const encrypted = await pyodide.runPythonAsync(`
import json
shared_secret = ${JSON.stringify(sharedSecretJs)}
public_key = ${JSON.stringify(publicKeyJs)}
result = crypto.encrypt_with_public_key(shared_secret, public_key)
result
                `);
                cryptoState.encryptedSecret = encrypted;
                
                // Update UI
                const encryptedData = JSON.parse(encrypted);
                document.getElementById('secret-plaintext').textContent = cryptoState.sharedSecret.substring(0, 32) + '...';
                document.getElementById('secret-encrypted').textContent = encryptedData.ciphertext.substring(0, 64) + '...';
                
                // Step 3 complete - wrapped secret is ready at Alice's position
                // DO NOT send it yet - that happens in Step 4
                updateStepInfo('Step 4 Complete: Secret is wrapped with ' + cryptoState.recipient.name + '\'s public key. Ready to send! Click Next Step to send it.');
                
                // Keep the wrapped box visible at Alice's position
                // It will be sent in the next step (Step 5)
                
            }, 1500);
            
        }, 300);
        
    } catch (error) {
        console.error('Error encrypting shared secret:', error);
        updateStepInfo('Error: Failed to encrypt shared secret. ' + (error.message || 'Please try again or go back to previous steps.'));
    }
}

// Send wrapped secret - Step 4: Clear visual message moving from Alice to Bob
function sendWrappedSecret() {
    if (!cryptoState.encryptedSecret) {
        updateStepInfo('Error: Wrapped secret not available. Please complete Step 4 (wrapping) first.');
        return;
    }
    
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const centerY = 160;
    const startX = 80; // Alice
    const endX = containerWidth - 140; // Bob
    
    // Clean up any other visuals
    cleanupAllVisuals();
    
    updateFrameStatus('Preparing to send...', 'alice');
    updateStepInfo('Step 5: Alice is preparing to send the wrapped secret to ' + cryptoState.recipient.name + '...');
    
    // Show the wrapped box at Alice's position first
    const wrappingVisual = document.getElementById('wrapping-visual');
    const secretBox = document.getElementById('secret-box');
    const publicKeyWrapper = document.getElementById('public-key-wrapper');
    
    wrappingVisual.style.display = 'block';
    wrappingVisual.style.left = startX + 'px';
    wrappingVisual.style.top = (centerY - 40) + 'px';
    wrappingVisual.style.zIndex = '30';
    wrappingVisual.style.transition = 'none';
    wrappingVisual.style.opacity = '1';
    
    if (secretBox) {
        secretBox.style.display = 'block';
        secretBox.style.opacity = '1';
    }
    if (publicKeyWrapper) {
        publicKeyWrapper.style.display = 'block';
        publicKeyWrapper.style.opacity = '1';
    }
    
    // Show it's wrapped
    const secretValueDisplay = document.getElementById('secret-value-display');
    if (secretValueDisplay) {
        secretValueDisplay.textContent = '🔒 Wrapped with Public Key';
    }
    
    // Wait, then create a message envelope that moves
    setTimeout(() => {
        updateFrameStatus('Sending wrapped secret...', 'alice');
        updateStepInfo('Step 5: Sending wrapped secret message from Alice to ' + cryptoState.recipient.name + '...');
        
        // Use the envelope element to show the message moving
        const envelope = document.getElementById('envelope-encrypted');
        envelope.style.display = 'flex';
        envelope.style.left = startX + 'px';
        envelope.style.top = (centerY - 20) + 'px';
        envelope.style.zIndex = '25';
        envelope.querySelector('.envelope-label').textContent = '🔑 Wrapped Secret';
        envelope.classList.add('glowing');
        
        // Also keep wrapped box visible for context
        wrappingVisual.style.opacity = '0.5'; // Fade it slightly to show envelope is the active item
        
        // Update the communication path to show the route
        const pathLine = document.getElementById('communication-path');
        pathLine.setAttribute('x1', startX);
        pathLine.setAttribute('y1', centerY);
        pathLine.setAttribute('x2', endX);
        pathLine.setAttribute('y2', centerY);
        
        // Start moving the envelope/message across
        setTimeout(() => {
            envelope.style.transition = 'left 3s ease-in-out, top 3s ease-in-out';
            envelope.style.left = endX + 'px';
        }, 300);
        
        // Message arrives at Bob
        setTimeout(() => {
            // Hide envelope
            envelope.style.display = 'none';
            envelope.classList.remove('glowing');
            envelope.style.transition = '';
            
            // Bob acknowledges receipt
            updateFrameStatus('Received! ✓', 'recipient');
            updateStepInfo('Step 5 Complete: ' + cryptoState.recipient.name + ' received the wrapped secret message!');
            
            // Show Bob's acknowledgment message
            const bobDisplay = document.getElementById('bob-message-display');
            if (bobDisplay) {
                bobDisplay.style.display = 'block';
                bobDisplay.style.position = 'absolute';
                bobDisplay.style.right = '20px';
                bobDisplay.style.top = '50px';
                bobDisplay.style.zIndex = '30';
                const bobText = document.getElementById('bob-message-text');
                if (bobText) bobText.textContent = 'Received! Message locked with my public key.';
                
                setTimeout(() => {
                    bobDisplay.style.display = 'none';
                }, 3000);
            }
            
            // Show wrapped box at Bob's position (ready for unwrapping)
            wrappingVisual.style.display = 'block';
            wrappingVisual.style.left = endX + 'px';
            wrappingVisual.style.top = (centerY - 40) + 'px';
            wrappingVisual.style.opacity = '1';
            wrappingVisual.style.zIndex = '30';
            
            // Update UI (only update if element exists - it's optional now)
            const encryptedData = JSON.parse(cryptoState.encryptedSecret);
            const secretEncryptedEl = document.getElementById('secret-encrypted');
            if (secretEncryptedEl) secretEncryptedEl.textContent = encryptedData.ciphertext.substring(0, 64) + '...';
            
            // Automatically progress to step 6
            setTimeout(() => {
                if (currentStep === 4) {
                    currentStep = 5;
                    showStep(5); // Move to step 6
                }
            }, 2000);
        }, 3400);
    }, 1000);
}

// Legacy function - kept for backward compatibility
function animateWrappedSecretSend(wrappingVisual, containerWidth, centerY) {
    sendWrappedSecret();
}

// Legacy function - kept for backward compatibility but now uses animateWrappedSecretSend
function animateEncryptedSecretSend() {
    // This is now handled by animateWrappedSecretSend
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const centerY = 160;
    const wrappingVisual = document.getElementById('wrapping-visual');
    
    if (wrappingVisual) {
        animateWrappedSecretSend(wrappingVisual, containerWidth, centerY);
    }
}

// Decrypt shared secret
async function decryptSharedSecret() {
    if (!isReady) {
        updateStepInfo('Error: System not ready. Please wait...');
        return;
    }
    
    // Wait a bit and check again if encrypted secret exists (in case step 4 is still completing)
    if (!cryptoState.encryptedSecret) {
        updateStepInfo('Waiting for wrapped secret to arrive from Step 4...');
        // Wait and check again after a short delay
        setTimeout(() => {
            if (cryptoState.encryptedSecret) {
                decryptSharedSecret();
            } else {
                updateStepInfo('Error: Encrypted secret not available. Please complete Step 4 first - make sure the wrapped secret is sent.');
            }
        }, 1000);
        return;
    }
    
    try {
        // Clean up any existing visuals first (but keep envelopes if needed)
        const secretGen = document.getElementById('secret-generation');
        if (secretGen) secretGen.style.display = 'none';
        const actionIndicator = document.getElementById('action-indicator');
        if (actionIndicator) actionIndicator.style.display = 'none';
        
        updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' received the wrapped secret from Alice.');
        updateFrameStatus('Ready to unwrap...', 'recipient');
        
        const container = document.querySelector('.communication-frame');
        const containerWidth = container.offsetWidth;
        const centerY = 160;
        
        // Show wrapped box at Bob's position (it should have just arrived from Alice)
        const wrappingVisual = document.getElementById('wrapping-visual');
        const secretBox = document.getElementById('secret-box');
        const publicKeyWrapper = document.getElementById('public-key-wrapper');
        
        // Make sure the wrapped box is visible at Bob's position (it should already be there from step 4)
        // But ensure it's visible if it got hidden
        wrappingVisual.style.display = 'block';
        wrappingVisual.style.left = (containerWidth - 140) + 'px';
        wrappingVisual.style.top = (centerY - 40) + 'px';
        wrappingVisual.style.zIndex = '30';
        wrappingVisual.style.opacity = '1';
        wrappingVisual.style.transition = 'none'; // Reset any transitions
        
        if (secretBox) {
            secretBox.style.display = 'block';
            secretBox.style.opacity = '1';
        }
        if (publicKeyWrapper) {
            publicKeyWrapper.style.display = 'block';
            publicKeyWrapper.style.opacity = '1';
        }
        
        // Show secret value as obscured (since it's still wrapped)
        const secretValueDisplay = document.getElementById('secret-value-display');
        if (secretValueDisplay) {
            secretValueDisplay.textContent = '🔒 Encrypted';
        }
        
        // Wait a moment to show the wrapped box, then start unwrapping
        setTimeout(() => {
            updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' retrieves his PRIVATE KEY to unlock the message...');
            updateFrameStatus('Retrieving private key...', 'recipient');
            
            // Show private key being retrieved/used
            const unwrappingVisual = document.getElementById('unwrapping-visual');
            unwrappingVisual.style.display = 'block';
            unwrappingVisual.style.left = (containerWidth - 140) + 'px';
            
            // Wait, then show unlocking
            setTimeout(() => {
                updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' is now using his PRIVATE KEY to unlock the message...');
                updateFrameStatus('Unlocking with private key...', 'recipient');
                
                // Animate the wrapper being removed
                publicKeyWrapper.classList.add('unwrapping');
                
                const encryptedDataJs = cryptoState.encryptedSecret;
                const privateKeyJs = cryptoState.recipient.privateKey;
                const publicKeyJs = cryptoState.recipient.publicKey;
                
                // Show decryption happening
                updateStepInfo('Step 6: ' + cryptoState.recipient.name + '\'s private key is removing the public key lock...');
            
                // Animate unwrapping - use async IIFE since we're in a setTimeout
                setTimeout(async () => {
                    const decrypted = await pyodide.runPythonAsync(`
encrypted_data = ${JSON.stringify(encryptedDataJs)}
private_key = ${JSON.stringify(privateKeyJs)}
public_key = ${JSON.stringify(publicKeyJs)}
crypto.decrypt_with_private_key(encrypted_data, private_key, public_key)
                    `);
                    
                    // Remove wrapper, show secret
                    setTimeout(() => {
                        // Wrapper disappears (unlocked!)
                        publicKeyWrapper.style.display = 'none';
                        publicKeyWrapper.classList.remove('unwrapping');
                        
                        // Show the unwrapped secret value (now revealed!)
                        if (secretValueDisplay) {
                            secretValueDisplay.textContent = decrypted.substring(0, 16) + '...';
                        }
                        
                        // Secret box sparkles to show it's now revealed
                        secretBox.classList.add('sparkling');
                        
                        // Hide unwrapping visual tool
                        unwrappingVisual.style.display = 'none';
                    
                    // Update UI elements (if they exist)
                    const encryptedData = JSON.parse(cryptoState.encryptedSecret);
                    const receivedEncrypted = document.getElementById('received-encrypted');
                    const recipientDecrypted = document.getElementById('recipient-decrypted');
                    if (receivedEncrypted) receivedEncrypted.textContent = encryptedData.ciphertext.substring(0, 64) + '...';
                    if (recipientDecrypted) recipientDecrypted.textContent = decrypted.substring(0, 32) + '...';
                    
                    // Update recipient names
                    const recipientName3 = document.getElementById('recipient-name-3');
                    const recipientName4 = document.getElementById('recipient-name-4-display');
                    const recipientName42 = document.getElementById('recipient-name-4-display2');
                    if (recipientName3) recipientName3.textContent = cryptoState.recipient.name;
                    if (recipientName4) recipientName4.textContent = cryptoState.recipient.name + ':';
                    if (recipientName42) recipientName42.textContent = cryptoState.recipient.name;
                    
                    updateFrameStatus('Secret unlocked and revealed! ✓', 'recipient');
                    updateStepInfo('Step 6: ✓ ' + cryptoState.recipient.name + ' successfully unlocked the message using his private key! The secret is now revealed!');
                    
                    // Hide wrapping visual after showing secret
                    setTimeout(() => {
                        wrappingVisual.style.display = 'none';
                        wrappingVisual.style.left = '';
                        wrappingVisual.style.top = '';
                        secretBox.style.display = 'none';
                        secretBox.classList.remove('sparkling');
                        publicKeyWrapper.style.display = 'none';
                        unwrappingVisual.style.display = 'none';
                        unwrappingVisual.style.left = '';
                    }, 2000);
                    
                    // Verify match and send acknowledgment from Bob to Alice
                    if (decrypted === cryptoState.sharedSecret) {
                        setTimeout(() => {
                            updateFrameStatus('Secret unlocked & ready! ✓', 'recipient');
                            updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' confirms the secret is correct! Now sending acknowledgment to Alice...');
                            
                            // Send acknowledgment message from Bob back to Alice (visual)
                            sendBobAcknowledgment();
                        }, 2500);
                        console.log('✓ Shared secrets match!');
                    } else {
                        updateStepInfo('Error: Decrypted secret does not match! Key exchange failed.');
                        console.error('✗ Shared secrets do not match!');
                    }
                }, 800);
                }, 1500); // Give time for wrapper animation to be visible
            }, 1000); // Time to show private key retrieval
        }, 1000); // Initial delay to show wrapped box before unwrapping
        
    } catch (error) {
        console.error('Error decrypting shared secret:', error);
    }
}

// Send Bob's acknowledgment message back to Alice (simple visual version for Step 6)
async function sendBobAcknowledgment() {
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const startX = containerWidth - 140; // Bob's position
    const endX = 80; // Alice's position
    const centerY = 160;
    
    try {
        // Encrypt acknowledgment message using shared secret
        const ackMessage = 'Got it! We now share the secret. Ready to communicate!';
        const sharedSecretJs = cryptoState.sharedSecret;
        const encrypted = await pyodide.runPythonAsync(`
message = ${JSON.stringify(ackMessage)}
shared_secret = ${JSON.stringify(sharedSecretJs)}
crypto.encrypt_symmetric(message, shared_secret)
        `);
        
        updateFrameStatus('Encrypting acknowledgment...', 'recipient');
        updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' encrypts an acknowledgment message using the shared secret...');
        
        // Wait a moment, then show envelope starting from Bob
        setTimeout(() => {
            const envelope = document.getElementById('envelope-acknowledgment');
            envelope.style.display = 'flex';
            envelope.style.left = startX + 'px';
            envelope.style.top = (centerY - 20) + 'px';
            envelope.style.zIndex = '25';
            envelope.querySelector('.envelope-label').textContent = '✅ Encrypted Acknowledgment';
            envelope.classList.add('glowing');
            
            updateFrameStatus('Sending acknowledgment...', 'recipient');
            updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' sends encrypted acknowledgment message to Alice...');
            
            // Update communication path
            const pathLine = document.getElementById('communication-path');
            pathLine.setAttribute('x1', startX);
            pathLine.setAttribute('y1', centerY);
            pathLine.setAttribute('x2', endX);
            pathLine.setAttribute('y2', centerY);
            
            // Animate envelope moving from Bob (right) to Alice (left)
            setTimeout(() => {
                envelope.style.transition = 'left 2.5s ease-in-out';
                envelope.style.left = endX + 'px';
            }, 300);
            
            // Envelope arrives at Alice
            setTimeout(async () => {
                envelope.style.display = 'none';
                envelope.classList.remove('glowing');
                envelope.style.transition = '';
                envelope.style.left = '';
                envelope.style.top = '';
                
                // Alice decrypts and displays the acknowledgment
                updateFrameStatus('Decrypting acknowledgment...', 'alice');
                updateStepInfo('Step 6: Alice decrypts ' + cryptoState.recipient.name + '\'s acknowledgment using the shared secret...');
                
                setTimeout(async () => {
                    const decrypted = await pyodide.runPythonAsync(`
encrypted_msg = ${JSON.stringify(encrypted)}
shared_secret = ${JSON.stringify(sharedSecretJs)}
crypto.decrypt_symmetric(encrypted_msg, shared_secret)
                    `);
                    
                    // Show Alice's message display with the decrypted acknowledgment
                    const aliceDisplay = document.getElementById('alice-message-display');
                    if (aliceDisplay) {
                        const aliceText = document.getElementById('alice-message-text');
                        const aliceEncrypted = document.getElementById('alice-message-encrypted');
                        if (aliceText) aliceText.textContent = decrypted;
                        if (aliceEncrypted) {
                            const encryptedData = JSON.parse(encrypted);
                            aliceEncrypted.textContent = encryptedData.ciphertext.substring(0, 48) + '...';
                        }
                        aliceDisplay.style.display = 'block';
                        aliceDisplay.style.left = '20px';
                        aliceDisplay.style.top = '50px';
                    }
                    
                    updateFrameStatus('Acknowledgment received ✓', 'alice');
                    updateFrameStatus('Key exchange complete! ✓', 'recipient');
                    updateStepInfo('✓ Key Exchange Complete! Both Alice and ' + cryptoState.recipient.name + ' now have the shared secret!');
                    
                    // Show success modal after a brief moment
                    setTimeout(() => {
                        showSuccessModal();
                    }, 1500);
                    
                }, 800);
            }, 2800);
        }, 1000);
        
    } catch (error) {
        console.error('Error sending acknowledgment:', error);
        updateStepInfo('Error sending acknowledgment. Key exchange still successful though!');
        // Still show success modal even if acknowledgment fails
        setTimeout(() => {
            showSuccessModal();
        }, 1000);
    }
}

// Show success modal after shared secret is established
function showSuccessModal() {
    const modal = document.getElementById('success-modal');
    const modalRecipientName = document.getElementById('modal-recipient-name');
    if (modal && modalRecipientName) {
        modalRecipientName.textContent = cryptoState.recipient.name;
        modal.style.display = 'flex';
        // Animate modal appearance
        setTimeout(() => {
            const modalContent = modal.querySelector('div > div');
            if (modalContent) {
                modalContent.style.transform = 'scale(1)';
                modalContent.style.opacity = '1';
            }
        }, 50);
    }
}

// Close success modal
function closeSuccessModal() {
    const modal = document.getElementById('success-modal');
    if (modal) {
        modal.style.display = 'none';
        // After closing modal, proceed directly to symmetric encryption demo
        setTimeout(() => {
            updateStepInfo('Key exchange complete! Both parties now have the shared secret! Proceeding to symmetric encryption demo...');
            // Move to Step 7 (symmetric communication)
            if (currentStep === 5) {
                currentStep = 6;
                showStep(6);
            }
        }, 500);
    }
}

// Animate Bob's acknowledgment message
function animateAcknowledgment() {
    // Clean up wrapping/unwrapping visuals first
    const wrappingVisual = document.getElementById('wrapping-visual');
    const secretBox = document.getElementById('secret-box');
    const publicKeyWrapper = document.getElementById('public-key-wrapper');
    const unwrappingVisual = document.getElementById('unwrapping-visual');
    if (wrappingVisual) wrappingVisual.style.display = 'none';
    if (secretBox) secretBox.style.display = 'none';
    if (publicKeyWrapper) publicKeyWrapper.style.display = 'none';
    if (unwrappingVisual) unwrappingVisual.style.display = 'none';
    
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const startX = containerWidth - 140; // Bob
    const endX = 80; // Alice
    const centerY = 160;
    
    updateFrameStatus('Encrypting acknowledgment...', 'recipient');
    updateStepInfo('Step 6: Bob encrypts an acknowledgment message using the shared secret');
    
    // First encrypt the acknowledgment message
    setTimeout(async () => {
        try {
            const ackMessage = 'Got it! We now share the secret. Ready to communicate securely!';
            const sharedSecretJs = cryptoState.sharedSecret;
            const encrypted = await pyodide.runPythonAsync(`
message = ${JSON.stringify(ackMessage)}
shared_secret = ${JSON.stringify(sharedSecretJs)}
crypto.encrypt_symmetric(message, shared_secret)
            `);
            
            // Show acknowledgment envelope from Bob to Alice
            const envelope = document.getElementById('envelope-acknowledgment');
            envelope.style.display = 'flex';
            envelope.style.left = startX + 'px';
            envelope.style.top = (centerY - 20) + 'px';
            envelope.querySelector('.envelope-label').textContent = '🔒 Encrypted';
            envelope.classList.add('glowing');
            
            updateFrameStatus('Sending encrypted acknowledgment...', 'recipient');
            updateStepInfo('Step 6: Bob sends encrypted acknowledgment message to Alice');
            
            // Animate envelope moving left (Bob → Alice)
            setTimeout(() => {
                envelope.style.transition = 'left 2s ease-in-out';
                envelope.style.left = endX + 'px';
            }, 300);
            
            // Envelope arrives at Alice
            setTimeout(async () => {
                envelope.style.display = 'none';
                envelope.classList.remove('glowing');
                // Clean up envelope
                envelope.style.transition = '';
                envelope.style.left = '';
                envelope.style.top = '';
                
                // Alice decrypts the acknowledgment
                updateFrameStatus('Decrypting acknowledgment...', 'alice');
                const sharedSecretForDecrypt = cryptoState.sharedSecret;
                const decrypted = await pyodide.runPythonAsync(`
encrypted_msg = ${JSON.stringify(encrypted)}
shared_secret = ${JSON.stringify(sharedSecretForDecrypt)}
crypto.decrypt_symmetric(encrypted_msg, shared_secret)
                `);
                
                setTimeout(() => {
                    // Update to step 5 (step 6 in UI) for acknowledgment
                    currentStep = 5;
                    showStep(5);
                    
                    updateFrameStatus('Acknowledgment received ✓', 'alice');
                    updateFrameStatus('Ready to communicate! ✓', 'recipient');
                    updateStepInfo('Step 6 Complete: ✓ Both parties confirmed! Now demonstrating symmetric-only encryption communication...');
                    
                    // Show success indicator
                    const secretBox = document.getElementById('secret-box');
                    if (secretBox) {
                        secretBox.style.display = 'block';
                        secretBox.style.position = 'absolute';
                        secretBox.style.left = '50%';
                        secretBox.style.top = '50%';
                        secretBox.style.transform = 'translate(-50%, -50%)';
                        secretBox.classList.add('sparkling');
                        secretBox.innerHTML = '<div class="text-white font-bold text-sm">✓ Shared Secret<br>Confirmed!</div>';
                        
                        setTimeout(() => {
                            secretBox.style.display = 'none';
                            secretBox.classList.remove('sparkling');
                            secretBox.style.position = '';
                            secretBox.style.left = '';
                            secretBox.style.top = '';
                            secretBox.style.transform = '';
                            secretBox.innerHTML = '<div class="text-sm text-white font-bold mb-1">🔒 Shared Secret</div><div id="secret-value-display" class="text-xs text-yellow-200 font-mono"></div>';
                            
                            // Start automatic symmetric encryption demonstration
                            setTimeout(() => {
                                startSymmetricCommunicationDemo();
                            }, 1000);
                        }, 3000);
                    }
                }, 500);
                
            }, 2400);
            
        } catch (error) {
            console.error('Error with acknowledgment:', error);
        }
    }, 1000);
}

// Start automatic symmetric encryption communication demonstration
let symmetricDemoActive = false;
let messageCounter = 0;

async function startSymmetricCommunicationDemo() {
    if (symmetricDemoActive) return;
    symmetricDemoActive = true;
    messageCounter = 0;
    
    updateStepInfo('💬 Starting symmetric encryption demo: Alice and ' + cryptoState.recipient.name + ' will exchange messages using only the shared secret!');
    
    // Wait a moment, then start with Alice sending first message
    setTimeout(() => {
        sendAutomaticMessage(true); // Alice sends first
    }, 2000);
}

// Send automatic message (Alice or Bob)
async function sendAutomaticMessage(isAlice) {
    if (!isReady || !cryptoState.sharedSecret || !symmetricDemoActive) return;
    
    const messages = {
        alice: [
            'Hello ' + cryptoState.recipient.name + '! Our shared secret is working perfectly!',
            'This symmetric encryption is much faster than using public keys for every message.',
            'Great! We can now communicate efficiently using our shared secret key.',
            'Symmetric encryption uses the same key for both encryption and decryption!'
        ],
        bob: [
            'Hi Alice! Yes, symmetric encryption is perfect for ongoing communication!',
            'Exactly! This is much more efficient than using asymmetric encryption for each message.',
            'Perfect! The shared secret makes our communication both secure and fast.',
            'This is how real-world secure communication works after the initial key exchange!'
        ]
    };
    
    const messageArray = isAlice ? messages.alice : messages.bob;
    const message = messageArray[messageCounter % messageArray.length];
    const senderName = isAlice ? 'Alice' : cryptoState.recipient.name;
    
    try {
        // Clean up any lingering visuals
        cleanupAllVisuals();
        
        const messageJs = message;
        const sharedSecretJs = cryptoState.sharedSecret;
        
        // Update step info
        updateStepInfo('🔐 ' + senderName + ' encrypts message using SHARED SECRET (symmetric encryption only)...');
        updateFrameStatus('Encrypting with shared secret...', isAlice ? 'alice' : 'recipient');
        
        // Show encryption indicator
        const actionIndicator = document.getElementById('action-indicator');
        const container = document.querySelector('.communication-frame');
        const containerWidth = container.offsetWidth;
        if (actionIndicator) {
            actionIndicator.style.display = 'block';
            if (isAlice) {
                actionIndicator.style.left = '80px';
            } else {
                actionIndicator.style.left = (containerWidth - 260) + 'px';
            }
            actionIndicator.style.transform = 'translateY(-50%)';
            actionIndicator.querySelector('div').textContent = '🔐 Encrypting with SHARED SECRET (symmetric)...';
        }
        
        // Encrypt message using symmetric encryption
        const encrypted = await pyodide.runPythonAsync(`
message = ${JSON.stringify(messageJs)}
shared_secret = ${JSON.stringify(sharedSecretJs)}
crypto.encrypt_symmetric(message, shared_secret)
        `);
        
        // Hide encryption indicator
        if (actionIndicator) actionIndicator.style.display = 'none';
        
        // Animate message being sent
        const direction = isAlice ? 'alice-to-bob' : 'bob-to-alice';
        animateMessageSend(message, encrypted, direction, true); // true = automatic mode
        
        // Update UI in step card
        if (isAlice) {
            document.getElementById('alice-message').textContent = message;
            document.getElementById('alice-encrypted-status').textContent = `🔒 Symmetric Encrypted: ${encrypted.substring(0, 35)}...`;
        } else {
            document.getElementById('recipient-message').textContent = message;
            document.getElementById('recipient-encrypted-status').textContent = `🔒 Symmetric Encrypted: ${encrypted.substring(0, 35)}...`;
        }
        
        messageCounter++;
        
        // After a few messages, stop the demo
        if (messageCounter >= 4) {
            setTimeout(() => {
                symmetricDemoActive = false;
                updateStepInfo('✓ Demo complete! Alice and ' + cryptoState.recipient.name + ' successfully communicated using symmetric encryption only.');
                updateFrameStatus('Demo complete! ✓', 'alice');
                updateFrameStatus('Demo complete! ✓', 'recipient');
            }, 3000);
        } else {
            // Schedule next message (other person responds)
            setTimeout(() => {
                sendAutomaticMessage(!isAlice);
            }, 4000);
        }
        
    } catch (error) {
        console.error('Error sending automatic message:', error);
        symmetricDemoActive = false;
    }
}


// Animate message being sent
function animateMessageSend(message, encrypted, direction, isAutomatic = false) {
    const container = document.querySelector('.communication-frame');
    const containerWidth = container.offsetWidth;
    const centerY = 160;
    
    // Determine start and end positions based on direction
    let startX, endX, recipientStatus, senderStatus;
    if (direction === 'alice-to-bob') {
        startX = 80; // Alice
        endX = containerWidth - 140; // Bob
        recipientStatus = 'recipient';
        senderStatus = 'alice';
    } else {
        // bob-to-alice
        startX = containerWidth - 140; // Bob
        endX = 80; // Alice
        recipientStatus = 'alice';
        senderStatus = 'recipient';
    }
    
    const messageBubble = document.getElementById('message-' + direction);
    messageBubble.style.display = 'flex';
    messageBubble.style.left = startX + 'px';
    messageBubble.style.top = (centerY - 25) + 'px';
    messageBubble.querySelector('.message-label').textContent = '🔒 Symmetric Encrypted';
    
    // Animate message moving
    setTimeout(() => {
        messageBubble.style.transition = 'left 2s ease-in-out';
        messageBubble.style.left = endX + 'px';
    }, 300);
    
    // Message arrives at recipient
    setTimeout(() => {
        messageBubble.style.display = 'none';
        // Clean up message bubble
        messageBubble.style.transition = '';
        messageBubble.style.left = '';
        messageBubble.style.top = '';
        updateFrameStatus('Message received!', recipientStatus);
        
        // Show decryption at recipient
        const actionIndicator = document.getElementById('action-indicator');
        if (actionIndicator) {
            actionIndicator.style.display = 'block';
            if (direction === 'alice-to-bob') {
                // Bob decrypts
                actionIndicator.style.left = (containerWidth - 260) + 'px';
            } else {
                // Alice decrypts
                actionIndicator.style.left = '80px';
            }
            actionIndicator.style.transform = 'translateY(-50%)';
            actionIndicator.querySelector('div').textContent = '🔓 Decrypting with SHARED SECRET (symmetric)...';
        }
        
        // Decrypt and display message
        setTimeout(async () => {
            try {
                const decrypted = await pyodide.runPythonAsync(`
encrypted_msg = ${JSON.stringify(encrypted)}
shared_secret = ${JSON.stringify(cryptoState.sharedSecret)}
crypto.decrypt_symmetric(encrypted_msg, shared_secret)
                `);
                
                if (direction === 'alice-to-bob') {
                    // Show Bob's message display
                    const bobDisplay = document.getElementById('bob-message-display');
                    const bobText = document.getElementById('bob-message-text');
                    const bobEncrypted = document.getElementById('bob-message-encrypted');
                    if (bobDisplay && bobText && bobEncrypted) {
                        document.getElementById('bob-message-name').textContent = cryptoState.recipient.name;
                        bobText.textContent = decrypted;
                        bobEncrypted.textContent = 'Symmetric Decrypted: ' + encrypted.substring(0, 30) + '...';
                        bobDisplay.style.display = 'block';
                        bobDisplay.classList.add('message-display-animate');
                        
                        // Hide after showing
                        setTimeout(() => {
                            bobDisplay.style.display = 'none';
                        }, 2000);
                    }
                    
                    if (actionIndicator) actionIndicator.style.display = 'none';
                    updateFrameStatus('Decrypted with shared secret ✓', 'recipient');
                    
                    if (isAutomatic) {
                        updateStepInfo('✓ ' + cryptoState.recipient.name + ' decrypted message using SHARED SECRET (symmetric encryption only - no public/private keys needed!)');
                    } else {
                        updateStepInfo('Message successfully decrypted! ' + cryptoState.recipient.name + ' can read it.');
                        // Bob responds after a delay (only in manual mode)
                        setTimeout(() => {
                            animateBobResponse(message);
                        }, 2000);
                    }
                } else {
                    // Show Alice's received message display
                    const aliceDisplay = document.getElementById('alice-message-display');
                    const aliceText = document.getElementById('alice-message-text');
                    if (aliceDisplay && aliceText) {
                        aliceText.textContent = decrypted;
                        aliceDisplay.style.display = 'block';
                        aliceDisplay.classList.add('message-display-animate');
                        
                        // Hide after showing
                        setTimeout(() => {
                            aliceDisplay.style.display = 'none';
                        }, 2000);
                    }
                    
                    if (actionIndicator) actionIndicator.style.display = 'none';
                    updateFrameStatus('Decrypted with shared secret ✓', 'alice');
                    
                    if (isAutomatic) {
                        updateStepInfo('✓ Alice decrypted message using SHARED SECRET (symmetric encryption only - no public/private keys needed!)');
                    } else {
                        updateStepInfo(cryptoState.recipient.name + '\'s message decrypted successfully!');
                    }
                }
                
            } catch (error) {
                console.error('Error decrypting message:', error);
            }
        }, 500);
        
    }, 2400);
}

// Animate Bob's response
async function animateBobResponse(originalMessage) {
    // Clean up any lingering visuals before Bob responds
    const secretBox = document.getElementById('secret-box');
    const wrappingVisual = document.getElementById('wrapping-visual');
    const unwrappingVisual = document.getElementById('unwrapping-visual');
    const publicKeyWrapper = document.getElementById('public-key-wrapper');
    if (secretBox) secretBox.style.display = 'none';
    if (wrappingVisual) wrappingVisual.style.display = 'none';
    if (unwrappingVisual) unwrappingVisual.style.display = 'none';
    if (publicKeyWrapper) publicKeyWrapper.style.display = 'none';
    
    const responses = [
        `Hi Alice! I received: "${originalMessage.substring(0, 20)}${originalMessage.length > 20 ? '...' : ''}". All good!`,
        `Thanks Alice! Encryption working perfectly.`,
        `Message received and decrypted successfully!`
    ];
    const response = responses[Math.floor(Math.random() * responses.length)];
    
    try {
        updateFrameStatus('Encrypting response...', 'recipient');
        
        // Show encryption at Bob
        const actionIndicator = document.getElementById('action-indicator');
        const container = document.querySelector('.communication-frame');
        const containerWidth = container.offsetWidth;
        
        if (actionIndicator) {
            actionIndicator.style.display = 'block';
            actionIndicator.style.left = (containerWidth - 260) + 'px';
            actionIndicator.style.transform = 'translateY(-50%)';
            actionIndicator.querySelector('div').textContent = '🔐 Encrypting response...';
        }
        
        const encrypted = await pyodide.runPythonAsync(`
response = ${JSON.stringify(response)}
shared_secret = ${JSON.stringify(cryptoState.sharedSecret)}
crypto.encrypt_symmetric(response, shared_secret)
        `);
        
        if (actionIndicator) actionIndicator.style.display = 'none';
        
        // Animate response message from Bob to Alice (starts at Bob, goes to Alice)
        setTimeout(() => {
            animateMessageSend(response, encrypted, 'bob-to-alice');
        }, 300);
        
        // Update UI
        document.getElementById('recipient-message').textContent = response;
        document.getElementById('recipient-encrypted-status').textContent = `Encrypted: ${encrypted.substring(0, 40)}...`;
        
        // Show Alice receiving and decrypting
        setTimeout(async () => {
            try {
                const decrypted = await pyodide.runPythonAsync(`
encrypted_msg = ${JSON.stringify(encrypted)}
shared_secret = ${JSON.stringify(cryptoState.sharedSecret)}
crypto.decrypt_symmetric(encrypted_msg, shared_secret)
                `);
                
                // Show Alice's message display
                const aliceDisplay = document.getElementById('alice-message-display');
                const aliceText = document.getElementById('alice-message-text');
                const aliceEncrypted = document.getElementById('alice-message-encrypted');
                
                aliceText.textContent = decrypted;
                aliceEncrypted.textContent = 'Encrypted: ' + encrypted.substring(0, 30) + '...';
                aliceDisplay.style.display = 'block';
                aliceDisplay.classList.add('message-display-animate');
                
                updateFrameStatus('Response received & decrypted ✓', 'alice');
                updateStepInfo('✓ Complete! Both parties can now communicate securely using the shared secret!');
                
            } catch (error) {
                console.error('Error decrypting response:', error);
            }
        }, 2700);
        
    } catch (error) {
        console.error('Error sending response:', error);
    }
}

// Navigation
function showStep(step) {
    // Clean up all visuals when changing steps (except when we're in the middle of animations)
    // Only clean up if we're starting fresh steps
    if (step === 0 || step === 1) {
        cleanupAllVisuals();
    }
    
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
            indicator.classList.add('bg-purple-600', 'text-white');
        } else {
            indicator.classList.remove('bg-purple-600', 'text-white');
            indicator.classList.add('bg-gray-600', 'text-gray-300');
        }
    });
    
    // Execute step-specific actions
    if (step === 1) {
        updateStepInfo('Step 2: Starting key generation...');
        generateKeys();
    } else if (step === 2) {
        updateStepInfo('Step 3: Generating shared secret...');
        generateSharedSecret();
    } else if (step === 3) {
        // Step 4: Wrap shared secret - always trigger this automatically
        updateStepInfo('Step 4: Checking prerequisites...');
        
        // Wait a moment for any async operations to complete, then check
        setTimeout(() => {
            // Check if prerequisites are available
            const hasSharedSecret = cryptoState.sharedSecret && cryptoState.sharedSecret.length > 0;
            const hasPublicKey = cryptoState.recipient && cryptoState.recipient.publicKey && cryptoState.recipient.publicKey.length > 0;
            
            console.log('Step 3 prerequisites check:', {
                hasSharedSecret,
                hasPublicKey,
                sharedSecret: cryptoState.sharedSecret ? cryptoState.sharedSecret.substring(0, 20) + '...' : 'missing',
                publicKey: cryptoState.recipient?.publicKey ? cryptoState.recipient.publicKey.substring(0, 20) + '...' : 'missing',
                recipient: cryptoState.recipient
            });
            
            if (hasSharedSecret && hasPublicKey) {
                updateStepInfo('Step 4: Wrapping shared secret with public key...');
                encryptSharedSecret();
            } else {
                // Provide detailed error message
                let errorMsg = 'Error: Missing prerequisites. ';
                if (!hasSharedSecret) {
                    errorMsg += 'Shared secret not generated. ';
                }
                if (!hasPublicKey) {
                    errorMsg += 'Recipient public key not available. ';
                }
                errorMsg += 'Please go back to previous steps to complete key generation and secret generation.';
                updateStepInfo(errorMsg);
                console.error('Prerequisites missing:', { hasSharedSecret, hasPublicKey, cryptoState });
            }
        }, 300); // Small delay to ensure async operations complete
    } else if (step === 4) {
        // Step 5: Send wrapped secret to recipient
        // Update recipient name in step card
        const sendRecipientName = document.getElementById('send-recipient-name');
        if (sendRecipientName) sendRecipientName.textContent = cryptoState.recipient.name;
        
        if (cryptoState.encryptedSecret) {
            // Wrapped secret is ready, send it
            updateStepInfo('Step 5: Sending wrapped secret...');
            sendWrappedSecret();
        } else if (cryptoState.sharedSecret && cryptoState.recipient.publicKey) {
            // Wrapping hasn't completed yet - trigger it now
            updateStepInfo('Step 5: Wrapping secret first, then sending...');
            encryptSharedSecret();
            // Wait for wrapping to complete, then send
            setTimeout(() => {
                let checkCount = 0;
                const checkWrapped = setInterval(() => {
                    checkCount++;
                    if (cryptoState.encryptedSecret) {
                        clearInterval(checkWrapped);
                        if (currentStep === 4) {
                            sendWrappedSecret();
                        }
                    } else if (checkCount > 15) { // 15 checks = ~3 seconds
                        clearInterval(checkWrapped);
                        updateStepInfo('Error: Wrapping taking too long. Please try again or go back to Step 4.');
                    }
                }, 200);
            }, 500);
        } else {
            // Prerequisites might not be ready yet - check again or suggest going back
            updateStepInfo('Waiting for prerequisites... Checking if we can wrap the secret...');
            // Check if prerequisites become available (might be async)
            setTimeout(() => {
                if (cryptoState.sharedSecret && cryptoState.recipient?.publicKey) {
                    // Prerequisites are now available - trigger wrapping
                    updateStepInfo('Step 5: Wrapping secret first, then sending...');
                    encryptSharedSecret();
                    // Wait for wrapping to complete, then send
                    setTimeout(() => {
                        let checkCount = 0;
                        const checkWrapped = setInterval(() => {
                            checkCount++;
                            if (cryptoState.encryptedSecret) {
                                clearInterval(checkWrapped);
                                if (currentStep === 4) {
                                    sendWrappedSecret();
                                }
                            } else if (checkCount > 15) {
                                clearInterval(checkWrapped);
                                updateStepInfo('Error: Wrapping taking too long. Please go back to Step 4 and try again.');
                            }
                        }, 200);
                    }, 500);
                } else {
                    // Prerequisites truly missing - need to go back
                    updateStepInfo('Missing required data. Please use the Previous button to go back to Step 4 (Wrap Shared Secret) to complete wrapping first.');
                }
            }, 500);
        }
    } else if (step === 5) {
        // Step 6: Bob unwraps with private key
        // Update recipient name in step card
        const unlockRecipientName = document.getElementById('unlock-recipient-name');
        if (unlockRecipientName) unlockRecipientName.textContent = cryptoState.recipient.name;
        
        if (cryptoState.encryptedSecret) {
            updateStepInfo('Step 6: ' + cryptoState.recipient.name + ' will unlock the message...');
            decryptSharedSecret();
        } else {
            updateStepInfo('Waiting for wrapped secret to arrive... Please complete Step 5 first.');
            setTimeout(() => {
                if (cryptoState.encryptedSecret && currentStep === 5) {
                    decryptSharedSecret();
                }
            }, 2000);
        }
    } else if (step === 6) {
        // Step 7: Symmetric encryption demo
        updateStepInfo('Step 7: Symmetric encryption communication demo');
        if (cryptoState.sharedSecret && !symmetricDemoActive) {
            setTimeout(() => {
                startSymmetricCommunicationDemo();
            }, 1000);
        }
    }
    
    // Update navigation buttons
    document.getElementById('prev-btn').disabled = step === 0;
    if (step === 0) {
        document.getElementById('prev-btn').classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        document.getElementById('prev-btn').classList.remove('opacity-50', 'cursor-not-allowed');
    }
    
    // Next button disabled on last step
    const nextBtn = document.getElementById('next-btn');
    if (step >= 6) {
        // Step 6 (step 7 in UI) is the final step - disable next button
        nextBtn.disabled = true;
        nextBtn.classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        nextBtn.disabled = false;
        nextBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

function nextStep() {
    if (currentStep < 6) {
        // Remove pulse animation from button if present
        const nextBtn = document.getElementById('next-btn');
        nextBtn.classList.remove('animate-pulse');
        
        // Store current scroll position to prevent jumping
        const scrollY = window.scrollY;
        
        currentStep++;
        showStep(currentStep);
        
        // Restore scroll position to prevent jumping
        requestAnimationFrame(() => {
            window.scrollTo(0, scrollY);
        });
    }
}

function previousStep() {
    if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    initPyodide();
    showStep(0);
});

// No longer need message input handlers - messages are auto-generated

