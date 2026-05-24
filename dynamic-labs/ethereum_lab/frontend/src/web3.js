import { ethers } from "ethers";
import { resolveRpcUrl } from "./lib/RpcClient";

// Setup provider connecting to the local blockchain node
// We use resolveRpcUrl('/rpc') to automatically route through the Vite BASE_URL proxy
export const provider = new ethers.JsonRpcProvider(resolveRpcUrl("/rpc"));

// Storage keys for wallet persistence
const WALLET_STORAGE_KEY = "eth_lab_wallet_pk";
const WALLET_NICKNAME_KEY = "eth_lab_wallet_nickname";
const WALLETS_LIST_KEY = "eth_lab_wallets";
const ACTIVE_WALLET_ID_KEY = "eth_lab_active_wallet_id";

// --- MIGRATION: legacy single-wallet to multi-wallet ---
function migrateToMultiWallet() {
    const list = localStorage.getItem(WALLETS_LIST_KEY);
    if (list) return; // Already migrated
    
    const legacyPk = localStorage.getItem(WALLET_STORAGE_KEY) || sessionStorage.getItem("guest_sk");
    const legacyNick = localStorage.getItem(WALLET_NICKNAME_KEY) || "My Wallet";
    
    if (legacyPk) {
        try {
            const wallet = new ethers.Wallet(legacyPk);
            const id = "w_" + Date.now();
            const wallets = [{ id, address: wallet.address, nickname: legacyNick, privateKey: legacyPk }];
            localStorage.setItem(WALLETS_LIST_KEY, JSON.stringify(wallets));
            localStorage.setItem(ACTIVE_WALLET_ID_KEY, id);
        } catch (e) {
            console.warn("[Wallet] Migration failed:", e);
        }
    }
}

// --- MULTI-WALLET API ---
export function getWalletList() {
    migrateToMultiWallet();
    try {
        const raw = localStorage.getItem(WALLETS_LIST_KEY);
        const list = raw ? JSON.parse(raw) : [];
        return list.map(({ id, address, nickname }) => ({ id, address, nickname }));
    } catch {
        return [];
    }
}

export function setActiveWallet(id) {
    const list = getWalletListFull();
    if (!list.find((w) => w.id === id)) return false;
    localStorage.setItem(ACTIVE_WALLET_ID_KEY, id);
    sessionStorage.setItem("guest_sk", list.find((w) => w.id === id).privateKey);
    window.dispatchEvent(new CustomEvent("walletSwitched"));
    return true;
}

