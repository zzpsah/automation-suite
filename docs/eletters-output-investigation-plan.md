# eLetters Output Investigation Plan

This record accompanies the eLetters regression evidence ledger. The objective is to restore the pre-existing output behavior, not replace it.

1. Compare `Global Document Publication` state transitions with the existing `Global Document Telegram Notifier` contract.
2. Trace source-file-change/reprocessing events that can invalidate an already published document.
3. Inspect notifier workflow runs and exact failures around the regression window.
4. Preserve the existing B2-to-Telegram PDF delivery mechanism.
5. Apply the smallest evidence-backed fix and verify it in CI and live Supabase state.
6. Require real Telegram PDF delivery plus a corresponding audit row before closure.

No synthetic document or synthetic delivery event is to be used as proof.