# task-pilot

> Give it a goal in plain language. It researches the live web to compare your options, decides with evidence, then publishes a fully structured plan — milestones, issues, board cards — through the browser. Every run ends with a replay of exactly what it did and what it cost.

---

## What is this?

**task-pilot** is an agentic system that takes a high-level goal and turns it into a structured GitHub Project board — but it doesn't plan blind. Before writing a single ticket, it browses the real web to compare the candidate tools, libraries, or approaches the plan depends on. The comparison decides the stack; the stack shapes the milestones.

No manual ticket writing. No blank-page paralysis. No decisions without evidence.

---

## How a run works

1. **Input** — You give the agent a goal in natural language
2. **Compare** — The agent browses live, dynamic pages (search, filter, sort, open detail pages — real interactions, not passive scraping) to compare candidate tools/approaches, producing a **structured comparison table**
3. **Plan** — The winning option feeds decomposition: milestones, then discrete issues with goal, acceptance criteria, subtasks, labels, priority
4. **Publish** — The agent drives the actual GitHub UI to create the board, milestones, and issues, and place cards in columns
5. **Replay** — Every run emits a replay view: original goal, planner DAG, browser path chosen per step (extract / deterministic / a11y / vision / blocked), actions taken, screenshots & page-state logs, extracted data, the comparison table, and turn count + cost summary

---

## Core concepts

| Concept | Description |
|---|---|
| **Comparison table** | The evidence artifact — candidates vs. criteria, gathered from live pages, embedded in the plan's epic issue |
| **Milestone** | A high-level phase of work with a target date and success condition |
| **Issue** | A single unit of work tied to a milestone, with goal + acceptance criteria + subtask checklist |
| **Card** | The issue on the project board, in the right column (Todo / In Progress / Done) |
| **Replay** | The full trace of a run — what the agent saw, chose, clicked, extracted, and spent |

---

## Design principles

- **Cheapest correct path** — the browser skill is a four-layer cascade: static extract → deterministic selectors → accessibility tree → vision (set-of-marks). Escalate only on failure; report cleanly when blocked
- **Plain language in, structured plan out** — no templates to fill, no forms to click through
- **Browser-native** — visible interactions on real dynamic pages, both for research (filter/sort/expand) and for publishing (GitHub UI, via a persistent logged-in profile)
- **Plugs in as a skill** — the orchestrator is untouched; task-pilot is a skill-catalogue entry plus prompts. No LangChain / LlamaIndex / CrewAI / AutoGen
- **Transparent** — the replay shows every decision, every layer escalation, and the cost ledger

---

## Roadmap

- [ ] Natural language goal intake
- [ ] Live-web comparison phase with structured comparison table
- [ ] Milestone decomposition + issue generation (goal, acceptance criteria, subtasks)
- [ ] GitHub Project board creation and card placement via browser
- [ ] Replay viewer (DAG, layer choices, actions, screenshots, data, costs)
- [ ] Later: Linear, Jira, Notion as publish targets

---

## Status

Early stage. The architecture is defined; implementation is in progress.
