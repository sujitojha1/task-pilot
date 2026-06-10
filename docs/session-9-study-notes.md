# Session 9 Study Notes — Browser Agents & the Autonomous Web

> Closes [issue #1](https://github.com/sujitojha1/repo-genesis/issues/1) — "Study Session 9: course video and lesson content"
>
> Sources: [Session video](https://www.youtube.com/watch?v=FE1PA0sRxEY&list=PLiVVtn2obw-N6zUcXD7g35fKQ7PBNyUhF&index=10) · [Lesson page](https://axiom.theschoolofai.in/courses/cmox5yhwl000107pgrjx41sqk/sessions/cmq1qpms50cla08ql71j46z18/lesson?zen=1) · `docs/class/` (slides PDF + transcript) · [docs/assignment.md](assignment.md)

## 1. What Session 9 adds

Session 8's `web_search` + `fetch_url` handle static pages only. They fail on JavaScript-rendered pages, click-revealed widgets (popovers, dropdowns, tabs), multi-page flows, and data that appears only after filtering or sorting. Session 9 adds exactly **three things** — nothing in the orchestrator changes:

1. **A Browser skill** — a new skill-catalogue entry (agent config + prompt; small dispatch branch in `skills.py`; `flow.py` untouched). The planner only learns that the skill exists, with metadata: *"fetches and interacts with web pages through a four-layer cascade; accepts URL and goal; returns browser output with the chosen layer."*
2. **Gateway V9** — the LLM gateway now accepts **images as prompts** (first time). This is what powers the vision layer: a screenshot goes up, the VLM returns which mark/box to click or bounding-box coordinates (e.g., "pixel 224,50–250,70 has the login button"), and the click happens programmatically.
3. **Teaching examples** — five worked examples, one per layer plus a blocked case (see §3).

The whole skill is built from scratch with Playwright + httpx + trafilatura + Pillow — **no LangChain / LlamaIndex / CrewAI / AutoGen** (Crawl4AI is used by the older MCP tools, not here).

## 2. The four-layer cascade (acceptance criterion 1)

Core principle: **pick the cheapest correct path**. Layers 1, 2a, 2b cost zero LLM calls (or a cheap small-LLM judgment); only escalate to vision when everything below fails. After each layer, a small critic-style check verifies the output is actually useful (≈200 chars read, must contain at least one keyword from the goal) — "I got 35 KB of something" is not success.

**Precondition — `gateway_blocked`:** before any layer runs, the gateway checks for CAPTCHA, login wall, geographic block, or rate limit. If hit, the step is classified `gateway_blocked` and the agent recovers or reports — it never attempts circumvention (ethical boundary; also gets your accounts banned).

| Layer | Name | Mechanism | When it applies | Cost |
|---|---|---|---|---|
| 1 | **Extract** | `httpx` GET + `trafilatura` → markdown. No browser launched. | Static, server-rendered pages. Example: Hacker News — 35 KB HTML → 9.4 KB markdown, sub-second, zero LLM cost. | Free |
| 2a | **Deterministic** | Headless Playwright + handwritten **CSS selectors** (`.product-title`, `.a-price` …). | JS-rendered pages with stable, well-tagged markup. Covers ~80% of cases where layer 1 fails. Example: Amazon product pages — 2.7 MB HTML → 2.2 KB clean JSON (~1%). Needs a "polite" browser context (real user-agent, JS enabled, webdriver markers handled) or the site serves a CAPTCHA instantly. | Free |
| 2b | **A11y** (accessibility tree) | Playwright pulls the browser's parallel **accessibility tree** (the structure screen readers use; ARIA roles/names) and sends that compact structure to a cheap LLM, which picks the action. | Dynamic pages where selectors break or aren't maintained (fast-moving sites). Example: Hugging Face — 1.1 MB page → ~30 KB tree; goal "models → filter text-generation → filter transformers → sort by likes → read top 3". Size reduction is 100–600×. | Cheap LLM |
| 3 | **Vision** (set-of-marks) | Screenshot → Playwright draws numbered boxes over every clickable element (where the cursor would turn to a pointer) → resized for DPR → sent to a **VLM** (Gemini flash here; small local VLMs ≤8 GB also work) → "click box 4". | Canvas/SVG apps and pages where there is no useful DOM, no selectors, no a11y tree: Excalidraw, tldraw, Photopea, p5.js/openprocessing, Chrome Dino, shadow-DOM demos. Most expensive and slowest — every turn is a photo + VLM call. | VLM call |
| — | **Gateway blocked** | Classify, then recover or report. | CAPTCHA / login wall / geo block / rate limit. Example: Redfin blocks immediately. | — |

**One-line decision rule:** *static text → extract; stable selectors → deterministic; meaningful a11y tree → a11y; only pixels → vision; CAPTCHA/login/rate-limit → blocked.*

### Engineering details worth remembering

- **State re-sync:** when an action changes the DOM (a popover opens, a dropdown renders new options), the LLM must be re-told the new page state. The Hugging Face example failed on turn 1 because the sort popover's options weren't in the first a11y summary; turn 2 included them and succeeded. This bug recurred across EAG v1/v2/v3.
- **DPR (device pixel ratio):** screenshots from high-DPI screens must be resized before the VLM call, and returned coordinates scaled back — otherwise "click 22,22" lands in the wrong place. Handled in the shared code.
- **Element dedupe:** overlapping/invisible elements (tiny SVG rects, overlay divs) must be deduplicated before drawing marks, or the VLM clicks the wrong thing.
- **Gateway fixes shipped this session:** V9 client default URL corrected (was pointing at 8108), SQLite long-run hang fixed, GitHub-Models vision failover query fixed, Gemini↔GitHub cooling/routing race fixed, planner "running amnesia" fixed (failure report now carried into the fresh planner node so the graph resumes instead of replanning from step 1), and the critic now receives the original user query so it stops rejecting correct off-context outputs.

### Glossary quick reference

`httpx` HTTP client (layer 1) · `trafilatura` HTML→clean text (layer 1) · **Playwright** browser automation over Chromium/Firefox/WebKit (layers 2a/2b/3) · **CDP** Chrome DevTools Protocol (e.g., full-page screenshots) · **ARIA** accessible-markup standard · **A11y tree** the browser's parallel accessibility structure · **set-of-marks** numbered boxes on a screenshot so a VLM can pick an element · **VLM** vision language model · **DPR** device pixel ratio · **headless browser** rendered in memory, no window.

## 3. Assignment: the 8 replay deliverables + submission checklist (acceptance criterion 2)

Full spec in [docs/assignment.md](assignment.md). Task: a real **comparison task** with ≥3 visible browser actions (search / filter / sort / open detail pages / switch tabs / expand / submit form); passive snippet-scraping is not accepted. Pipeline: User Goal → Planner → Researcher (candidate URLs) → Browser skill (cascade) → Distiller → QA/Critic → Replay Viewer → Final comparison table. Orchestrator must not be modified — everything plugs in via the skill catalogue.

The replay viewer/report must show all **8 deliverables** ([assignment.md](assignment.md) "Required output"; mapped to requirement IDs in [requirements.md](requirements.md) §5):

| # | Replay deliverable | Traces to |
|---|---|---|
| 1 | Original user goal | REQ-REP-001 |
| 2 | Planner DAG | REQ-REP-001 |
| 3 | Browser path chosen: extract / deterministic / a11y / vision / blocked | REQ-BRW-001, REQ-BRW-002 |
| 4 | Browser actions taken | REQ-RES-002, REQ-REP-001 |
| 5 | Screenshots or page-state logs | REQ-REP-001 |
| 6 | Extracted data | REQ-RES-003, REQ-REP-001 |
| 7 | Final comparison table | REQ-CMP-001, REQ-CMP-002 |
| 8 | Turn count and cost summary | REQ-REP-001, REQ-REP-002 |

**Submission checklist** ([assignment.md](assignment.md) "Submission"):

- [ ] YouTube demo
- [ ] GitHub repo
- [ ] Replay trace/log
- [ ] Final comparison output
- [ ] Short architecture note

Constraints: orchestrator unmodified (REQ-CON-001), no third-party agentic frameworks (REQ-CON-002).

## 4. How this informs repo-genesis requirements

| Requirement | What Session 9 establishes |
|---|---|
| **REQ-BRW-001** (try layers in order, escalate on failure) | The cascade order extract → deterministic → a11y → vision and the "cheapest correct path" rationale (§2). |
| **REQ-BRW-002** (record chosen layer per step) | Replay deliverable #3; the skill already returns the chosen layer in its output. |
| **REQ-BRW-003** (`gateway_blocked` on CAPTCHA/login/rate-limit; never circumvent) | The gateway precondition and the explicit ethical line drawn in the session (Redfin example). |
| **REQ-REP-001** (replay with all 8 items) | The required-output list in §3; the replay viewer sits after QA/Critic in the reference pipeline. |
