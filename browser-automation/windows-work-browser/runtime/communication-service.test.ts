import test from "node:test";
import assert from "node:assert/strict";
import { ApprovedCommunicationService, type CommunicationProvider } from "./communication-service";

test("communication service rejects unapproved outbound send", async () => {
  const calls: string[] = [];
  const provider: CommunicationProvider = { send: async (message) => { calls.push(message.body); return { providerMessageId: "m1" }; } };
  const service = new ApprovedCommunicationService(provider);
  await assert.rejects(() => service.send({ destination: "demo", body: "hello" }), /approval/i);
  assert.equal(calls.length, 0);
  const result = await service.send({ destination: "demo", body: "hello" }, "approved");
  assert.equal(result.providerMessageId, "m1");
  assert.deepEqual(calls, ["hello"]);
});
