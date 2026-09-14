# Architecture

## Foundation stack

`WPF shell -> WebView2 browser surface -> browser state/services -> later CDP automation adapter`

## Milestone layering

1. F0 browser ownership: shell, one tab, navigation, startup/shutdown.
2. F1 browser core: tabs, downloads, session/profile basics.
3. F2 automation core: controlled DevTools/automation adapter on the same browser/session.
4. F3 reliable execution: observe -> act -> verify -> retry/checkpoint/recover.
5. F4 extraction: text/tables/records/pagination -> JSON/CSV.
6. F5 task engine: steps/progress/pause/resume/stop.
7. F6 natural-language planner produces structured plans; it does not directly click.
8. F7 safe mutation/approval boundary for uploads/submits/deletes/sends.
9. Optional capabilities only after core reliability is proven.

## Core invariant
AI planning must never become the execution authority. A deterministic, validated runtime owns browser actions and verification.
