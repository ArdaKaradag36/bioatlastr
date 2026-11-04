#!/usr/bin/env node
// Fail the web build when PLACEHOLDER_ remains in public-facing files.
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const targets = [
  path.join(root, "web/src"),
  path.join(root, "web/public"),
  path.join(root, "LICENSE"),
  path.join(root, "DATA_LICENSE.md"),
  path.join(root, "README.md"),
  path.join(root, "CITATION.cff"),
  path.join(root, "CONTRIBUTING.md"),
  path.join(root, "CHANGELOG.md"),
  path.join(root, ".zenodo.json"),
].filter((p) => existsSync(p));

const rg = process.env.RG || "rg";
let out = "";
try {
  out = execFileSync(
    rg,
    ["-n", "--glob", "!data/**", "PLACEHOLDER_", ...targets],
    { encoding: "utf8" },
  );
} catch (err) {
  if (err.status === 1) {
    process.exit(0); // no matches
  }
  if (err.status === 127 || err.code === "ENOENT") {
    console.error("rg not found; install ripgrep or set RG=");
    process.exit(2);
  }
  throw err;
}

if (out.trim()) {
  console.error("PLACEHOLDER_ still present in public files:\n" + out);
  process.exit(1);
}
