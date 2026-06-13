"""Tests for BaseDriver._enumerate_with_retry — the in-driver recovery for
the Playwright navigation race.

`enumerate_interactives` runs a `page.evaluate` pass each turn. When the
previous turn's action triggered a navigation that is still in flight (typical
right after a GitHub form submit), Playwright aborts with "Execution context
was destroyed, most likely because of a navigation". That is transient: it
clears once the new document commits. Before the retry this killed the whole
browse on its first turn (the 0.0s Browser failures in session logs) and cost
a full upstream Planner re-plan.

These tests stub `enumerate_interactives` (patched on the driver module) and a
minimal page so the retry logic is exercised without a real browser.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from browser import driver as driver_mod
from browser.driver import A11yDriver, DriverConfig
from browser.dom import PageSnapshot


def _snapshot() -> PageSnapshot:
    return PageSnapshot(elements=[], dpr=1.0, viewport_w=800, viewport_h=600)


class _FakePage:
    """Records wait_for_load_state calls; everything else is unused here."""

    def __init__(self) -> None:
        self.url = "https://github.com/new"
        self.load_state_waits = 0

    async def wait_for_load_state(self, state: str = "load", timeout: float = 0):
        self.load_state_waits += 1


def _make_driver() -> A11yDriver:
    # client is unused by _enumerate_with_retry; pass None.
    return A11yDriver(_FakePage(), None, DriverConfig(goal="g", max_steps=3))


def _nav_error() -> Exception:
    return Exception(
        "Page.evaluate: Execution context was destroyed, most likely "
        "because of a navigation."
    )


@pytest.mark.asyncio
async def test_retry_recovers_after_transient_navigation(monkeypatch) -> None:
    drv = _make_driver()
    calls = {"n": 0}
    snap = _snapshot()

    async def flaky(page):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _nav_error()      # first turn races a navigation
        return snap                  # settles on retry

    monkeypatch.setattr(driver_mod, "enumerate_interactives", flaky)
    out = await drv._enumerate_with_retry()
    assert out is snap, "retry should return the snapshot once the nav settles"
    assert calls["n"] == 2, "should have retried exactly once"
    assert drv.page.load_state_waits >= 1, "retry should wait for load state"


@pytest.mark.asyncio
async def test_retry_gives_up_after_attempts_and_reraises(monkeypatch) -> None:
    drv = _make_driver()

    async def always_racing(page):
        raise _nav_error()

    monkeypatch.setattr(driver_mod, "enumerate_interactives", always_racing)
    with pytest.raises(Exception, match="Execution context was destroyed"):
        await drv._enumerate_with_retry(attempts=2)


@pytest.mark.asyncio
async def test_retry_does_not_swallow_unrelated_errors(monkeypatch) -> None:
    # A genuine DOM/JS fault is NOT the navigation race — it must propagate
    # immediately, not burn retries pretending the page will settle.
    drv = _make_driver()
    calls = {"n": 0}

    async def real_fault(page):
        calls["n"] += 1
        raise Exception("TypeError: cannot read property 'x' of null")

    monkeypatch.setattr(driver_mod, "enumerate_interactives", real_fault)
    with pytest.raises(Exception, match="cannot read property"):
        await drv._enumerate_with_retry()
    assert calls["n"] == 1, "unrelated error must not be retried"
