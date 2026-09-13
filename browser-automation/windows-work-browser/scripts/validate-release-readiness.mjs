import { readFile } from "node:fs/promises";

const file = new URL("../RELEASE-READINESS.json", import.meta.url);
const readiness = JSON.parse(await readFile(file, "utf8"));

const required = Object.entries(readiness.gates ?? {})
  .filter(([, value]) => value !== true)
  .map(([key]) => key);

const optional = Object.entries(readiness.optionalGates ?? {})
  .filter(([, value]) => value !== true)
  .map(([key]) => key);

if (readiness.releaseReady !== true || required.length > 0) {
  console.error(
    JSON.stringify(
      {
        status: "BLOCKED",
        releaseReady: readiness.releaseReady,
        failingRequiredGates: required,
        optionalGatesPending: optional,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      status: "READY",
      releaseReady: true,
      optionalGatesPending: optional,
    },
    null,
    2,
  ),
);
