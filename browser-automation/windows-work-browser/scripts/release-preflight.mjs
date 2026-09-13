import { readFileSync } from "node:fs";

const requiredFiles = [
  "docs/RELEASE-GATES.md",
  "docs/FINAL-RELEASE-PACKAGE.md",
  "docs/THIRD-PARTY-NOTICES.md",
  "upstream/OPTION-A-RELEASE.json",
  "runtime/playwright-controller.ts",
  "runtime/windows-native-executor.ts",
  "runtime/mcp-gateway.ts",
  "runtime/extraction-engine.ts",
  "runtime/local-file-service.ts",
  "runtime/pdf-service.ts",
  "runtime/image-service.ts",
  "runtime/update-manager.ts",
  "scripts/generate-sbom.mjs",
];

const missing = requiredFiles.filter((file) => {
  try { readFileSync(file); return false; } catch { return true; }
});
if (missing.length) {
  console.error(`Missing required release files:\n${missing.join("\n")}`);
  process.exit(2);
}

const status = readFileSync("BUILD-STATUS.md", "utf8");
const blocked = ["RELEASE CANDIDATE BLOCKED", "NOT RELEASED", "NOT COMPLETE", "NOT COMPLETED"]
  .filter((token) => status.includes(token));
if (blocked.length) {
  console.error("Release preflight blocked: BUILD-STATUS contains unresolved release state markers.");
  console.error(blocked.join(", "));
  process.exit(3);
}

const manifest = JSON.parse(readFileSync("upstream/OPTION-A-RELEASE.json", "utf8"));
if (!/^[0-9a-f]{64}$/i.test(manifest.artifact.sha256)) throw new Error("Invalid upstream SHA-256.");
console.log(JSON.stringify({ status: "PASS", product: manifest.product, upstream: manifest.upstream.release, artifact: manifest.artifact.filename }));
