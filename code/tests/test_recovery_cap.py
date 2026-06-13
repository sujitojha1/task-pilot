"""Tests for the per-branch node-failure recovery cap.

Mirrors the critic-fail cap (test_recovery.py) for the OTHER recovery path:
when a node fails with `upstream_failure` the Executor queues a recovery
Planner. Before this cap, that loop was unbounded — a Browser node that hit
the same navigation race or step cap on every attempt re-planned forever, and
each recovery Planner re-emitted the same failing work, marching the graph to
MAX_NODES doing nothing useful (observed in session s8-3c96dada).

The cap charges every failure to a recovery ROOT. A node spliced in by a
recovery inherits its parent Planner's `recovery_root`, so re-emitted work
counts against the same budget instead of escaping it with a fresh node id.
These tests pin (1) the root helper, (2) the lineage propagation in
Graph.extend_from, and (3) the two composing into a real cap.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flow import Graph, MAX_RECOVERIES_PER_BRANCH
from recovery import recovery_root_for
from schemas import AgentResult, NodeSpec


# ── stub registry: extend_from only reads internal_successors + critic ──────
class _StubDef:
    internal_successors: list[str] = []
    critic = False


class _StubRegistry:
    def get(self, name: str) -> _StubDef:
        return _StubDef()


def _browser_successor(label: str = "retry") -> AgentResult:
    return AgentResult(
        success=True, agent_name="planner",
        successors=[NodeSpec(skill="browser", inputs=[],
                             metadata={"label": label, "url": "https://x"})],
    )


# ── (1) the root helper ─────────────────────────────────────────────────────
def test_recovery_root_for_first_failure_is_self() -> None:
    assert recovery_root_for(None, "n:8") == "n:8"
    assert recovery_root_for({}, "n:8") == "n:8"
    assert recovery_root_for({"url": "https://x"}, "n:8") == "n:8"


def test_recovery_root_for_inherits_lineage() -> None:
    # A node spliced in by a recovery carries recovery_root; its own failure
    # is charged to that root, not to its fresh id.
    assert recovery_root_for({"recovery_root": "n:8"}, "n:15") == "n:8"


# ── (2) extend_from propagation ─────────────────────────────────────────────
def test_extend_from_propagates_recovery_root_to_children() -> None:
    g = Graph()
    planner = g.add_node("planner", inputs=["USER_QUERY"],
                         metadata={"recovery_root": "n:8"})
    g.g.nodes[planner]["status"] = "complete"
    added = g.extend_from(planner, _browser_successor(), registry=_StubRegistry())
    assert added, "expected a spliced-in child"
    assert g.g.nodes[added[0]]["metadata"].get("recovery_root") == "n:8", \
        "child must inherit recovery_root so the cap counts the lineage"


def test_extend_from_without_root_leaves_children_unstamped() -> None:
    # A normal (non-recovery) Planner must NOT stamp recovery_root — otherwise
    # every node would look like recovery lineage and share one budget.
    g = Graph()
    planner = g.add_node("planner", inputs=["USER_QUERY"])
    added = g.extend_from(planner, _browser_successor(), registry=_StubRegistry())
    assert added
    assert "recovery_root" not in g.g.nodes[added[0]]["metadata"]


# ── (3) the two composed into an actual cap ─────────────────────────────────
def test_recovery_cap_blocks_second_failure_in_lineage() -> None:
    """Reproduce the Executor's cap arithmetic: an original Browser failure
    gets one recovery; the re-emitted Browser node's later failure is capped
    because it resolves to the same root that already spent its budget."""
    g = Graph()
    reg = _StubRegistry()
    recovery_counts: dict[str, int] = {}
    cap_hit: list[str] = []

    # Original browser node fails → first recovery is allowed.
    orig = g.add_node("browser", inputs=[], metadata={"url": "https://x"})
    root = recovery_root_for(g.g.nodes[orig].get("metadata"), orig)
    assert root == orig
    assert recovery_counts.get(root, 0) < MAX_RECOVERIES_PER_BRANCH
    recovery_counts[root] = recovery_counts.get(root, 0) + 1
    rec = g.add_node("planner", inputs=["USER_QUERY"],
                     metadata={"recovers": orig, "recovery_root": root})

    # Recovery Planner re-emits a fresh browser node (the exact behaviour the
    # cap exists to contain). It inherits the lineage root via extend_from.
    child = g.extend_from(rec, _browser_successor(), registry=reg)[0]
    child_root = recovery_root_for(g.g.nodes[child].get("metadata"), child)
    assert child_root == root, "re-emitted node must share the lineage root"

    # The re-emitted child fails too → budget already spent → capped.
    if recovery_counts.get(child_root, 0) >= MAX_RECOVERIES_PER_BRANCH:
        cap_hit.append(child)
    assert cap_hit == [child], "second failure in the lineage must be capped"
