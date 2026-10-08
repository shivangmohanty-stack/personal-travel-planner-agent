"""Check scoring and incomplete-run handling without any Gemini calls."""
import pytest
from pydantic import ValidationError
from evaluator import Judgment, summarize


def record(case_id, scores, passed=True):
    return {"id": case_id, "scores": scores, "passed": passed}


def test_overall_uses_all_four_metrics_and_keeps_failures():
    rows = [record("TC01", dict(correctness=0.9, relevance=1.0, completeness=0.8, tool_usage=1.0)),
            record("TC02", dict(correctness=0.2, relevance=0.6, completeness=0.4, tool_usage=1.0), False)]
    result = summarize(rows, 2)
    assert result["complete"]
    assert result["overall_percentage"] == 73.75
    assert result["metric_averages"]["correctness"] == 0.55
    assert result["failed_test_cases"] == ["TC02"]


def test_pending_judge_does_not_inflate_final_score():
    rows = [record("TC01", dict.fromkeys(("correctness", "relevance", "completeness", "tool_usage"), 1.0)),
            record("TC02", None)]
    result = summarize(rows, 2)
    assert result["overall_percentage"] is None
    assert result["provisional_percentage"] == 100
    assert result["pending_test_cases"] == ["TC02"]
    assert not summarize(rows[:1], 2)["complete"]


@pytest.mark.parametrize("bad_score", [-0.1, 1.1, float("nan")])
def test_judge_scores_must_be_finite_and_between_zero_and_one(bad_score):
    with pytest.raises(ValidationError):
        Judgment(correctness=bad_score, relevance=1, completeness=1, tool_usage=1,
                 reason="Check", missed_expectations=[], concerns=[])


def test_empty_run_has_no_fabricated_score():
    result = summarize([], 12)
    assert result["overall_score"] is None and result["metric_averages"] is None
