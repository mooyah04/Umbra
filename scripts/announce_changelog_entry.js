#!/usr/bin/env node
/*
 * Extract the top entry from frontend/src/lib/changelog.ts and
 * optionally post it to the Discord webhook.
 *
 * The changelog.ts file is valid JavaScript minus its type annotations,
 * so we strip imports/types/interfaces and eval the resulting module.
 * Much more robust than regex-extracting a TS object literal with
 * multi-line strings and escaped quotes.
 *
 * Usage:
 *   node scripts/announce_changelog_entry.js extract <path>
 *     -> prints JSON of the top entry
 *   node scripts/announce_changelog_entry.js diff <old-path> <new-path>
 *     -> exits 0 if the top entry (date+title) differs, 1 if unchanged
 *   node scripts/announce_changelog_entry.js post <path>
 *     -> posts the top entry to $DISCORD_ANNOUNCE_WEBHOOK
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

function loadChangelog(filePath) {
  const source = fs.readFileSync(filePath, "utf-8");
  // Strip TS-only syntax and the lone type annotation on CHANGELOG.
  // Everything we're dropping is preamble; the array literal itself is
  // plain JavaScript.
  const jsOnly = source
    .replace(/^import[\s\S]*?;$/gm, "")
    .replace(/^export\s+type\s+[\s\S]*?;$/gm, "")
    .replace(/^export\s+interface\s+\w+\s*\{[\s\S]*?^\}$/gm, "")
    .replace(
      /export\s+const\s+CHANGELOG\s*:\s*ChangelogEntry\[\]/,
      "const CHANGELOG"
    )
    + "\nmodule.exports = CHANGELOG;\n";

  // Write to a temp .js file and require() it. require() caches by
  // absolute path, so each extraction writes a unique temp so repeated
  // calls within one process still see fresh content.
  const tmp = path.join(
    os.tmpdir(),
    `changelog-${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}.js`
  );
  fs.writeFileSync(tmp, jsOnly);
  try {
    const mod = require(tmp);
    if (!Array.isArray(mod) || mod.length === 0) {
      throw new Error("CHANGELOG is empty or not an array");
    }
    return mod[0];
  } finally {
    fs.unlinkSync(tmp);
  }
}

const CATEGORY_COLORS = {
  new: 0x10b981, // green
  improved: 0x3b82f6, // blue
  fixed: 0xf59e0b, // amber
};
const CATEGORY_LABELS = {
  new: "New",
  improved: "Improved",
  fixed: "Fixed",
};

function buildPayload(entry) {
  let body = entry.body ?? "";
  // Discord embed description caps at 4096 chars; stay well under.
  if (body.length > 3500) {
    body = body.slice(0, 3500).trimEnd() + "\n...";
  }
  const category = entry.category ?? "improved";
  return {
    embeds: [
      {
        title: entry.title,
        description: body,
        url: "https://wowumbra.gg/changelog",
        color: CATEGORY_COLORS[category] ?? 0x8a2be2,
        footer: {
          text: `${CATEGORY_LABELS[category] ?? category} · wowumbra.gg/changelog`,
        },
      },
    ],
  };
}

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  if (cmd === "extract") {
    const entry = loadChangelog(args[0]);
    console.log(JSON.stringify(entry, null, 2));
    return;
  }
  if (cmd === "diff") {
    const prev = loadChangelog(args[0]);
    const cur = loadChangelog(args[1]);
    if (prev.date !== cur.date || prev.title !== cur.title) {
      console.log("different");
      process.exit(0);
    } else {
      console.log("unchanged");
      process.exit(1);
    }
  }
  if (cmd === "post") {
    const webhook = process.env.DISCORD_ANNOUNCE_WEBHOOK;
    if (!webhook) {
      console.error("DISCORD_ANNOUNCE_WEBHOOK not set; skipping.");
      return;
    }
    const entry = loadChangelog(args[0]);
    const payload = buildPayload(entry);
    const res = await fetch(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Discord webhook ${res.status}: ${text}`);
    }
    console.log(`Posted: ${entry.title}`);
    return;
  }
  console.error(
    "Usage: node announce_changelog_entry.js {extract|diff|post} <path> [other_path]"
  );
  process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
