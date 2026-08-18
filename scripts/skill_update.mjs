#!/usr/bin/env node
/**
 * Update the globally installed nblm skill via the Vercel skills CLI.
 *
 * GitHub auth resolution order:
 *   1. `gh auth token` (GitHub CLI — preferred)
 *   2. GITHUB_TOKEN env var
 *   3. GH_TOKEN env var
 *   4. unauthenticated (subject to GitHub API rate limits)
 *
 * The resolved token is exported as GITHUB_TOKEN for the child process,
 * which is what `npx skills` reads when fetching repo trees.
 *
 * Usage:
 *   npm run skill:update            # global scope (-g)
 *   node scripts/skill_update.mjs -p  # any skills-CLI update flags pass through
 */
import { execFileSync, spawnSync } from "node:child_process";

function ghCliToken() {
  try {
    const token = execFileSync("gh", ["auth", "token"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    return token || null;
  } catch {
    return null; // gh not installed or not logged in
  }
}

const token = ghCliToken() ?? process.env.GITHUB_TOKEN ?? process.env.GH_TOKEN ?? null;

const env = { ...process.env };
if (token) env.GITHUB_TOKEN = token;

const args = process.argv.slice(2);
const scope = args.length > 0 ? args : ["-g"];

const result = spawnSync("npx", ["--yes", "skills", "update", ...scope], {
  stdio: "inherit",
  env,
  shell: process.platform === "win32",
});

process.exit(result.status ?? 1);
