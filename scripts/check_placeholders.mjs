#!/usr/bin/env node
// Fail the web build when PLACEHOLDER_ remains in public-facing files.
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const needle = "PLACEHOLDER_";
const files = [];
const skipDirNames = new Set(["data", "node_modules", ".next"]);

function walk(p) {
  if (!existsSync(p)) return;
  const st = statSync(p);
  if (st.isDirectory()) {
    if (skipDirNames.has(path.basename(p))) return;
    for (const name of readdirSync(p)) walk(path.join(p, name));
    return;
  }
  files.push(p);
}

for (const rel of [
  "web/src",
  "web/public",
  "LICENSE",
  "DATA_LICENSE.md",
  "README.md",
  "CITATION.cff",
  "CONTRIBUTING.md",
  "CHANGELOG.md",
  ".zenodo.json",
]) {
  walk(path.join(root, rel));
}

const hits = [];
for (const file of files) {
  let text = "";
  try {
    text = readFileSync(file, "utf8");
  } catch {
    continue;
  }
  if (!text.includes(needle)) continue;
  text.split(/\r?\n/).forEach((line, i) => {
    if (line.includes(needle)) hits.push(`${path.relative(root, file)}:${i + 1}:${line.trim()}`);
  });
}

if (hits.length) {
  console.error("PLACEHOLDER_ still present in public files:\n" + hits.join("\n"));
  process.exit(1);
}
