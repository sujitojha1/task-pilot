# repo-genesis — Software Requirements Specification

| | |
|---|---|
| **Standard** | ISO/IEC/IEEE 29148:2018 (SRS information item, tailored) |
| **Syntax** | EARS — Easy Approach to Requirements Syntax |
| **System** | repo-genesis |
| **Status** | Draft v0.1 — 2026-06-10 |

---

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for **repo-genesis**, a browser-capable agent that bootstraps a plain-language idea into a complete, traceable GitHub project: repository, license, evidence-refined README, formal requirements, issues, and milestones — finishing with a replay of the run.

### 1.2 Scope
In scope: GitHub login verification, repository creation, similar-repo research and comparison, idea refinement, requirements generation, issue and milestone publishing, traceability review, and replay reporting. Out of scope: real authentication flows beyond a persistent logged-in browser profile, CAPTCHA circumvention, publishing targets other than GitHub (deferred), and modification of the host orchestrator.

### 1.3 Product overview
repo-genesis runs as a skill-catalogue entry on the Session 8/9 agent runtime (Planner → Researcher → Browser skill → Distiller → QA/Critic), using the four-layer browser cascade (extract → deterministic → a11y → vision) with a `gateway_blocked` recovery branch. See [README.md](../README.md) for the run narrative and [assignment.md](assignment.md) for course constraints.

### 1.4 Definitions
- **Target repository** — the new GitHub repository created from the user's idea.
- **Comparison table** — structured table of 3–5 similar repositories vs. evaluation criteria.
- **EARS patterns** — Ubiquitous ("The system shall…"), Event-driven ("WHEN…"), State-driven ("WHILE…"), Unwanted behavior ("IF…, THEN…"), Optional feature ("WHERE…").
- **Replay** — the per-run report defined in assignment item 8 (goal, DAG, layer choices, actions, screenshots/logs, data, table, turn/cost summary).
- **Verification methods** — **I**nspection, **D**emonstration, **T**est.

---

## 2. Functional requirements

### 2.1 Authentication precondition (AUTH)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-AUTH-001 | WHEN a run starts, the system shall verify that the persistent browser profile is logged into GitHub before performing any other action. | D |
| REQ-AUTH-002 | IF the user is not logged into GitHub, THEN the system shall halt the run without side effects and report the blocked state with remediation steps in the replay. | T |

### 2.2 Repository bootstrap (BOOT)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-BOOT-001 | WHEN authentication is verified, the system shall create the target repository with an Apache-2.0 license and a README.md containing the user's initial idea. | D |
| REQ-BOOT-002 | IF a repository with the target name already exists in the user's account, THEN the system shall halt and report without modifying the existing repository. | T |

### 2.3 Similar-repo research (RES)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-RES-001 | WHEN the target repository exists, the system shall identify 3 to 5 similar repositories via GitHub search. | D |
| REQ-RES-002 | The system shall perform at least three visible browser actions during research (e.g., search, sort, filter, open repository pages); passive scraping of search snippets shall not substitute for these actions. | D |
| REQ-RES-003 | WHEN a candidate repository is opened, the system shall read its README and extract purpose, key features, license, and activity signals. | T |
| REQ-RES-004 | IF fewer than three similar repositories are found, THEN the system shall broaden the search once, proceed with the repositories found, and record the deviation in the replay. | T |

### 2.4 Comparison and idea refinement (CMP)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-CMP-001 | WHEN research completes, the system shall produce a structured comparison table of the candidate repositories against common criteria. | I |
| REQ-CMP-002 | The system shall write the reference links and the comparison table into the target repository's README. | I |
| REQ-CMP-003 | WHEN the comparison table is complete, the system shall produce a refined objective for the idea and record it in the README together with its rationale. | I |

### 2.5 Requirements generation (SPEC)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-SPEC-001 | WHEN the refined objective is recorded, the system shall generate a `requirements.md` in the target repository structured per ISO/IEC/IEEE 29148:2018. | I |
| REQ-SPEC-002 | The system shall state every generated requirement in one of the five EARS patterns with a stable, unique identifier. | I |
| REQ-SPEC-003 | The system shall trace every generated requirement to the refined objective or to comparison evidence. | I |

### 2.6 Issue and milestone publishing (PUB)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-PUB-001 | WHEN `requirements.md` is committed, the system shall create issues one at a time, each containing a goal statement, acceptance criteria, a subtask checklist, and the requirement IDs it traces to. | D |
| REQ-PUB-002 | WHEN all issues are created, the system shall group them into logical milestones such that every issue belongs to exactly one milestone. | D |

### 2.7 Traceability review (REV)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-REV-001 | WHEN publishing completes, the system shall review `requirements.md` and verify the traceability chain: every requirement maps to at least one issue and every issue to a milestone. | T |
| REQ-REV-002 | IF the review finds an untraced requirement or an orphaned issue, THEN the system shall repair the gap once and report any remaining gaps in the replay. | T |

### 2.8 Browser cascade (BRW)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-BRW-001 | WHEN fetching or interacting with a page, the system shall attempt layers in order — extract, deterministic selectors, accessibility tree, vision — escalating only when the current layer fails. | T |
| REQ-BRW-002 | The system shall record the layer chosen for every browser step in the replay. | I |
| REQ-BRW-003 | IF a page presents a CAPTCHA, login wall, or rate limit, THEN the system shall classify the step as `gateway_blocked` and recover or report — never attempt circumvention. | T |

### 2.9 Replay and observability (REP)

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-REP-001 | WHEN a run ends (success or halt), the system shall emit a replay containing: original goal, planner DAG, browser path per step, actions taken, screenshots or page-state logs, extracted data, the comparison table, and turn count with cost summary. | D |
| REQ-REP-002 | The system shall account the cost of every LLM call in the replay using the gateway's pricing ledger. | T |

---

## 3. Constraints and non-functional requirements

| ID | Requirement (EARS) | Verify |
|---|---|---|
| REQ-CON-001 | The system shall integrate through the skill catalogue only; the orchestrator (`flow.py`) shall not be modified. | I |
| REQ-CON-002 | The system shall not use third-party agentic frameworks (LangChain, LlamaIndex, CrewAI, AutoGen). | I |
| REQ-CON-003 | The system shall license created repositories under Apache-2.0. | I |
| REQ-NFR-001 | WHERE a per-run cost budget is configured, IF projected spend exceeds the budget, THEN the system shall pause and report before continuing. | T |

---

## 4. Verification

Each requirement carries a verification method: **I** (inspect the produced artifact), **D** (demonstrate in the recorded run / YouTube demo), **T** (automated or scripted test). The assignment demo doubles as the demonstration evidence for all D-tagged requirements.

## 5. Traceability to assignment deliverables

| Assignment item (docs/assignment.md) | Covered by |
|---|---|
| 1. Original user goal | REQ-REP-001 |
| 2. Planner DAG | REQ-REP-001 |
| 3. Browser path chosen | REQ-BRW-001, REQ-BRW-002 |
| 4. Browser actions taken | REQ-RES-002, REQ-REP-001 |
| 5. Screenshots / page-state logs | REQ-REP-001 |
| 6. Extracted data | REQ-RES-003, REQ-REP-001 |
| 7. Final comparison table | REQ-CMP-001, REQ-CMP-002 |
| 8. Turn count and cost summary | REQ-REP-001, REQ-REP-002 |
| Orchestrator unmodified / no frameworks | REQ-CON-001, REQ-CON-002 |
