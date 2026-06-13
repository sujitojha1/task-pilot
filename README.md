# repo-genesis

> Give it an idea in plain language. It verifies you're logged into GitHub, creates the repo, refines the idea against 3–5 similar projects found on the live web, derives formal requirements, and publishes traceable issues and milestones — all through the browser, with a replay of everything it did and what it cost.

---

## What is this?

**repo-genesis** is an agentic system that bootstraps a raw idea into a complete, traceable GitHub project. It doesn't plan blind: before specifying anything, it researches similar repositories, compares them, and refines the objective with evidence. Every issue it opens traces back to a formal requirement; every requirement traces back to the refined idea.

No manual ticket writing. No blank-page paralysis. No decisions without evidence.

---

## How to run

Prerequisites: [uv](https://docs.astral.sh/uv/), Python 3.11+.

**1. Install dependencies**

```bash
cd gateway && uv sync
cd ../code && uv sync
uv run playwright install chromium   # browsers for the Browser skill
```

**2. Configure environment**

- `code/.env` — copy from `code/.env.example` and set `TAVILY_API_KEY` (web search).
- `gateway/.env` — set at least one LLM provider key, e.g. `GEMINI_API_KEY` (also supported: `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `NVIDIA_API_KEY`, `OPEN_ROUTER_API_KEY`, `GITHUB_ACCESS_TOKEN`, or a local `OLLAMA_URL`).

**3. Start the Gateway V9**

```bash
cd gateway
uv run python main.py   # serves on :8109 (override with GATEWAY_V9_PORT)
```

Verify it's up: `curl http://localhost:8109/v1/routers`.

**4. Run a goal**

```bash
cd code
uv run python flow.py "When was Claude Shannon born and what did he contribute to information theory?"
```

Resume an interrupted session with `uv run python flow.py --resume <session-id>`.

**5. Inspect the run**

- `uv run python replay.py` lists sessions; `uv run python replay.py <session-id>` replays one (DAG, per-node status, browser layer choices).
- Raw artifacts live in `code/state/sessions/<session-id>/` — `graph.json`, `query.txt`, `nodes/n_*.json` (exact prompts and results), and `browser/` (per-turn screenshots when the Browser skill ran).
- The gateway records every LLM call (tokens, latency, agent, session) in its SQLite ledger for cost accounting.

`./run_demo.sh` walks the test suite plus five canonical queries (`./run_demo.sh browser` exercises the Browser skill end-to-end). Note its gateway-startup hint references an old `../llm_gatewayV9` path — the gateway lives in `gateway/` in this repo.

---

## How a run works

1. **Verify** — Confirm the user is logged into GitHub (persistent browser profile). If not, stop and report cleanly — never act half-authenticated
2. **Bootstrap** — Create the repository with an Apache-2.0 license and a README.md holding the initial idea
3. **Research** — The **Researcher** searches GitHub for 3–5 similar repositories; the **Browser skill** opens each one (search, sort, open detail pages — visible actions, never passive scraping) and reads its README
4. **Compare & refine** — The **Distiller** builds a **structured comparison table** of the similar repos; the idea's objective is broadened and refined against it, and the reference links are written into the README
5. **Specify** — Write `requirements.md` following **IEEE 29148:2018**, with each requirement stated in **EARS** syntax and given a stable ID (REQ-001, …)
6. **Publish** — Create issues one by one, each traced to its requirement IDs, then group them into logical milestones on the project board
7. **Review** — The **QA/Critic** reviews `requirements.md` and the traceability chain: every requirement has an issue, every issue has a milestone
8. **Replay** — Every run emits a replay view: original goal, planner DAG, browser path chosen per step (extract / deterministic / a11y / vision / blocked), actions taken, screenshots & page-state logs, extracted data, the comparison table, and turn count + cost summary

---

## Core concepts

| Concept | Description |
|---|---|
| **Comparison table** | The evidence artifact — 3–5 similar repos vs. criteria, gathered by reading their READMEs on live pages |
| **Requirement** | An EARS-syntax statement in `requirements.md` (IEEE 29148:2018) with a stable ID |
| **Issue** | A single unit of work, traced to one or more requirement IDs |
| **Milestone** | A logical grouping of issues with a success condition |
| **Traceability** | The unbroken chain: idea → refined objective → requirement → issue → milestone |
| **Replay** | The full trace of a run — what the agent saw, chose, clicked, extracted, and spent |

---

## Interactive course (dev documentation)

`course/index.html` is an interactive, single-page HTML course that teaches how this codebase works — the agent flow, the skill catalogue, the browser cascade, and the gateway — with animated visualizations, quizzes, and plain-English code translations. Open it directly in a browser; it works offline (the only external fetch is Google Fonts, which degrades gracefully).

This is **developer documentation for this repository only**, not a feature of the agent: it is generated with the [codebase-to-course](https://github.com/zarazhangrui/codebase-to-course) Claude Code skill vendored at `.claude/skills/codebase-to-course/`, which is deliberately *not* registered in `code/agent_config.yaml`. To regenerate after significant architecture changes, ask Claude Code to "regenerate the course for this repo" (the skill triggers on that), then run `bash build.sh` inside `course/` to reassemble `index.html` from the per-module files.

---

## Design principles

- **Verify before act** — login state is a precondition, checked first; a blocked gateway is reported, not worked around
- **Cheapest correct path** — the browser skill is a four-layer cascade: static extract → deterministic selectors → accessibility tree → vision (set-of-marks). Escalate only on failure
- **Evidence before specification** — the idea is refined against real, comparable projects before a single requirement is written
- **Traceable by construction** — issues and milestones are generated *from* requirements, so the chain never needs reconstructing
- **Browser-native** — visible interactions on real dynamic pages, both for research and for publishing through the actual GitHub UI
- **Plugs in as a skill** — the orchestrator is untouched; repo-genesis is a skill-catalogue entry plus prompts. No LangChain / LlamaIndex / CrewAI / AutoGen
- **Transparent** — the replay shows every decision, every layer escalation, and the cost ledger

---

## Roadmap

**Infrastructure — built and validated:**

- [x] GitHub login verification — persistent browser profile, clean abort when absent (`github_auth.py`, `tests/test_github_auth.py`)
- [x] Browser cascade — extract → deterministic → a11y → vision, with `gateway_blocked` recovery (see `code/VALIDATION.md`)
- [x] Replay viewer + cost accounting — DAG, per-step layer choices, screenshots/page-state logs, gateway cost ledger (`replay.py`)

**repo-genesis pipeline — prompt-wired into the Planner, not yet demonstrated end-to-end against a live GitHub repo:**

- [ ] Repo bootstrap: Apache-2.0 license + initial README — slug derivation and duplicate-name guard now specified (REQ-BOOT-002/003/004, `planner.md`); still needs an end-to-end run to prove them
- [ ] Similar-repo research against GitHub search with structured comparison table and reference links
- [ ] Idea refinement from comparison evidence
- [ ] `requirements.md` generation (IEEE 29148:2018 + EARS, stable IDs) — `specifier` skill exists, not yet run end-to-end
- [ ] Issue creation traced to requirements; milestone grouping — `publisher` skill exists, browser form-fill unproven
- [ ] Traceability review pass (QA/Critic) — generic critic only; the dedicated traceability-repair pass (REQ-REV-002) is not yet built

---

## Status

The shared agent infrastructure is built and validated: the GitHub login precondition, the four-layer browser cascade, recovery/re-planning, the gateway with its cost ledger, and the replay viewer all work and are exercised by tests and recorded runs (`code/VALIDATION.md`, `docs/run-report-laptops-under-80k.md`).

The repo-genesis vertical itself — bootstrap → research → compare → specify → publish → review — is defined as skill prompts and wired into the Planner, but has not yet been demonstrated as a complete run against a live GitHub repository. The only recorded end-to-end run to date is the generic browser-comparison task (laptops under ₹80,000), which exercises the cascade but not the GitHub-acting pipeline.

GitHub actions are performed through the persistent browser profile (log in once via `uv run python github_auth.py --login`), **not** an API token — there is no `GITHUB_TOKEN`/REST path in the design.

Built for the Session 9 assignment — see [docs/assignment.md](docs/assignment.md) for the full spec (deliverables, constraints, submission checklist).
