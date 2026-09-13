import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const raw = execFileSync(npmCommand, ["ls", "--all", "--json", "--omit=optional"], { encoding: "utf8" });
const tree = JSON.parse(raw);
const components = [];
const seen = new Set();

function visit(node, parent = null) {
  if (!node?.dependencies) return;
  for (const [name, dependency] of Object.entries(node.dependencies)) {
    const version = dependency?.version ?? "unknown";
    const key = `${name}@${version}`;
    if (!seen.has(key)) {
      seen.add(key);
      components.push({
        type: "library",
        name,
        version,
        scope: "runtime",
        ...(parent ? { dependsOn: parent } : {}),
      });
    }
    visit(dependency, key);
  }
}

visit(tree);
const bom = {
  bomFormat: "CycloneDX",
  specVersion: "1.5",
  version: 1,
  metadata: {
    timestamp: new Date().toISOString(),
    component: { type: "application", name: tree.name, version: tree.version },
  },
  components: components.sort((a, b) => `${a.name}@${a.version}`.localeCompare(`${b.name}@${b.version}`)),
};
writeFileSync(process.env.SBOM_OUT ?? "sbom.cdx.json", JSON.stringify(bom, null, 2));
