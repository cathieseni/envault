"""Tests for envault.drift — drift detection against baseline."""

import pytest

from envault.project import register_project
from envault.secrets import set_secret, delete_secret
from envault.baseline import capture_baseline
from envault.drift import detect_drift, DriftResult


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "KEY_A", "alpha")
    set_secret("myapp", "KEY_B", "beta")
    return "myapp"


def test_detect_drift_no_baseline_raises(project):
    with pytest.raises(FileNotFoundError, match="No baseline"):
        detect_drift(project)


def test_detect_drift_missing_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        detect_drift("nonexistent")


def test_detect_drift_no_changes(project):
    capture_baseline(project)
    result = detect_drift(project)
    assert isinstance(result, DriftResult)
    assert not result.has_drift
    assert result.unchanged == ["KEY_A", "KEY_B"]
    assert result.added == []
    assert result.removed == []
    assert result.changed == []


def test_detect_drift_added_key(project):
    capture_baseline(project)
    set_secret(project, "KEY_C", "gamma")
    result = detect_drift(project)
    assert result.has_drift
    assert "KEY_C" in result.added
    assert result.removed == []
    assert result.changed == []


def test_detect_drift_removed_key(project):
    capture_baseline(project)
    delete_secret(project, "KEY_B")
    result = detect_drift(project)
    assert result.has_drift
    assert "KEY_B" in result.removed
    assert result.added == []
    assert result.changed == []


def test_detect_drift_changed_key(project):
    capture_baseline(project)
    set_secret(project, "KEY_A", "CHANGED_VALUE")
    result = detect_drift(project)
    assert result.has_drift
    assert "KEY_A" in result.changed
    assert result.added == []
    assert result.removed == []


def test_detect_drift_combined(project):
    capture_baseline(project)
    set_secret(project, "KEY_A", "new_alpha")  # changed
    delete_secret(project, "KEY_B")             # removed
    set_secret(project, "KEY_D", "delta")       # added
    result = detect_drift(project)
    assert result.has_drift
    assert "KEY_A" in result.changed
    assert "KEY_B" in result.removed
    assert "KEY_D" in result.added


def test_summary_no_drift(project):
    capture_baseline(project)
    result = detect_drift(project)
    summary = result.summary()
    assert "No drift detected" in summary


def test_summary_with_drift(project):
    capture_baseline(project)
    set_secret(project, "KEY_A", "changed")
    result = detect_drift(project)
    summary = result.summary()
    assert "KEY_A" in summary
    assert "changed" in summary
