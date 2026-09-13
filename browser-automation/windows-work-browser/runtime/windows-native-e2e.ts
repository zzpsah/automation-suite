import { FixedWindowsNativeExecutor } from "./windows-native-executor";

async function main(): Promise<void> {
  const executor = new FixedWindowsNativeExecutor();
  const before = await executor.observe();
  const clipboard = await executor.execute({
    operation: "clipboard-write",
    arguments: { text: "Windows Work Browser native smoke" },
    timeoutMs: 10_000,
  });
  if (!clipboard.ok) throw new Error(`Clipboard write failed: ${clipboard.error?.message ?? "unknown error"}`);
  const after = await executor.observe();
  console.log(JSON.stringify({ status: "PASS", observedBefore: before.foregroundWindow, observedAfter: after.foregroundWindow, clipboardWrite: clipboard.ok }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
