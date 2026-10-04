"""`make eval`: runs the golden Q&A set against the Ask pipeline and writes a
report. The deterministic parts (refusal correctness,
citation validity) run the same way in CI with FakeProvider; a live-model
evaluation is manual and its score is only shown once the owner confirms the
numbers -- this command never claims a score for a provider it didn't use.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from django.core.management.base import BaseCommand, CommandError

from apps.ai.services import ask

DEFAULT_GOLDEN_PATH = Path("tests/ai/golden.yaml")
DEFAULT_REPORT_DIR = Path("docs/eval")


class Command(BaseCommand):
    help = "Run the golden Q&A set against the Ask pipeline and write a report."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--golden", default=str(DEFAULT_GOLDEN_PATH))
        parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))

    def handle(self, *args: Any, **options: Any) -> None:
        golden_path = Path(options["golden"])
        if not golden_path.exists():
            raise CommandError(f"Golden set not found: {golden_path}")

        cases = yaml.safe_load(golden_path.read_text(encoding="utf-8")) or []
        results = [self._run_case(case) for case in cases]

        report = self._build_report(results)
        report_dir = Path(options["report_dir"])
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(
                f"Ran {report['total']} case(s): "
                f"{report['refusal_correct']}/{report['refusal_total']} refusal-correct, "
                f"{report['citation_valid']}/{report['answered_total']} citations valid. "
                f"Report: {report_path}"
            )
        )

    def _run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        result = ask(case["question"])
        expect_refusal = case.get("expect_refusal", False)
        expected_title = case.get("expected_title_contains")

        citation_valid = True
        if not result.refused and expected_title:
            citation_valid = any(
                expected_title.lower() in c["title"].lower() for c in result.citations
            )
        if not result.refused and not result.citations:
            citation_valid = False

        return {
            "question": case["question"],
            "expect_refusal": expect_refusal,
            "actual_refused": result.refused,
            "refusal_correct": expect_refusal == result.refused,
            "citation_valid": citation_valid,
            "answer": result.answer,
        }

    def _build_report(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        answered = [r for r in results if not r["actual_refused"]]
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "provider": "fake",
            "total": len(results),
            "refusal_total": len(results),
            "refusal_correct": sum(r["refusal_correct"] for r in results),
            "answered_total": len(answered),
            "citation_valid": sum(r["citation_valid"] for r in answered),
            "cases": results,
        }
