"""Unit tests for the github_auth skill."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add the parent directory containing github_auth to path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from github_auth import (
    ERROR_CODE,
    REMEDIATION_STEPS,
    GitHubAuthSkill,
    interpret_login_meta,
    pack_result,
)
from schemas import AgentResult


def test_interpret_login_meta_logged_in() -> None:
    res = interpret_login_meta("sujitojha1")
    assert res == {"logged_in": True, "user": "sujitojha1"}

    res = interpret_login_meta("  sujitojha1  ")
    assert res == {"logged_in": True, "user": "sujitojha1"}


def test_interpret_login_meta_logged_out() -> None:
    res = interpret_login_meta(None)
    assert res == {"logged_in": False, "user": None}

    res = interpret_login_meta("")
    assert res == {"logged_in": False, "user": None}

    res = interpret_login_meta("   ")
    assert res == {"logged_in": False, "user": None}


def test_pack_result_logged_in() -> None:
    state = {"logged_in": True, "user": "sujitojha1"}
    res = pack_result(state, elapsed=1.5)
    assert isinstance(res, AgentResult)
    assert res.success is True
    assert res.agent_name == "github_auth"
    assert res.output["logged_in"] is True
    assert res.output["user"] == "sujitojha1"
    assert "profile_dir" in res.output
    assert res.elapsed_s == 1.5
    assert res.error is None
    assert res.error_code is None


def test_pack_result_logged_out() -> None:
    state = {"logged_in": False, "user": None}
    res = pack_result(state, elapsed=2.0)
    assert isinstance(res, AgentResult)
    assert res.success is False
    assert res.agent_name == "github_auth"
    assert res.output["logged_in"] is False
    assert res.output["blocked"] == ERROR_CODE
    assert res.output["remediation"] == REMEDIATION_STEPS
    assert res.error_code == ERROR_CODE
    assert ERROR_CODE in res.error
    assert " | ".join(REMEDIATION_STEPS) in res.error
    assert res.elapsed_s == 2.0


@pytest.mark.asyncio
async def test_skill_run_logged_in() -> None:
    skill = GitHubAuthSkill()
    with patch("github_auth.read_login_state", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = {"logged_in": True, "user": "sujitojha1"}
        result = await skill.run()
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.output["user"] == "sujitojha1"


@pytest.mark.asyncio
async def test_skill_run_logged_out() -> None:
    skill = GitHubAuthSkill()
    with patch("github_auth.read_login_state", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = {"logged_in": False, "user": None}
        result = await skill.run()
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert result.error_code == ERROR_CODE


@pytest.mark.asyncio
async def test_skill_run_exception() -> None:
    skill = GitHubAuthSkill()
    with patch("github_auth.read_login_state", new_callable=AsyncMock) as mock_read:
        mock_read.side_effect = Exception("Playwright browser connection failed")
        result = await skill.run()
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert result.output["logged_in"] is False
        assert "Playwright browser connection failed" in result.error
        assert "auth check could not run" in result.error
