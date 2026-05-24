#!/usr/bin/env node
/**
 * Copy lab docs from docs/ to frontend/public/docs/ (recursive), preserving subfolders.
 * Run before build (prebuild) or manually.
 */
const fs = require('fs');
const path = require('path');

const docsSrc = path.join(__dirname, '..', '..', 'docs');
const docsDest = path.join(__dirname, '..', 'public', 'docs');

function walkMdFiles(dir, base = dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const st = fs.statSync(full);
    if (st.isDirectory()) out.push(...walkMdFiles(full, base));
    else if (name.endsWith('.md')) out.push(path.relative(base, full).replace(/\\/g, '/'));
  }
  return out;
}

function removeStaleMd(destRoot, validRelPaths) {
  const valid = new Set(validRelPaths);
  function walk(d) {
    if (!fs.existsSync(d)) return;
    for (const name of fs.readdirSync(d)) {
      const full = path.join(d, name);
      const st = fs.statSync(full);
      if (st.isDirectory()) walk(full);
      else if (name.endsWith('.md')) {
        const rel = path.relative(destRoot, full).replace(/\\/g, '/');
        if (!valid.has(rel)) {
          fs.unlinkSync(full);
          console.log(`copy-docs: Removed stale ${rel}`);
        }
      }
    }
  }
  walk(destRoot);
  // Remove empty directories bottom-up
  function rmdirEmpty(d) {
    if (!fs.existsSync(d)) return;
    for (const name of fs.readdirSync(d)) {
      const full = path.join(d, name);
      if (fs.statSync(full).isDirectory()) rmdirEmpty(full);
    }
    try {
      if (fs.readdirSync(d).length === 0 && d !== destRoot) fs.rmdirSync(d);
    } catch (_) {}
  }
  rmdirEmpty(destRoot);
}

function copyTree(srcRoot, destRoot) {
  fs.mkdirSync(destRoot, { recursive: true });
  for (const name of fs.readdirSync(srcRoot)) {
    const src = path.join(srcRoot, name);
    const dest = path.join(destRoot, name);
    if (fs.statSync(src).isDirectory()) copyTree(src, dest);
    else if (name.endsWith('.md')) {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.copyFileSync(src, dest);
    }
  }
}

if (!fs.existsSync(docsSrc)) {
  console.warn('copy-docs: docs/ folder not found, skipping');
  process.exit(0);
}

const files = walkMdFiles(docsSrc);
if (fs.existsSync(docsDest)) {
  removeStaleMd(docsDest, files);
}
copyTree(docsSrc, docsDest);
console.log(`copy-docs: Synced ${files.length} markdown files to public/docs/ (recursive)`);
