const fs = require("fs");
const path = require("path");

const themes = [
  ["mempool-storms", "Mempool Storms", "Chaotic pending transactions visualized as electrical weather."],
  ["gas-relics", "Gas Relics", "Ancient artifacts powered by fluctuating gas fees."],
  ["validator-badges", "Validator Badges", "Emblems, medals, or identity marks for fictional validators."],
  ["block-fossils", "Block Fossils", "Excavated blocks preserved like prehistoric specimens."],
  ["calldata-glyphs", "Calldata Glyphs", "Abstract symbols formed from transaction input data."],
  ["nonce-keys", "Nonce Keys", "Mystical keys representing ordered account actions."],
  ["fork-artifacts", "Fork Artifacts", "Objects split into parallel versions after a chain fork."],
  ["receipt-scrolls", "Receipt Scrolls", "Transaction receipts rendered as illuminated proof documents."],
  ["event-echoes", "Event Echoes", "Visual traces of emitted smart contract events."],
  ["topic-hash-totems", "Topic Hash Totems", "Monuments built from event topic hashes."],
  ["rollup-cities", "Rollup Cities", "Layer-2 cities compressing activity into dense skylines."],
  ["bridge-portals", "Bridge Portals", "Gateways representing cross-chain movement."],
  ["merkle-trees", "Merkle Trees", "Cryptographic trees as living, geometric structures."],
  ["state-roots", "State Roots", "Crystalline roots anchoring the current blockchain state."],
  ["storage-slots", "Storage Slots", "Vaults, drawers, or memory cells holding contract state."],
  ["smart-contract-blueprints", "Smart Contract Blueprints", "Architectural diagrams of fictional on-chain machines."],
  ["minting-forges", "Minting Forges", "Foundries where unique tokens are created."],
  ["transfer-trails", "Transfer Trails", "Glowing paths showing ownership moving between addresses."],
  ["approval-seals", "Approval Seals", "Stamped permissions authorizing another account to act."],
  ["escrow-chambers", "Escrow Chambers", "Secure rooms where NFTs and ETH wait for atomic exchange."],
  ["payable-gates", "Payable Gates", "Contract doors that open only when ETH is sent."],
  ["revert-posters", "Revert Posters", "Stylized warning posters for failed transactions."],
  ["gas-limit-engines", "Gas Limit Engines", "Machines that consume gas to complete computation."],
  ["pending-transaction-lanterns", "Pending Transaction Lanterns", "Floating lights waiting to be included in a block."],
  ["miners-archive", "Miner's Archive", "Historical nod to proof-of-work block production."],
  ["beacon-chain-signals", "Beacon Chain Signals", "Beacons, towers, or signals representing proof-of-stake consensus."],
  ["epoch-clocks", "Epoch Clocks", "Timepieces tracking validator epochs and slots."],
  ["block-builder-workshops", "Block Builder Workshops", "Fictional workshops assembling blocks from transactions."],
  ["execution-layer-maps", "Execution Layer Maps", "Terrain maps showing where contract execution changes state."],
  ["address-masks", "Address Masks", "Identity masks based on wallet addresses."],
  ["wallet-sigils", "Wallet Sigils", "Personal symbols derived from account ownership."],
  ["signature-runes", "Signature Runes", "Cryptographic signatures as engraved magical marks."],
  ["token-vaults", "Token Vaults", "Secure displays for unique ERC-721 assets."],
  ["metadata-capsules", "Metadata Capsules", "Containers holding JSON, names, descriptions, and image links."],
  ["uri-beacons", "URI Beacons", "Signals pointing from tokens to their metadata."],
  ["explorer-windows", "Explorer Windows", "Visualized blockchain explorer panels as artifacts."],
  ["contract-creatures", "Contract Creatures", "Abstract machines or entities that live at contract addresses."],
  ["liquidity-bazaars", "Liquidity Bazaars", "Marketplaces where assets are listed, bought, and transferred."],
  ["atomic-swap-machines", "Atomic Swap Machines", "Devices that exchange asset and payment in one motion."],
  ["genesis-mint-cards", "Genesis Mint Cards", "First-edition cards marking a student's original token creation."],
];

const publicRoot = path.join(__dirname, "..", "frontend", "public");
const labRoot = path.join(publicRoot, "labs", "ethereum_lab");
const assetRoot = path.join(labRoot, "nft-assets");
const metadataRoot = path.join(labRoot, "nft-metadata");
const bankRoot = path.join(labRoot, "nft-bank");

fs.mkdirSync(assetRoot, { recursive: true });
fs.mkdirSync(metadataRoot, { recursive: true });
fs.mkdirSync(bankRoot, { recursive: true });

// Generated source art is downscaled to compact 512x512 JPGs (see scripts/process-nft-image.py),
// so the bank references .jpg assets rather than the large source PNGs.
const imageExt = "jpg";

const manifest = {
  version: 1,
  imageBasePath: "/labs/ethereum_lab/nft-assets",
  metadataBasePath: "/labs/ethereum_lab/nft-metadata",
  imageFormat: imageExt,
  reservationModel: "one-student-per-theme",
  variantsPerTheme: 5,
  themes: themes.map(([slug, name, description]) => {
    const themeAssetDir = path.join(assetRoot, slug);
    const themeMetadataDir = path.join(metadataRoot, slug);
    fs.mkdirSync(themeAssetDir, { recursive: true });
    fs.mkdirSync(themeMetadataDir, { recursive: true });

    const variants = Array.from({ length: 5 }, (_, index) => {
      const variantNumber = index + 1;
      const variantSlug = `variant-${String(variantNumber).padStart(2, "0")}`;
      const image = `/labs/ethereum_lab/nft-assets/${slug}/${variantSlug}.${imageExt}`;
      const metadata = `/labs/ethereum_lab/nft-metadata/${slug}/${variantSlug}.json`;
      const metadataFile = path.join(themeMetadataDir, `${variantSlug}.json`);

      const tokenMetadata = {
        name: `${name} ${variantNumber}`,
        description: `${description} This NFT is part of the Tokenization Lab static asset bank.`,
        image,
        attributes: [
          { trait_type: "Theme", value: name },
          { trait_type: "Theme Slug", value: slug },
          { trait_type: "Variant", value: variantNumber },
          { trait_type: "Lab", value: "Tokenization Lab" },
        ],
      };

      // Metadata is fully derived from the theme list, so always (re)write it. This keeps the
      // bank idempotent and lets format/path changes (e.g. .png -> .jpg) propagate on re-run.
      fs.writeFileSync(metadataFile, `${JSON.stringify(tokenMetadata, null, 2)}\n`);

      return {
        slug: variantSlug,
        name: `${name} ${variantNumber}`,
        image,
        metadata,
      };
    });

    return {
      slug,
      name,
      description,
      claimScope: "theme",
      variants,
    };
  }),
};

fs.writeFileSync(path.join(bankRoot, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Prepared ${themes.length} themes and ${themes.length * 5} metadata files.`);
console.log(`Assets: ${assetRoot}`);
console.log(`Metadata: ${metadataRoot}`);
console.log(`Manifest: ${path.join(bankRoot, "manifest.json")}`);
