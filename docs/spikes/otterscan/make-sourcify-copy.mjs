// Lays out compiled contracts the way a Sourcify RepositoryV1 copy does, so Otterscan shows their source offline.
// Usage: node make-sourcify-copy.mjs <forge project> <out dir> <chain id> Name=0xChecksumAddress ...
// The project must be built (forge build); addresses are checksummed, as forge create prints them.
import fs from 'node:fs';
import path from 'node:path';
const [project, outDir, chainId, ...pairs] = process.argv.slice(2);
const outs = fs.readdirSync(path.join(project, 'out')).map(d => path.join(project, 'out', d));
for (const pair of pairs) {
  const [name, addr] = pair.split('=');
  const file = outs.map(d => path.join(d, name + '.json')).find(f => fs.existsSync(f));
  if (!file) throw new Error(`${name}: no build output in ${project}/out`);
  const meta = JSON.parse(fs.readFileSync(file, 'utf8')).rawMetadata;
  const dir = path.join(outDir, 'contracts/full_match', chainId, addr);
  for (const src of Object.keys(JSON.parse(meta).sources)) {
    fs.mkdirSync(path.dirname(path.join(dir, 'sources', src)), { recursive: true });
    fs.copyFileSync(path.join(project, src), path.join(dir, 'sources', src));
  }
  fs.writeFileSync(path.join(dir, 'metadata.json'), meta);
  console.log(`${name} ${addr}: ${dir}`);
}
