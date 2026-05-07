"""Tests for envault.env_check module."""

import time
import pytest
from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.expiry import set_expiry
from envault.env_check import check_project, has_issues, CheckResult


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp", "/tmp/myapp")
    return "myapp"


def test_all_ok_no_expiry(project):
    set_secret(project, "DB_URL", "postgres://localhost")
    results = check_project(project)
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].key == "DB_URL"


def test_missing_required_key(project):
    results = check_project(project, required_keys=["MISSING_KEY"])
    assert len(results) == 1
    assert results[0].status == "missing"


def test_expired_secret(project):
    set_secret(project, "API_KEY", "abc123")
    past_ts = time.time() - 1  # already expired
    set_expiry(project, "API_KEY", past_ts)
    results = check_project(project, required_keys=["API_KEY"])
    assert results[0].status == "expired"


def test_expiring_soon_secret(project):
    set_secret(project, "TOKEN", "xyz")
    soon_ts = time.time() + 3 * 86400  # 3 days from now
    set_expiry(project, "TOKEN", soon_ts)
    results = check_project(project, required_keys=["TOKEN"], warn_days=7)
    assert results[0].status == "expiring_soon"
    assert "3." in results[0].message


def test_not_expiring_soon_when_far_away(project):
    set_secret(project, "TOKEN", "xyz")
    far_ts = time.time() + 30 * 86400  # 30 days
    set_expiry(project, "TOKEN", far_ts)
    results = check_project(project, required_keys=["TOKEN"], warn_days=7)
    assert results[0].status == "ok"


def test_has_issues_false_when_all_ok(project):
    set_secret(project, "X", "val")
    results = check_project(project)
    assert not has_issues(results)


def test_has_issues_true_when_missing(project):
    results = check_project(project, required_keys=["NOPE"])
    assert has_issues(results)


def test_unknown_project_raises():
    with pytest.raises(KeyError):
        check_project("nonexistent_project")


def test_check_result_repr():
    r = CheckResult("MY_KEY", "ok", "All good.")
    assert "MY_KEY" in repr(r)
    assert "ok" in repr(r)
