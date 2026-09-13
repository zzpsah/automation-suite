import { PlaywrightController } from "./playwright-controller";

async function main(): Promise<void> {
  const endpoint = process.env.CDP_ENDPOINT ?? "http://127.0.0.1:9222";
  const controller = new PlaywrightController({ cdpEndpoint: endpoint, defaultTimeoutMs: 30_000 });
  const sessionId = "ci-e2e";
  try {
    const navigate = await controller.act({ sessionId, executor: "playwright", operation: "navigate", value: "https://example.com" });
    if (!navigate.ok) throw new Error(`Navigate failed: ${navigate.detail ?? "unknown error"}`);
    const first = await controller.verify({ sessionId, condition: "title", expected: "Example Domain" });
    if (!first.passed) throw new Error(`Title verification failed: ${first.detail}`);
    const observed = await controller.observe({ id: sessionId, profileId: "default" });
    if (!observed.url.startsWith("https://example.com")) throw new Error(`Unexpected observed URL: ${observed.url}`);

    const fixture = `data:text/html,<html><body><input id="name"><button id="go" onclick="document.body.dataset.done=document.getElementById('name').value">Go</button></body></html>`;
    const second = await controller.act({ sessionId, executor: "playwright", operation: "navigate", value: fixture });
    if (!second.ok) throw new Error(`Fixture navigate failed: ${second.detail ?? "unknown error"}`);
    const typed = await controller.act({ sessionId, executor: "playwright", operation: "type", target: "#name", value: "Windows Work Browser" });
    if (!typed.ok) throw new Error(`Type failed: ${typed.detail ?? "unknown error"}`);
    const clicked = await controller.act({ sessionId, executor: "playwright", operation: "click", target: "#go" });
    if (!clicked.ok) throw new Error(`Click failed: ${clicked.detail ?? "unknown error"}`);
    const verified = await controller.verify({ sessionId, condition: "element-visible", target: "#go" });
    if (!verified.passed) throw new Error(`Element verification failed: ${verified.detail}`);
    const extracted = await controller.act({ sessionId, executor: "playwright", operation: "extract", target: "body" });
    if (!extracted.ok || !String(extracted.detail).includes("Windows Work Browser")) {
      throw new Error(`Extract failed: ${extracted.detail ?? "missing text"}`);
    }

    console.log(JSON.stringify({ endpoint, status: "PASS", browserUrl: observed.url, operations: ["navigate", "type", "click", "verify", "extract"] }));
  } finally {
    await controller.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
