#!/usr/bin/env python3
"""Batch-generate the remaining Tokenization Lab NFT bank images.

Pipeline (validated 2026-06-03, see memory nft-bank-image-pipeline):
  1. agy --add-dir /tmp/nft-raw -p "...native Imagen... save PNG at <abs>"  -> ~1024x1024 raw
  2. scripts/process-nft-image.py <raw> <dest>.jpg --quality 80            -> 512x512 JPG

This driver is RESUMABLE and IDEMPOTENT: it skips any final variant JPG that
already exists, so re-running only fills gaps. It retries agy a few times per
image and never aborts the whole batch on a single failure (failures are
collected and reported at the end).

Usage:
  python3 scripts/generate-nft-batch.py            # generate every missing image in the spec
  python3 scripts/generate-nft-batch.py <slug>...  # only the given theme slugs
  python3 scripts/generate-nft-batch.py --force ... # regenerate even if the JPG exists
"""

import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_ROOT = os.path.join(REPO, "frontend", "public", "labs", "ethereum_lab", "nft-assets")
RAW_DIR = "/tmp/nft-raw"
PROCESS = os.path.join(REPO, "scripts", "process-nft-image.py")

# Shared house style so the whole 200-image bank reads as one cohesive collection.
GLOBAL_STYLE = (
    "richly painted heavily textured ultra-detailed ornate oil-painting digital concept art, "
    "dense intricate rendering with fine detail filling the whole frame, warm molten gold amber "
    "and bronze palette, intense inner glow, glowing golden particle sparks, dark shadowed "
    "background with a faint tiled blockchain-grid floor, dramatic chiaroscuro lighting, clean "
    "centered composition, strong readable silhouette, cohesive Ethereum blockchain artifact "
    "collection, recurring glowing Ethereum diamond octahedron motif, "
    "absolutely NOT flat, NOT minimalist, NOT vector art, NOT a simple flat illustration, NOT "
    "sparse, NOT plain, NOT a clip-art icon, "
    "NO text, no lettering, no numbers, no logos, no watermarks, no signatures"
)

# revert-posters established a red warning palette, so override the gold for it.
REVERT_STYLE = (
    "richly painted heavily textured ultra-detailed ornate oil-painting digital concept art, "
    "dense intricate rendering with fine detail filling the whole frame, deep crimson rust and "
    "ember-orange warning palette, cracked glowing red-orange light, sparks and embers, ominous "
    "danger atmosphere, dark riveted industrial background, dramatic chiaroscuro lighting, clean "
    "centered composition, strong readable silhouette, recurring glowing Ethereum diamond "
    "octahedron motif, absolutely NOT flat, NOT minimalist, NOT vector art, NOT a simple flat "
    "illustration, NOT sparse, NOT plain, NOT a clip-art icon, "
    "NO text, no lettering, no numbers, no logos, no watermarks, no signatures"
)

