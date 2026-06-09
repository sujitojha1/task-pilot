# task-pilot

> A browser-controlled agent that breaks any task into structured milestones, issues, and project board cards — with goals, acceptance criteria, and subtasks auto-generated.

---

## What is this?

**task-pilot** is an agentic system that takes a high-level goal — described in plain language — and automatically decomposes it into a fully structured plan inside a GitHub Project board.

You describe what you want to build or achieve. task-pilot figures out the milestones, creates the issues, writes the acceptance criteria, and populates the board. No manual ticket writing. No blank-page paralysis.

---

## How it works

1. **Input** — You give the agent a task in natural language
2. **Plan** — The agent breaks it down into milestones, then further into discrete, actionable issues
3. **Structure** — Each issue is formatted with a goal, acceptance criteria, subtasks, labels, priority, and milestone
4. **Publish** — The agent uses browser control to create the project board, push milestones, and open issues

---

## Core concepts

| Concept | Description |
|---|---|
| **Milestone** | A high-level phase of work with a target date and success condition |
| **Issue** | A single unit of work tied to a milestone |
| **Card** | The issue on the project board, in the right column (Todo / In Progress / Done) |
| **Structured goal** | Every issue has a goal statement, acceptance criteria, and subtask checklist |

---

## Design principles

- **Plain language in, structured plan out** — no templates to fill, no forms to click through
- **Browser-native** — operates through the actual GitHub UI, not just the API
- **Composable** — the planner, the browser driver, and the board publisher are separate layers
- **Transparent** — every card shows exactly what the agent decided and why

---

## Roadmap

- [ ] Natural language task intake
- [ ] Milestone decomposition with target dates
- [ ] Issue generation with goal + acceptance criteria + subtasks
- [ ] GitHub Project board creation and card placement
- [ ] Support for Linear, Jira, and Notion as publish targets
- [ ] Replay viewer

---

## Status

Early stage. The architecture is defined; implementation is in progress.