function getWalletListFull() {
    migrateToMultiWallet();
    try {
        const raw = localStorage.getItem(WALLETS_LIST_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

export function addWallet(privateKey, nickname = "Imported") {
    try {
        const wallet = new ethers.Wallet(privateKey);
        const list = getWalletListFull();
        const existing = list.find((w) => w.address.toLowerCase() === wallet.address.toLowerCase());
        if (existing) return { success: true, id: existing.id, address: wallet.address };
        
        const id = "w_" + Date.now();
        list.push({ id, address: wallet.address, nickname, privateKey });
        localStorage.setItem(WALLETS_LIST_KEY, JSON.stringify(list));
        localStorage.setItem(ACTIVE_WALLET_ID_KEY, id);
        sessionStorage.setItem("guest_sk", privateKey);
        return { success: true, id, address: wallet.address };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

export function removeWallet(id) {
    const list = getWalletListFull().filter((w) => w.id !== id);
    const activeId = localStorage.getItem(ACTIVE_WALLET_ID_KEY);
    if (activeId === id && list.length > 0) {
        localStorage.setItem(ACTIVE_WALLET_ID_KEY, list[0].id);
        sessionStorage.setItem("guest_sk", list[0].privateKey);
    } else if (list.length === 0) {
        localStorage.removeItem(ACTIVE_WALLET_ID_KEY);
        sessionStorage.removeItem("guest_sk");
    }
    localStorage.setItem(WALLETS_LIST_KEY, JSON.stringify(list));
    window.dispatchEvent(new CustomEvent("walletSwitched"));
}

// --- METAMASK CONNECTION ---
export const connectWallet = async () => {
  if (window.ethereum) {
    try {
      const browserProvider = new ethers.BrowserProvider(window.ethereum);
      const signer = await browserProvider.getSigner();
      return { mode: 'metamask', signer };
    } catch (error) {
      console.error("User rejected connection", error);
      throw error;
    }
  } else {
    throw new Error("MetaMask not found");
  }
};

// --- BURNER / GUEST WALLET ---
// Persists across browser sessions using localStorage; uses active wallet from multi-wallet list
export const getGuestWallet = () => {
    migrateToMultiWallet();
    let privateKey = sessionStorage.getItem("guest_sk");
    if (!privateKey) {
        const activeId = localStorage.getItem(ACTIVE_WALLET_ID_KEY);
        const list = getWalletListFull();
        const active = list.find((w) => w.id === activeId) || list[0];
        if (active) {
            privateKey = active.privateKey;
            sessionStorage.setItem("guest_sk", privateKey);
        }
    }
    if (!privateKey) {
        const wallet = ethers.Wallet.createRandom();
        privateKey = wallet.privateKey;
        addWallet(privateKey, "My Wallet");
        console.log("[Wallet] Created new wallet:", wallet.address);
    }
    const wallet = new ethers.Wallet(privateKey, provider);
    return { mode: 'guest', signer: wallet };
}

// Get existing wallet address without creating new one
export const getStoredWalletAddress = () => {
    const info = getWalletInfo();
    return info ? info.address : null;
}

// Reset wallet - creates a new identity (legacy; now adds new wallet and switches)
export const resetWallet = () => {
    const list = getWalletListFull();
    if (list.length > 0) {
        const activeId = localStorage.getItem(ACTIVE_WALLET_ID_KEY);
        const others = list.filter((w) => w.id !== activeId);
        if (others.length > 0) {
            localStorage.setItem(ACTIVE_WALLET_ID_KEY, others[0].id);
            sessionStorage.setItem("guest_sk", others[0].privateKey);
        } else {
            localStorage.removeItem(ACTIVE_WALLET_ID_KEY);
            sessionStorage.removeItem("guest_sk");
        }
        localStorage.setItem(WALLETS_LIST_KEY, JSON.stringify(others));
    } else {
        localStorage.removeItem(WALLETS_LIST_KEY);
        localStorage.removeItem(ACTIVE_WALLET_ID_KEY);
        sessionStorage.removeItem("guest_sk");
    }
    window.dispatchEvent(new CustomEvent("walletSwitched"));
    console.log("[Wallet] Wallet reset");
}

// Export wallet private key (for backup purposes - warn user!)
export const exportWalletKey = () => {
    const info = getWalletInfo();
    if (!info) {
        console.warn("[Wallet] No wallet found to export");
        return null;
    }
    console.warn("[Wallet] SECURITY WARNING: Never share your private key!");
    return info.privateKey;
}

// Import wallet from private key - adds to list and sets as active
export const importWallet = (privateKey, nickname = null) => {
    const result = addWallet(privateKey, nickname || "Imported Wallet");
    if (result.success) {
        console.log("[Wallet] Imported wallet:", result.address);
        return { success: true, address: result.address };
    }
    return { success: false, error: result.error || "Invalid private key" };
}

// Get wallet nickname (of active wallet)
export const getWalletNickname = () => {
    const info = getWalletInfo();
    return info ? info.nickname : "My Wallet";
}

// Set wallet nickname (of active wallet)
export const setWalletNickname = (nickname) => {
    const activeId = localStorage.getItem(ACTIVE_WALLET_ID_KEY);
    const list = getWalletListFull();
    const idx = list.findIndex((w) => w.id === activeId);
    if (idx >= 0) {
        list[idx].nickname = nickname;
        localStorage.setItem(WALLETS_LIST_KEY, JSON.stringify(list));
    }
}

// Generate a new wallet - adds to list and sets as active
export const generateNewWallet = (nickname = 'My Wallet') => {
    const wallet = ethers.Wallet.createRandom();
    const result = addWallet(wallet.privateKey, nickname);
    console.log("[Wallet] Generated new wallet:", wallet.address);
    return {
        address: wallet.address,
        privateKey: wallet.privateKey,
        nickname: nickname
    };
}

// Get full wallet info (of active wallet)
export const getWalletInfo = () => {
    migrateToMultiWallet();
    const activeId = localStorage.getItem(ACTIVE_WALLET_ID_KEY);
    const list = getWalletListFull();
    const active = list.find((w) => w.id === activeId) || list[0];
    if (!active) return null;
    try {
        const wallet = new ethers.Wallet(active.privateKey);
        return {
            address: wallet.address,
            privateKey: active.privateKey,
            nickname: active.nickname || "My Wallet"
        };
    } catch {
        return null;
    }
}

// Helper to check if local node is alive
export const checkNodeStatus = async (customUrl = null) => {
    const targetProvider = customUrl 
        ? new ethers.JsonRpcProvider(resolveRpcUrl(customUrl)) 
        : provider;
    
    try {
        const network = await targetProvider.getNetwork();
        const blockNumber = await targetProvider.getBlockNumber();
        return {
            connected: true,
            chainId: network.chainId.toString(),
            blockNumber: blockNumber
        };
    } catch (error) {
        return { connected: false, error: error.message };
    }
};

