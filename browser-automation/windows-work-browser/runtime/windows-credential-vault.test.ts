import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { WindowsCredentialVault } from "./windows-credential-vault";

test("Windows vault fails closed off Windows", async () => {
  const vault = new WindowsCredentialVault();
  if (process.platform !== "win32") {
    await assert.rejects(
      () => vault.save("test", "https://example.com", "synthetic-secret"),
      /requires Windows/i,
    );
  }
});

test("vault persists protected credentials and never returns plaintext", async () => {
  if (process.platform !== "win32") return;
  const directory = await mkdtemp(join(tmpdir(), "wwb-vault-"));
  const path = join(directory, "vault.json");
  const first = new WindowsCredentialVault(path);
  await first.save("test", "https://example.com", "synthetic-secret", "alice");

  const stored = await first.list("https://example.com");
  assert.deepEqual(stored, [{ id: "test", origin: "https://example.com", username: "alice" }]);
  assert.ok(first.getProtectedBlobForNativeBridge("test"));
  assert.equal(first.getProtectedBlobForNativeBridge("missing"), undefined);

  const restarted = new WindowsCredentialVault(path);
  const result = await restarted.use({ credentialId: "test", origin: "https://example.com", purpose: "login" });
  assert.equal(result.ok, true);
  assert.equal("secret" in result, false);
  assert.match(result.sessionRef ?? "", /^cred-session-/);

  await restarted.remove("test");
  assert.deepEqual(await restarted.list(), []);
});
