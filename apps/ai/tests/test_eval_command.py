import json

import pytest
import yaml
from django.core.management import call_command


@pytest.fixture
def golden_file(tmp_path):
    cases = [
        {"question": "What is the meaning of life?", "expect_refusal": True},
        {"question": "Off topic question", "expect_refusal": False},  # deliberately wrong
    ]
    path = tmp_path / "golden.yaml"
    path.write_text(yaml.safe_dump(cases), encoding="utf-8")
    return path


@pytest.mark.django_db
def test_eval_rag_writes_report_with_expected_shape(golden_file, tmp_path):
    report_dir = tmp_path / "report"

    call_command("eval_rag", golden=str(golden_file), report_dir=str(report_dir))

    report = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    assert report["total"] == 2
    assert report["provider"] == "fake"
    assert len(report["cases"]) == 2


@pytest.mark.django_db
def test_eval_rag_flags_incorrect_refusal_expectation(golden_file, tmp_path):
    report_dir = tmp_path / "report"

    call_command("eval_rag", golden=str(golden_file), report_dir=str(report_dir))

    report = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    # "Off topic question" expected NOT to refuse but nothing is indexed, so
    # it will refuse -- the harness should record that mismatch, not hide it.
    assert report["refusal_correct"] < report["total"]


@pytest.mark.django_db
def test_eval_rag_errors_on_missing_golden_file(tmp_path):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("eval_rag", golden=str(tmp_path / "does-not-exist.yaml"))