# slug -> { variant_number: subject }.  Partial themes list only variant 5;
# new themes list all five distinct compositions.
THEMES = {
    # ---- 3 remaining partial themes (only variant-05) ----
    "escrow-chambers": {
        5: "a deep underground stone escrow vault chamber, a tall glowing glass containment "
           "cylinder at the center holding a luminous Ethereum diamond octahedron suspended in "
           "light, two ornate armored guardian sentinel statues flanking it, carved rune circles "
           "on the floor, gold light beams, locked treasure waiting for atomic exchange, overhead "
           "three-quarter view",
    },
    "payable-gates": {
        5: "a massive ornate stone payable gateway arch, twin pillars carved with circuitry runes, "
           "a brilliant vertical river of golden energy pouring down through the open gate onto a "
           "glowing tiled path, small Ethereum diamond coins floating upward toward the gate, the "
           "gate only opens when payment flows, frontal heroic view",
    },
    "revert-posters": {  # uses REVERT_STYLE
        5: "a weathered distressed warning banner nailed to a dark riveted industrial pipe wall, a "
           "cracked glowing red-orange Ethereum diamond octahedron emblem fracturing at the center, "
           "sparks and embers raining down, a failed reverted transaction, straight-on view",
    },

    # ---- 18 new themes (all five variants) ----
    "gas-limit-engines": {
        1: "a towering brass and gold computation engine with glowing gas-fed pistons and pressure "
           "gauges, an Ethereum diamond glowing in its furnace core, pipes venting golden vapor, "
           "mounted on a stone dais, heroic three-quarter view",
        2: "a horizontal row of interlocking golden gear-driven engine cylinders burning luminous "
           "gas, an Ethereum crest at the hub, glowing valves, intricate clockwork, side profile view",
        3: "an overhead view of a circular gas-limit engine, radial pistons firing around a central "
           "glowing Ethereum octahedron furnace, golden steam swirling outward",
        4: "a colossal vertical engine tower of stacked brass combustion chambers each burning a "
           "golden flame, pressure pipes spiraling upward, an Ethereum diamond capstone glowing",
        5: "an extreme close-up of a single ornate engine valve and gauge cluster, molten gold gas "
           "igniting, an embossed Ethereum diamond on the brass housing, flying sparks",
    },
    "pending-transaction-lanterns": {
        1: "a swarm of ornate golden lanterns floating upward in the dark, each glowing with a tiny "
           "Ethereum diamond inside, suspended mid-air over a tiled grid, wide atmospheric view",
        2: "a single grand ornate floating lantern at center with intricate filigree cage and a "
           "luminous Ethereum octahedron flame within, smaller lanterns drifting behind it",
        3: "a vertical column of stacked glowing golden lanterns rising like a queue into darkness, "
           "warm light, each holding an Ethereum diamond, waiting to be included",
        4: "a cluster of three large lanterns tethered by glowing golden threads, hovering above a "
           "reflective blockchain-grid floor, sparks rising, an Ethereum crest glow",
        5: "an extreme close-up of one filigree lantern, its glass panes glowing amber, an Ethereum "
           "diamond suspended inside as the flame, ornate metalwork",
    },
    "miners-archive": {
        1: "an ancient archive vault of proof-of-work mining relics, golden pickaxes and bronze "
           "mining lamps mounted on a stone wall around a glowing Ethereum diamond, stacked ledger "
           "tomes, museum display view",
        2: "a heavy ornate mining pickaxe and lantern crossed over a glowing block of ore containing "
           "an Ethereum octahedron, on a pedestal, dramatic light",
        3: "rows of bronze ledger books and rock-core samples on archive shelves each glowing faintly "
           "gold, a central Ethereum crest, dusty historical atmosphere",
        4: "an old golden mining cart filled with glowing Ethereum-diamond ore nuggets, rails leading "
           "into a dark mine, warm lamplight",
        5: "an extreme close-up of a weathered bronze miner's medallion engraved with an Ethereum "
           "diamond and crossed pickaxes, glowing patina",
    },
    "beacon-chain-signals": {
        1: "a tall ornate golden beacon tower on a dark cliff emitting a brilliant vertical beam of "
           "light into the sky, an Ethereum diamond glowing at its apex, smaller beacons answering in "
           "the distance, epic wide view",
        2: "a ring of golden signal beacons arranged in a circle, each beaming light toward a central "
           "floating Ethereum octahedron, consensus visualized, overhead three-quarter view",
        3: "a single monumental beacon lighthouse, spiraling golden energy rising from its base to a "
           "radiant Ethereum crest lantern at the top, frontal heroic view",
        4: "an overhead view of a network of beacon towers connected by glowing golden signal lines "
           "across a dark tiled plain, an Ethereum hub at center",
        5: "an extreme close-up of a beacon's glowing crystal lens with an Ethereum diamond refracted "
           "in radiant golden light, ornate brass housing",
    },
    "epoch-clocks": {
        1: "a grand ornate golden astronomical clock with concentric rotating rings marking epochs "
           "and slots, an Ethereum diamond as the central gear, glowing hands, intricate gears, "
           "frontal view",
        2: "a golden orrery of orbiting epoch spheres revolving around a luminous central Ethereum "
           "octahedron, brass armatures, glowing tracks, three-quarter view",
        3: "an exploded clockwork mechanism floating in dark space, golden gears and escapements "
           "arranged around a glowing Ethereum crest, slot markers",
        4: "a tall ornate grandfather epoch-clock tower, its glowing pendulum a swinging Ethereum "
           "diamond, gears visible through crystal panels",
        5: "an extreme close-up of interlocking golden clock gears with an embossed Ethereum diamond "
           "at the meshing point, glowing jewels",
    },
    "block-builder-workshops": {
        1: "a cozy golden artisan workshop where glowing transaction blocks are assembled and stacked "
           "into a chain on a workbench, tiny tools, an Ethereum crest forge glowing, warm "
           "three-quarter view",
        2: "a master builder's anvil with a glowing Ethereum diamond block being forged, golden sparks "
           "flying, hammers and tongs, stacked finished blocks behind",
        3: "an overhead view of a workshop table covered in glowing modular blocks being arranged into "
           "a chain, golden blueprints, an Ethereum hub",
        4: "a towering assembly rig lifting a glowing block crowned with an Ethereum octahedron onto a "
           "growing tower of blocks, golden cranes and gears",
        5: "an extreme close-up of two glowing blocks being fitted together by golden clamps, an "
           "Ethereum diamond seam glowing between them, sparks",
    },
    "execution-layer-maps": {
        1: "an ornate glowing golden topographic terrain map spread on a table, raised contour ridges "
           "and valleys, luminous routes tracing contract execution across the land, an Ethereum "
           "diamond landmark, overhead view",
        2: "a three-dimensional floating relief map of an execution-layer continent, glowing golden "
           "state-change rivers flowing between districts, an Ethereum crest capital",
        3: "an antique golden cartographer's globe of the execution layer, glowing trade routes and "
           "node cities, an Ethereum octahedron axis",
        4: "a wall-mounted illuminated map panel, golden node markers connected by glowing execution "
           "paths, an Ethereum diamond at the central hub",
        5: "an extreme close-up of a glowing map junction where multiple golden execution routes "
           "converge on an embossed Ethereum diamond waypoint",
    },
    "address-masks": {
        1: "an ornate ceremonial golden identity mask floating in the dark, its surface engraved with "
           "intricate hexadecimal circuitry patterns, a glowing Ethereum diamond on the forehead, "
           "frontal portrait view",
        2: "a wall display of three distinct golden address masks, each with unique engraved patterns "
           "and glowing eyes, an Ethereum crest above",
        3: "a profile three-quarter view of a regal golden mask, filigree circuitry across the cheeks, "
           "a glowing Ethereum octahedron mouthpiece, dramatic light",
        4: "a stack of stylized golden masks on a pedestal with glowing seams, the topmost bearing a "
           "radiant Ethereum diamond, museum lighting",
        5: "an extreme close-up of one ornate mask's eye region, engraved circuit runes, a glowing "
           "Ethereum diamond reflected in the eye",
    },
    "wallet-sigils": {
        1: "an ornate glowing golden heraldic sigil emblem floating in the dark, an Ethereum diamond "
           "at its heart surrounded by intricate filigree key-and-shield motifs, frontal crest view",
        2: "a circular golden sigil seal of ownership, concentric engraved rings of arcane circuitry "
           "around a luminous Ethereum octahedron, radiating light",
        3: "three distinct floating wallet sigil crests arranged in a triangle, each glowing gold with "
           "a unique emblem, an Ethereum diamond linking them",
        4: "a tall ceremonial banner bearing a regal golden wallet sigil, an Ethereum crest above "
           "crossed keys, glowing threads",
        5: "an extreme close-up of a glowing engraved sigil medallion, an embossed Ethereum diamond "
           "ringed by ornate ownership runes, golden glow",
    },
    "signature-runes": {
        1: "an ancient towering golden runestone monolith covered in glowing engraved cryptographic "
           "signature runes, an Ethereum diamond carved at its center, heroic frontal view",
        2: "a circle of standing golden signature-rune stones around a glowing central Ethereum "
           "octahedron, radiating engraved light lines, overhead three-quarter view",
        3: "a single ornate rune tablet held upright, intricate glowing signature glyphs flowing "
           "across it, an Ethereum crest seal at the base",
        4: "a cascade of floating golden rune sigils swirling around an Ethereum diamond, each glowing "
           "mark a cryptographic signature, dark space",
        5: "an extreme close-up of a glowing carved signature rune on golden stone, an embossed "
           "Ethereum diamond at the rune's intersection, molten light in the grooves",
    },
    "token-vaults": {
        1: "an ornate golden vault chamber with a single glowing Ethereum-diamond token displayed on a "
           "central pedestal under a beam of light, thick engraved vault door open, three-quarter view",
        2: "a wall of golden safe-deposit token drawers, one open and glowing with an Ethereum "
           "octahedron inside, intricate locks, secure atmosphere",
        3: "a luminous Ethereum token suspended inside a transparent golden display dome on a marble "
           "plinth, ornate base, museum lighting",
        4: "a massive circular golden vault door dialed open, golden light pouring out revealing a "
           "glowing Ethereum diamond within, frontal heroic view",
        5: "an extreme close-up of an ornate golden lockbox cracked open, a radiant Ethereum diamond "
           "token nestled inside, glowing facets",
    },
    "metadata-capsules": {
        1: "an ornate golden glass capsule canister floating upright, glowing data and a luminous "
           "Ethereum diamond suspended inside, intricate brass caps and seals, frontal view",
        2: "a rack of three glowing metadata capsules, each a golden vial holding swirling luminous "
           "data motes around a tiny Ethereum crest",
        3: "a single grand metadata capsule cracked open, golden light and ribbons of glowing data "
           "streaming out, an Ethereum octahedron core",
        4: "a cluster of floating golden capsule pods orbiting a central Ethereum diamond, glowing "
           "seams, dark space",
        5: "an extreme close-up of one ornate capsule's glowing core, an Ethereum diamond encased in "
           "swirling golden data threads, brass filigree",
    },
    "uri-beacons": {
        1: "an ornate golden beacon obelisk emitting a focused beam of light that arcs toward a distant "
           "glowing metadata scroll, an Ethereum diamond at the beacon's tip, wide view",
        2: "a floating golden signal node projecting glowing linked threads outward to orbiting data "
           "tablets, an Ethereum octahedron core, a network of pointers",
        3: "a tall lighthouse-like beacon casting a golden directed ray across a dark tiled plain "
           "toward a glowing capsule, an Ethereum crest lantern",
        4: "two golden beacons connected by a bright glowing link arc, an Ethereum diamond traveling "
           "along the beam between token and metadata",
        5: "an extreme close-up of a beacon's golden emitter lens firing a focused glowing link-beam, "
           "an embossed Ethereum diamond on the housing",
    },
    "explorer-windows": {
        1: "an ornate golden arched window frame floating in the dark, glowing blockchain data and an "
           "Ethereum diamond visible through the glass like a magical portal, frontal view",
        2: "a row of three golden explorer window panels, each revealing a different glowing scene of "
           "blocks and transactions, an Ethereum crest above",
        3: "a grand circular golden porthole window opening onto a luminous interior of floating "
           "blocks and an Ethereum octahedron, brass rivets",
        4: "an ornate bay window of golden frames overlooking a glowing cityscape of blocks, an "
           "Ethereum diamond sun on the horizon, three-quarter view",
        5: "an extreme close-up of an ornate golden window mullion and glowing pane, an Ethereum "
           "diamond glimpsed through the rippled glass",
    },
    "contract-creatures": {
        1: "an ornate golden mechanical creature, a sleek geometric golem with a glowing "
           "Ethereum-diamond core and circuit-etched plating, standing alert on a tiled platform, "
           "heroic three-quarter view",
        2: "a coiled serpentine golden contract-creature made of interlocking blocks with glowing "
           "seams, an Ethereum octahedron head, hovering in dark space",
        3: "a small ornate mechanical guardian beast crouched protectively over a glowing Ethereum "
           "diamond, brass limbs, glowing eyes, frontal view",
        4: "a winged golden machine-creature with circuitry feathers and an Ethereum crest on its "
           "chest, spreading luminous wings, dramatic light",
        5: "an extreme close-up portrait of a contract-creature's golden mechanical head, a glowing "
           "Ethereum-diamond eye, intricate engraved plating",
    },
    "liquidity-bazaars": {
        1: "a bustling ornate golden bazaar of market stalls under glowing lanterns, floating "
           "Ethereum-diamond tokens displayed for trade, draped awnings, wide atmospheric view",
        2: "a central golden market fountain with luminous Ethereum tokens cascading like coins, "
           "stalls radiating outward, glowing exchange activity, overhead view",
        3: "a single ornate golden trading stall draped in fabric, a glowing Ethereum octahedron on "
           "display, scales and ledgers, warm lamplight, three-quarter view",
        4: "a grand bazaar archway entrance with hanging golden lanterns and floating tradable tokens "
           "streaming through, an Ethereum crest keystone",
        5: "an extreme close-up of a merchant's golden scale balancing a glowing Ethereum diamond "
           "against coins, ornate bazaar detail",
    },
    "atomic-swap-machines": {
        1: "an ornate golden exchange machine with two symmetrical chambers connected by a glowing "
           "mechanism, an Ethereum diamond and a stack of coins swapping simultaneously across the "
           "center, frontal view",
        2: "a grand golden balance-scale apparatus, an Ethereum octahedron on one glowing pan and "
           "payment on the other, locked in a single instant of exchange, three-quarter view",
        3: "an intricate clockwork swap engine, two interlocking golden rotors trading glowing tokens "
           "between them in one motion, sparks at the seam",
        4: "a symmetrical mirror-image machine, two golden hands reaching from opposite sides "
           "exchanging a glowing Ethereum diamond and a coin at the center, beam of light",
        5: "an extreme close-up of the swap mechanism's central golden gear, an Ethereum diamond and a "
           "coin crossing paths mid-exchange, glowing",
    },
    "genesis-mint-cards": {
        1: "an ornate golden first-edition collectible card floating upright, a radiant Ethereum "
           "diamond crest embossed at its center within a filigree border, glowing genesis aura, "
           "frontal hero view",
        2: "a fanned spread of three identical golden genesis cards, each glowing with an Ethereum "
           "octahedron emblem, ornate borders, dramatic light",
        3: "a single golden genesis card encased in a glowing protective slab on a pedestal, an "
           "Ethereum diamond crest, premium first-edition presentation",
        4: "a golden genesis card mid-mint emerging from a beam of light with sparks, an Ethereum "
           "diamond crest forming on its face, ornate frame",
        5: "an extreme close-up of a genesis card's embossed corner, a radiant Ethereum diamond crest "
           "and ornate filigree border catching golden light",
    },
}

