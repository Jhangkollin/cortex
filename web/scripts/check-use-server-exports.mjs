#!/usr/bin/env node
/**
 * Static guard: a `"use server"` module must export ONLY async functions.
 *
 * Turbopack emits a runtime reference to any TYPE exported from a
 * `"use server"` module at SSR module-eval time. Because types are erased,
 * that reference is `undefined` and crashes with a `ReferenceError`. The
 * fix is to keep type/interface exports in a plain (non-"use server")
 * module (e.g. a sibling `*-types.ts`).
 *
 * This script fails (exit 1) if a file whose FIRST real line is the
 * `"use server"` directive also has a top-level `export type` /
 * `export interface`. It only treats the directive as real when it is the
 * first non-empty, non-comment line — a file that merely mentions
 * `"use server"` inside a comment is NOT flagged.
 *
 * Node built-ins only; no dependencies.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = join(__dirname, "..");
const srcRoot = join(webRoot, "src");

/** Recursively collect every .ts / .tsx file under `dir`. */
function collectFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...collectFiles(full));
    } else if (full.endsWith(".ts") || full.endsWith(".tsx")) {
      out.push(full);
    }
  }
  return out;
}

/**
 * Returns true when the file's first real (non-blank, non-comment) line is
 * a `"use server"` / `'use server'` directive. Skips leading blank lines,
 * `//` line comments, and `/* … *\/` block comments (including multi-line).
 */
function hasRealUseServerDirective(lines) {
  let inBlockComment = false;
  for (let raw of lines) {
    let line = raw.trim();
    if (inBlockComment) {
      const end = line.indexOf("*/");
      if (end === -1) continue;
      // Resume scanning after the block comment ends on this line.
      line = line.slice(end + 2).trim();
      inBlockComment = false;
    }
    if (line === "") continue;
    if (line.startsWith("//")) continue;
    if (line.startsWith("/*")) {
      if (line.includes("*/")) {
        // Single-line block comment — strip it and keep evaluating.
        line = line.slice(line.indexOf("*/") + 2).trim();
        if (line === "") continue;
      } else {
        inBlockComment = true;
        continue;
      }
    }
    // First real line found.
    return line === '"use server";' || line === "'use server';";
  }
  return false;
}

const typeExportRe = /^\s*export\s+(type|interface)\b/;

const offenders = [];
for (const file of collectFiles(srcRoot)) {
  const content = readFileSync(file, "utf8");
  const lines = content.split(/\r?\n/);
  if (!hasRealUseServerDirective(lines)) continue;
  lines.forEach((line, i) => {
    if (typeExportRe.test(line)) {
      offenders.push({ file: relative(webRoot, file), line: i + 1 });
    }
  });
}

if (offenders.length > 0) {
  for (const { file, line } of offenders) {
    console.error(
      `✗ ${file}:${line} — "use server" modules must export only async functions (move types to a *-types.ts module)`,
    );
  }
  process.exit(1);
}

console.log('✓ no type exports from "use server" modules');
process.exit(0);
