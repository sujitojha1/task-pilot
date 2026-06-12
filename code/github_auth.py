"""The github_auth skill — GitHub login precondition (REQ-AUTH-001/002).

Deterministic, non-LLM skill in the sandbox_executor / browser dispatch
family. It opens the PERSISTENT browser profile (the same identity every
GitHub-acting step will use), loads github.com, and reads the login state
from the `user-login` meta tag GitHub stamps on every page for an
authenticated session.

Contract with the orchestrator:

  - Logged in  → AgentResult(success=True) with the username in
    output.user; downstream GitHub-acting nodes (which the Planner wires
    to depend on this node) become ready. (REQ-AUTH-001)
  - Logged out → AgentResult(success=False,
    error_code="github_login_required") with remediation steps in BOTH
    output.remediation (so the replay shows them verbatim) and the error
    text (so the recovery Planner's FAILURE block carries them). The
    failed node never reaches "complete", so every node depending on it
    stays blocked — the run halts with no side effects, and planner.md
    instructs the recovery Planner to emit only a formatter that relays
    the remediation. (REQ-AUTH-002)

The check is read-only: one navigation, no clicks, no form posts.

CLI:
    uv run python github_auth.py            # run the check, print verdict
    uv run python github_auth.py --login    # open a headed browser on the
                                            # persistent profile; complete
                                            # the GitHub login (incl. 2FA),
                                            # the poller detects it and
                                            # closes the window for you
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

from schemas import AgentResult, NodeSpec

ROOT = Path(__file__).parent
# One profile for every GitHub-touching step of a run. Login once, reuse
# everywhere — this directory IS the "persistent browser profile" the
# requirements name.
PROFILE_DIR = ROOT / "state" / "browser_profile" / "github"

GITHUB_URL = "https://github.com/"
LOGIN_URL = "https://github.com/login"

ERROR_CODE = "github_login_required"

REMEDIATION_STEPS = [
    "Run: cd code && uv run python github_auth.py --login",
    "A browser window opens on the persistent profile. Sign in to GitHub "
    "(complete 2FA if prompted).",
    "The window closes by itself once the login is detected.",
    "Re-run the original goal; the auth check will now pass.",
]


def interpret_login_meta(user_login: str | None) -> dict:
    """Pure decision core, unit-testable without a browser.

    GitHub stamps `<meta name="user-login" content="<username>">` on every
    page for an authenticated session; anonymous sessions render it empty
    or omit it. Non-empty content == logged in.
    """
    user = (user_login or "").strip()
    if user:
        return {"logged_in": True, "user": user}
    return {"logged_in": False, "user": None}


def pack_result(state: dict, *, elapsed: float = 0.0) -> AgentResult:
    """Map a login state onto the orchestrator contract described above."""
    if state.get("logged_in"):
        return AgentResult(
            success=True, agent_name=GitHubAuthSkill.NAME,
            output={
                "logged_in": True,
                "user": state.get("user"),
                "profile_dir": str(PROFILE_DIR),
            },
            elapsed_s=elapsed,
        )
    remediation = " | ".join(REMEDIATION_STEPS)
    return AgentResult(
        success=False, agent_name=GitHubAuthSkill.NAME,
        output={
            "logged_in": False,
            "blocked": ERROR_CODE,
            "remediation": REMEDIATION_STEPS,
            "profile_dir": str(PROFILE_DIR),
        },
        error=(f"{ERROR_CODE}: the persistent browser profile is not "
               f"logged into GitHub. The run was halted before any GitHub "
               f"action (no side effects). Remediation: {remediation}"),
        error_code=ERROR_CODE,
        elapsed_s=elapsed,
    )


async def read_login_state(*, headless: bool = True,
                           timeout_ms: int = 45_000) -> dict:
    """Open the persistent profile, load github.com, read the login meta."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=headless,
            viewport={"width": 1366, "height": 900},
        )
        try:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto(GITHUB_URL, wait_until="domcontentloaded",
                            timeout=timeout_ms)
            user_login = await page.evaluate(
                "() => document.querySelector('meta[name=\"user-login\"]')"
                "?.content ?? null"
            )
            return interpret_login_meta(user_login)
        finally:
            await ctx.close()


class GitHubAuthSkill:
    NAME = "github_auth"

    async def run(self, node: NodeSpec | None = None) -> AgentResult:
        t0 = time.time()
        try:
            state = await read_login_state()
        except Exception as e:  # browser/profile fault — report, don't raise
            return AgentResult(
                success=False, agent_name=self.NAME,
                output={"logged_in": False,
                        "remediation": REMEDIATION_STEPS,
                        "profile_dir": str(PROFILE_DIR)},
                error=(f"auth check could not run "
                       f"({type(e).__name__}: {e}); treat as not verified "
                       f"and do not act on GitHub"),
                elapsed_s=time.time() - t0,
            )
        return pack_result(state, elapsed=time.time() - t0)


# ── CLI ──────────────────────────────────────────────────────────────────────

async def _login_flow(poll_s: float = 3.0, wall_clock_s: float = 600.0) -> dict:
    """Headed login on the persistent profile. Polls the login meta while
    the user signs in; closes the window once a username appears."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=False,
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded",
                        timeout=45_000)
        print(f"[github_auth] complete the login in the browser window "
              f"(profile: {PROFILE_DIR})")
        deadline = time.time() + wall_clock_s
        try:
            while time.time() < deadline:
                await asyncio.sleep(poll_s)
                if not ctx.pages:  # user closed the window
                    break
                user_login = await ctx.pages[0].evaluate(
                    "() => document.querySelector('meta[name=\"user-login\"]')"
                    "?.content ?? null"
                )
                state = interpret_login_meta(user_login)
                if state["logged_in"]:
                    print(f"[github_auth] logged in as "
                          f"{state['user']} — closing window")
                    return state
        except Exception:                              # noqa: BLE001
            pass  # window closed mid-poll; fall through to a fresh check
        finally:
            try:
                await ctx.close()
            except Exception:                          # noqa: BLE001
                pass
    return await read_login_state()


def main() -> None:
    if "--login" in sys.argv[1:]:
        state = asyncio.run(_login_flow())
    else:
        state = asyncio.run(read_login_state())
    if state["logged_in"]:
        print(f"logged in as {state['user']}")
        return
    print(f"NOT logged in ({ERROR_CODE}). Remediation:")
    for i, step in enumerate(REMEDIATION_STEPS, 1):
        print(f"  {i}. {step}")
    sys.exit(1)


if __name__ == "__main__":
    main()
