# github_auth — login precondition (REQ-AUTH-001 / REQ-AUTH-002)

This skill never reaches a model: the dispatcher routes it to
`github_auth.GitHubAuthSkill` (the same non-LLM dispatch family as
`sandbox_executor` and `browser`). This file documents the contract for
humans and keeps the registry uniform.

## What it does

Opens the persistent browser profile (`state/browser_profile/github`),
loads github.com, and reads the `user-login` meta tag GitHub stamps on
every authenticated page. One navigation, read-only, no side effects.

## Output contract

Logged in (REQ-AUTH-001):

    {"logged_in": true, "user": "<username>", "profile_dir": "..."}

Logged out (REQ-AUTH-002): the node FAILS with
`error_code=github_login_required`; `output.remediation` lists the exact
steps (also embedded in the error text so the recovery Planner's FAILURE
block carries them). Downstream GitHub-acting nodes — which the Planner
wires to depend on this node — stay blocked, so the run halts with no
side effects. The recovery Planner emits only a formatter relaying the
remediation (see planner.md).

## Remediation (what the user runs)

    cd code && uv run python github_auth.py --login

A headed browser opens on the persistent profile; complete the GitHub
login (including 2FA). The window closes itself once the login is
detected. Re-run the original goal.