MIN_RAW_BYTES = 120_000  # below this the call plainly failed (0KB == agy timed out / throttled)
# Imagen intermittently drops into a flat/minimalist vector style that clashes with the
# painterly house look. Those flat renders compress to ~150KB; rich painterly ones are
# ~600KB-2.5MB. So treat raw size as a richness proxy and retry anything under this floor.
RICH_MIN_BYTES = 400_000
FLAT_RETRIES = 4         # flat-render (got an image but < rich floor) tries before accepting best
# The Google plan throttles Imagen after bursts: latency climbs until agy returns 0KB. When that
# happens we back off and retry the SAME image rather than give up, so the run self-heals through
# throttle windows. MAX_COOLDOWNS caps total back-offs so the run can never loop forever.
COOLDOWN_SECS = 1500     # 25-min back-off on a throttle (0KB) signal
MAX_COOLDOWNS = 40       # generous cap so an overnight run persists through long throttle windows


def build_prompt(slug, subject, raw_path):
    style = REVERT_STYLE if slug == "revert-posters" else GLOBAL_STYLE
    return (
        f"Use ONLY your built-in native Imagen image-generation model to render ONE image at a square "
        f"1:1 aspect ratio, then save it as a PNG to the absolute path {raw_path}. "
        f"Do NOT write, author, or run any code, script, Python, PIL, numpy, matplotlib, SVG, or canvas "
        f"drawing to produce this image — it must be a genuine Imagen painterly render, never a "
        f"procedurally drawn illustration. If you cannot use native Imagen right now, do NOT fall back "
        f"to drawing it with code; just stop without creating the file. "
        f"Style: {style}. "
        f"Subject: {subject}. "
        f"After saving, reply with only the final saved path."
    )


