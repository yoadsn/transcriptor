"""Slice 3 — Pure counting & eligibility logic (no DB)."""
import pytest

from app.services.rules import (
    is_line_eligible_for_user,
    mint_line_external_id,
    order_session_lines,
    should_increment_count,
    SessionLine,
)


# ── should_increment_count ────────────────────────────────────────────────────

def test_increment_on_first_response():
    assert should_increment_count(True) is True


def test_no_increment_on_edit():
    assert should_increment_count(False) is False


# ── is_line_eligible_for_user ─────────────────────────────────────────────────

@pytest.mark.parametrize("count,responded,target,expected", [
    (0, False, 3, True),
    (1, False, 3, True),
    (2, False, 3, True),
    (3, False, 3, False),   # at target → not eligible
    (4, False, 3, False),   # over target → not eligible
    (0, True,  3, False),   # already responded → not eligible
    (2, True,  3, False),   # responded even with room → not eligible
    (0, False, 1, True),    # custom target
    (1, False, 1, False),   # at custom target
])
def test_eligibility(count, responded, target, expected):
    assert is_line_eligible_for_user(count, responded, target) == expected


# ── mint_line_external_id ─────────────────────────────────────────────────────

def test_mint_stable():
    a = mint_line_external_id("batch-1", "page-1", 0)
    b = mint_line_external_id("batch-1", "page-1", 0)
    assert a == b


def test_mint_different_index():
    a = mint_line_external_id("batch-1", "page-1", 0)
    b = mint_line_external_id("batch-1", "page-1", 1)
    assert a != b


def test_mint_different_page():
    a = mint_line_external_id("batch-1", "page-1", 0)
    b = mint_line_external_id("batch-1", "page-2", 0)
    assert a != b


def test_mint_different_batch():
    a = mint_line_external_id("batch-1", "page-1", 0)
    b = mint_line_external_id("batch-2", "page-1", 0)
    assert a != b


# ── order_session_lines ───────────────────────────────────────────────────────

def _make_line(line_index, count, user_transcription=None):
    return SessionLine(
        id=line_index,
        line_index=line_index,
        bbox={"x": 0, "y": 0, "w": 1, "h": 1},
        polygon=None,
        transcription_count=count,
        user_transcription=user_transcription,
    )


def test_order_by_line_index():
    lines = [_make_line(2, 0), _make_line(0, 0), _make_line(1, 0)]
    result = order_session_lines(lines)
    assert [r["line_index"] for r in result] == [0, 1, 2]


def test_eligible_status():
    result = order_session_lines([_make_line(0, 0)])
    assert result[0]["status"] == "eligible"


def test_full_status():
    result = order_session_lines([_make_line(0, 3)])
    assert result[0]["status"] == "full"


def test_done_by_you_status():
    t = {"kind": "text", "text": "שלום"}
    result = order_session_lines([_make_line(0, 1, user_transcription=t)])
    assert result[0]["status"] == "done_by_you"
    assert result[0]["prior_text"] == "שלום"
    assert result[0]["prior_kind"] == "text"


def test_mixed_statuses():
    lines = [
        _make_line(0, 0),                                  # eligible
        _make_line(1, 3),                                  # full
        _make_line(2, 1, {"kind": "cant_read", "text": None}),  # done_by_you
    ]
    result = order_session_lines(lines)
    statuses = {r["line_index"]: r["status"] for r in result}
    assert statuses == {0: "eligible", 1: "full", 2: "done_by_you"}
