import { readFile } from "node:fs/promises";

const file = new URL("../RELEASE-READINESS.json", import.meta.url);
const readiness = JSON.parse(await readFile(file, "utf8"));

const required = Object.entries(readiness.gates).filter(([, value]) => value !== true).map(([key]) => key);
if (readiness.releaseReady !== true || required.length > 0) {
  console.error(JSON.stringify({ status: "BLOCKED", releaseReady: readiness.releaseReady, failingGates: required }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "READY", releaseReady: true }, null, 2));