def run_agy(prompt, raw_path):
    """Call agy once; return the resulting raw byte size (0 if nothing landed)."""
    try:
        os.remove(raw_path)
    except FileNotFoundError:
        pass
    try:
        subprocess.run(
            ["agy", "--add-dir", RAW_DIR, "-p", prompt],
            timeout=330,  # agy self-caps generation near ~300s; reap promptly past that
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        pass
    return os.path.getsize(raw_path) if os.path.exists(raw_path) else 0


def downscale(raw_path, dest_path):
    """Downscale to the final JPG; resilient to transient 9p write errors. Returns bool."""
    for _ in range(4):
        try:
            subprocess.run(
                ["python3", PROCESS, raw_path, dest_path, "--quality", "80"],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            time.sleep(1)
    return False


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    only = [a for a in argv if not a.startswith("--")]

    jobs = []
    for slug, variants in THEMES.items():
        if only and slug not in only:
            continue
        for num, subject in sorted(variants.items()):
            dest = os.path.join(ASSET_ROOT, slug, f"variant-{num:02d}.jpg")
            if os.path.exists(dest) and not force:
                continue
            jobs.append((slug, num, subject, dest))

    total = len(jobs)
    print(f"[batch] {total} images to generate (rich floor {RICH_MIN_BYTES//1000}KB; "
          f"auto-cooldown {COOLDOWN_SECS}s on throttle, cap {MAX_COOLDOWNS})", flush=True)
    done, low, failed = 0, [], []
    cooldowns = 0
    aborted = False
    for i, (slug, num, subject, dest) in enumerate(jobs, 1):
        if aborted:
            failed.append(f"{slug}/variant-{num:02d} (unstarted)")
            continue
        label = f"{slug}/variant-{num:02d}"
        try:
            raw = os.path.join(RAW_DIR, f"{slug}-variant-{num:02d}-raw.png")
            best = os.path.join(RAW_DIR, f"{slug}-variant-{num:02d}-best.png")
            prompt = build_prompt(slug, subject, raw)
            best_size = 0
            flat_tries = 0
            while True:
                t0 = time.time()
                size = run_agy(prompt, raw)
                dt = time.time() - t0
                if size >= RICH_MIN_BYTES:                      # rich painterly render — done
                    best_size = size
                    if os.path.exists(raw):
                        shutil.copyfile(raw, best)
                    print(f"[{i}/{total}] OK    {label}  ({size//1000}KB, {dt:.0f}s)", flush=True)
                    break
                if size >= MIN_RAW_BYTES:                       # got an image but flat/low-detail
                    if size > best_size:
                        best_size = size
                        if os.path.exists(raw):
                            shutil.copyfile(raw, best)
                    flat_tries += 1
                    print(f"[{i}/{total}] retry {label}  (flat {size//1000}KB, try {flat_tries}/{FLAT_RETRIES}, {dt:.0f}s)", flush=True)
                    if flat_tries >= FLAT_RETRIES:
                        break                                   # accept the richest flat we got
                    continue
                # size < MIN_RAW_BYTES -> 0KB: agy timed out, i.e. we're throttled
                if cooldowns >= MAX_COOLDOWNS:
                    print(f"[{i}/{total}] ABORT {label}  (hit {MAX_COOLDOWNS}-cooldown cap; stopping run)", flush=True)
                    aborted = True
                    break
                cooldowns += 1
                print(f"[{i}/{total}] throttle {label}  (0KB after {dt:.0f}s) -> cooldown {COOLDOWN_SECS}s [{cooldowns}/{MAX_COOLDOWNS}]", flush=True)
                time.sleep(COOLDOWN_SECS)                       # back off, then retry the SAME image

            if aborted:
                failed.append(label)
            elif best_size >= MIN_RAW_BYTES and downscale(best, dest):
                done += 1
                if best_size < RICH_MIN_BYTES:
                    low.append(label)
                    print(f"[{i}/{total}] LOW   {label}  (best only {best_size//1000}KB)", flush=True)
            elif best_size >= MIN_RAW_BYTES:
                failed.append(f"{label} (downscale)")
                print(f"[{i}/{total}] FAIL  {label}  (raw OK {best_size//1000}KB but downscale failed; best kept at {best})", flush=True)
            else:
                failed.append(label)
                print(f"[{i}/{total}] FAIL  {label}  (no usable raw)", flush=True)
        except Exception as exc:  # never let one image kill the whole batch
            failed.append(f"{label} (error)")
            print(f"[{i}/{total}] FAIL  {label}  (unexpected error: {exc!r})", flush=True)

    print(f"\n[batch] complete: {done}/{total} generated, {len(low)} low-detail, "
          f"{len(failed)} failed/unfinished (cooldowns used {cooldowns})", flush=True)
    if low:
        print("[batch] low-detail (review): " + ", ".join(low), flush=True)
    if failed:
        print("[batch] failed/unfinished: " + ", ".join(failed), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
