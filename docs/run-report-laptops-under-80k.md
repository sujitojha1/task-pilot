# Run Report: Compare 3 Laptops under Rs 80,000

Closes [issue #5](https://github.com/sujitojha1/repo-genesis/issues/5) (milestone M2: Comparison Dry Runs).

- **Session:** `s8-61aa4af8` (artifacts under `code/state/sessions/s8-61aa4af8/`, local only)
- **Date:** 2026-06-11
- **Query:** `Compare 3 laptops under Rs 80,000`
- **Wall time:** 5.6 min
- **Outcome:** Pass (critic verdict on final attempt)

## Final comparison

| # | Laptop | Price |
|---|--------|-------|
| 1 | HP 15.6-inch Graphics Privacy (fc0031AU) | ₹55,490 |
| 2 | HP i3-1315U Anti-Glare Micro-Edge (fd0573TU) | ₹55,990 |
| 3 | ASUS Vivobook Touchscreen Office (X1504VA-E83959WS) | ₹56,990 |

Prices were extracted from live product listings (Amazon.in), not search snippets.

## Browser steps and layer per step

Six browser invocations, each driven by a planner goal with visible actions
(search, price filter, sort, extract). The browser cascade recorded the layer
used for every step:

| Node | Site | Goal (abridged) | Layer | Turns |
|------|------|-----------------|-------|-------|
| n:2  | flipkart.com | search "laptops", filter ₹40k–80k, sort by popularity, extract top 3 | a11y | 10 |
| n:7  | amazon.in | search "laptops", filter below ₹80k, sort featured, extract top 3 | a11y | 4 |
| n:12 | amazon.in | search "laptops", filter under ₹80k, sort featured, extract top 3 | a11y | 6 |
| n:17 | amazon.in | search "laptops under 80000", sort price low-to-high, extract top 3 | a11y | 6 |
| n:22 | flipkart.com | search "laptops", filter below ₹80k, sort by popularity, extract top 3 | vision | 7 |
| n:27 | amazon.in | search "laptops", filter under ₹80k, sort featured, extract top 3 | a11y | 7 |

## Screenshots / page-state logs

Every browser turn saved a raw screenshot plus an element legend under the
session directory, e.g.
`code/state/sessions/s8-61aa4af8/browser/browser_1781194809/a11y/turn_01_raw.png`
and `turn_01_legend.txt`. The vision-path run additionally saved
set-of-marks images (`turn_NN_marked.png`).

## Turn count and cost summary

- **Plan nodes:** 30 total — 6 planner, 6 browser, 6 distiller, 6 critic,
  1 formatter, 5 skipped (formatter nodes abandoned when a critic failed).
- **Browser turns:** 40 across the 6 browser invocations.
- **Recovery loop:** critics failed 5 times (n:5, n:10, n:14, n:20, n:25 —
  mostly over-budget items leaking into the extraction); the planner
  re-planned after each failure and the 6th attempt passed (n:30).
- **Providers:** gemini (planner / distiller / formatter), groq (critic);
  browser cascade ran locally.
- **Recorded cost:** $0.00 (free-tier providers; per-node `cost` field
  summed across all 25 executed nodes).

## Changes used

Only prompt refinements and minimal code changes — no structural edits.
Relevant commits: UTF-8 encoding fixes (`4ae7a72`), gateway path fix for V9
(`ce806cc`), Playwright setup (`e5e8129`).
