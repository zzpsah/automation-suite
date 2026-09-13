import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { PDFDocument } from "@cantoo/pdf-lib";
import { DeterministicMcpGateway } from "./mcp-gateway";
import { runExtraction } from "./extraction-engine";
import { PdfLibService } from "./pdf-service";
import { SharpImageService } from "./image-service";
import { DeterministicWorkflowService } from "./workflow-service";
import { ApprovedCommunicationService, type CommunicationProvider } from "./communication-service";
import { evaluateAction } from "../agent/policy-engine";
import type { AutomationAction } from "../agent/action-contract";

test("local release component integration suite", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "wwb-release-components-"));
  try {
    const mcp = new DeterministicMcpGateway();
    const capabilities = await mcp.listCapabilities();
    assert.ok(capabilities.some((item) => item.capability === "browser.extract"));
    const mcpAction = await mcp.authorize({
      requestId: "local-1",
      workspaceId: "test-workspace",
      capability: "files.write",
      arguments: { target: "fixture.csv" },
    });
    assert.equal(mcpAction.requiresApproval, true);
    const policy = evaluateAction(mcpAction);
    assert.equal(policy.requiresApproval, true);

    const extracted = runExtraction(
      {
        expectedCount: 2,
        deduplicateBy: ["id"],
        records: [
          { id: "1", name: "Alpha", class: "10" },
          { id: "1", name: "Alpha duplicate", class: "10" },
          { id: "2", name: "Beta", class: "9" },
        ],
      },
      ["id", "name", "class"],
      "csv",
    );
    assert.equal(extracted.countVerified, true);
    assert.equal(extracted.duplicatesRemoved, 1);
    assert.match(extracted.exported, /"id","name","class"/);

    const pdfA = path.join(root, "a.pdf");
    const pdfB = path.join(root, "b.pdf");
    const merged = path.join(root, "merged.pdf");
    const split = path.join(root, "split.pdf");
    for (const file of [pdfA, pdfB]) {
      const doc = await PDFDocument.create();
      doc.addPage([300, 400]);
      await writeFile(file, await doc.save());
    }
    const pdf = new PdfLibService();
    await pdf.merge([pdfA, pdfB], merged);
    const mergedDoc = await PDFDocument.load(await readFile(merged));
    assert.equal(mergedDoc.getPageCount(), 2);
    await pdf.split(merged, { from: 1, to: 1 }, split);
    const splitDoc = await PDFDocument.load(await readFile(split));
    assert.equal(splitDoc.getPageCount(), 1);

    const sourceImage = path.join(root, "input.svg");
    const outputImage = path.join(root, "output.jpg");
    await writeFile(sourceImage, '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="400" height="200" fill="white"/><circle cx="100" cy="100" r="60" fill="black"/></svg>');
    const image = new SharpImageService();
    const imageResult = await image.transform({
      input: sourceImage,
      output: outputImage,
      crop: { x: 0, y: 0, width: 200, height: 200 },
      resize: { width: 100, keepAspect: true },
      format: "jpeg",
      maxBytes: 100_000,
    });
    assert.equal(imageResult.output, outputImage);
    assert.ok(imageResult.bytes > 0 && imageResult.bytes <= 100_000);

    const calls: string[] = [];
    const provider: CommunicationProvider = {
      send: async (message) => { calls.push(message.body); return { providerMessageId: "test-message-1" }; },
    };
    const communication = new ApprovedCommunicationService(provider);
    await assert.rejects(() => communication.send({ destination: "fixture", body: "hello" }), /approval/i);
    const sent = await communication.send({ destination: "fixture", body: "hello" }, "test-approval");
    assert.equal(sent.providerMessageId, "test-message-1");
    assert.deepEqual(calls, ["hello"]);

    const workflow = new DeterministicWorkflowService(path.join(root, "checkpoints"));
    const events: string[] = [];
    const created = await workflow.create("release-smoke", {
      steps: [
        { id: "step-a", run: async () => { events.push("a"); } },
        { id: "step-b", run: async () => { await new Promise((resolve) => setTimeout(resolve, 25)); events.push("b"); } },
      ],
    });
    const task = await workflow.run(created.id);
    for (let i = 0; i < 20 && events.length === 0; i += 1) await new Promise((resolve) => setTimeout(resolve, 10));
    await workflow.pause(task.taskId);
    await new Promise((resolve) => setTimeout(resolve, 40));
    await workflow.resume(task.taskId);
    for (let i = 0; i < 30 && events.length < 2; i += 1) await new Promise((resolve) => setTimeout(resolve, 10));
    assert.deepEqual(events, ["a", "b"]);

    const safeAction: AutomationAction = {
      id: "read-1",
      capability: "browser.read",
      risk: "read",
      args: {},
      requiresApproval: false,
      reason: "test read",
    };
    assert.equal(evaluateAction(safeAction).requiresApproval, false);
    assert.equal(evaluateAction({ ...safeAction, capability: "communication.send", risk: "write" }).requiresApproval, true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
