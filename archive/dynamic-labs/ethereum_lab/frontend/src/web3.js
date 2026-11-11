import { ethers } from "ethers";
import { resolveRpcUrl } from "./lib/RpcClient";
import {
    addSessionWallet,
    fetchSessionState,
    setSessionActiveWallet,
} from "./lib/sessionState";

const DEFAULT_CHAIN_ID = 31337;

const createLabProvider = (url = "/rpc-write") => {
    const network = ethers.Network.from(DEFAULT_CHAIN_ID);
    return new ethers.JsonRpcProvider(resolveRpcUrl(url), network, { staticNetwork: network });
};

let walletCache = {
    loaded: false,
    wallets: [],
    activeId: null,
};
let hydratePromise = null;

function publicWallet(wallet) {
    if (!wallet) return null;
    return {
        id: wallet.id,
        address: wallet.address,
        nickname: wallet.nickname || "My Wallet",
    };
}

function normalizeWalletsDoc(doc = {}) {
    const wallets = Array.isArray(doc.wallets) ? doc.wallets : [];
    const activeId = doc.activeId || wallets[0]?.id || null;
    walletCache = { loaded: true, wallets, activeId };
    return walletCache;
}

function activeWalletRecord() {
    const active = walletCache.wallets.find((item) => item.id === walletCache.activeId) || walletCache.wallets[0];
    return active || null;
}

export async function hydrateSessionWallets({ force = false } = {}) {
    if (walletCache.loaded && !force) return walletCache;
    if (!hydratePromise || force) {
        hydratePromise = fetchSessionState()
            .then((data) => normalizeWalletsDoc(data?.state?.wallets || {}))
            .finally(() => { hydratePromise = null; });
    }
    return hydratePromise;
}

export function applySessionWalletState(walletsDoc = {}) {
    return normalizeWalletsDoc(walletsDoc);
}

export function getWalletList() {
    return walletCache.wallets.map(publicWallet).filter(Boolean);
}

export async function setActiveWallet(id) {
    const result = await setSessionActiveWallet(id);
    normalizeWalletsDoc(result.wallets || {});
    window.dispatchEvent(new CustomEvent("walletSwitched"));
    return true;
}

export async function addWallet(privateKey, nickname = "Imported") {
    const wallet = new ethers.Wallet(privateKey);
    const result = await addSessionWallet({
        privateKey,
        address: wallet.address,
        nickname,
        source: "user",
    });
    normalizeWalletsDoc(result.wallets || {});
    window.dispatchEvent(new CustomEvent("walletSwitched"));
    return { success: true, id: walletCache.activeId, address: wallet.address };
}

export async function removeWallet() {
    throw new Error("Wallet removal is not available in backend session mode. Reset the session instead.");
}

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

export const getGuestWallet = async () => {
    await hydrateSessionWallets();
    let active = activeWalletRecord();
    if (!active) {
        const wallet = ethers.Wallet.createRandom();
        await addWallet(wallet.privateKey, "My Wallet");
        active = activeWalletRecord();
    }
    if (!active?.privateKey) {
        throw new Error("Session wallet is missing a private key.");
    }
    const wallet = new ethers.Wallet(active.privateKey);
    return { mode: 'guest', signer: wallet };
};

export const getStoredWalletAddress = () => {
    const info = getWalletInfo();
    return info ? info.address : null;
};

export const resetWallet = async () => {
    const wallet = ethers.Wallet.createRandom();
    await addWallet(wallet.privateKey, "My Wallet");
    window.dispatchEvent(new CustomEvent("walletSwitched"));
};

export const exportWalletKey = () => {
    const info = getWalletInfo();
    if (!info) {
        console.warn("[Wallet] No wallet found to export");
        return null;
    }
    console.warn("[Wallet] SECURITY WARNING: Never share your private key!");
    return info.privateKey;
};

export const importWallet = async (privateKey, nickname = null) => {
    try {
        const result = await addWallet(privateKey, nickname || "Imported Wallet");
        return { success: true, address: result.address };
    } catch (e) {
        return { success: false, error: e.message || "Invalid private key" };
    }
};

export const getWalletNickname = () => {
    const info = getWalletInfo();
    return info ? info.nickname : "My Wallet";
};

export const setWalletNickname = async (nickname) => {
    const active = activeWalletRecord();
    if (!active) return false;
    await addWallet(active.privateKey, nickname || "My Wallet");
    return true;
};

export const generateNewWallet = async (nickname = 'My Wallet') => {
    const wallet = ethers.Wallet.createRandom();
    await addWallet(wallet.privateKey, nickname);
    console.log("[Wallet] Generated new wallet:", wallet.address);
    return {
        address: wallet.address,
        privateKey: wallet.privateKey,
        nickname,
    };
};

export const getWalletInfo = () => {
    const active = activeWalletRecord();
    if (!active?.privateKey) return null;
    try {
        const wallet = new ethers.Wallet(active.privateKey);
        return {
            id: active.id,
            address: wallet.address,
            privateKey: active.privateKey,
            nickname: active.nickname || "My Wallet",
        };
    } catch {
        return null;
    }
};

export const checkNodeStatus = async (customUrl = null) => {
    const targetProvider = createLabProvider(customUrl || "/rpc-write");
    try {
        const network = await targetProvider.getNetwork();
        const blockNumber = await targetProvider.getBlockNumber();
        return {
            connected: true,
            chainId: network.chainId.toString(),
            blockNumber,
        };
    } catch (error) {
        return { connected: false, error: error.message };
    } finally {
        targetProvider.destroy?.();
    }
};
