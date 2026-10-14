"""The order file in the sprint (bot spec §7.2–§7.3): what the AI may read, where the order sits, what the report
shows. Pure, no mocks."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from scrumbot.core.errors import InputError
from scrumbot.core.model import (
    Assignment,
    Dev,
    Finding,
    Level,
    Order,
    OrderDraft,
    Placement,
    Priority,
    Result,
    Severity,
    Size,
    SizeEstimate,
    Source,
    SprintRow,
    SprintView,
)
from scrumbot.core.model_risk import IF_IT_HAPPENS, Risk, RiskGroup, RiskLevel
from scrumbot.core.rules.new_order import PERSON, looks_like_code, order_report, place, scrub
from scrumbot.core.rules.pipeline import team_for
from scrumbot.core.rules.summary import summarize

LINH = Dev("Ngọc Văn Linh", "LinhNV", Level.MIDDLE_PLUS, True, ())
MINH = Dev("Nguyễn Nhật Minh", "MinhNM", Level.MIDDLE, True, ())
NOW = datetime(2026, 10, 13, 9, 0)


def _row(stt: int, title: str, kind: str = "Task", order_id: str = "", root: str = "") -> SprintRow:
    return SprintRow(
        stt,
        title,
        kind,
        "Demo",
        (),
        "",
        "",
        None,
        date(2026, 10, 6),
        "",
        id=order_id,
        root_id=root,
    )


def _view() -> SprintView:
    rows = (_row(1, "1.0.1 - Add ads", order_id="a"), _row(2, "1.0.2 - Fix UI", order_id="b"))
    rows += (_row(3, "Sub", "Subtask", "s", "a"),)
    bugs = (_row(4, "Bug", "Bug", "x", "a"),)
    return SprintView("Sprint 10 (10/6 - 10/17)", 10, date(2026, 10, 6), date(2026, 10, 17), rows, "S10", bugs)


def _draft(title: str = "Demo 2.0.0 - Add IAP", order_id: str = "", description: str = "") -> OrderDraft:
    return OrderDraft(
        title=title, order_id=order_id, app="Demo", priority_raw="high", due=date(2026, 10, 16), description=description
    )


def test_scrub_turns_links_into_their_kind_and_names_into_a_mark() -> None:
    text = (
        "Liên hệ BA: TestBA, hỏi Ngọc Văn Linh\n"
        "* SRS: [https://docs.google.com/document/d/1/edit](https://docs.google.com/document/d/1/edit)\n"
        "* [UI](https://www.figma.com/design/abc/Game) và https://example.test/x"
    )

    assert scrub(text, frozenset({LINH.name, LINH.code})) == (
        f"Liên hệ BA: {PERSON}, hỏi {PERSON} * SRS: [link Google Docs] * UI [link Figma] và [link]"
    )


@pytest.mark.parametrize(("word", "code"), [("TestBA", True), ("TiếnBV", True), ("GameUI", True), ("iOS", False)])
def test_looks_like_code(word: str, code: bool) -> None:
    assert looks_like_code(word) is code


@pytest.mark.parametrize("word", ["SRS", "Figma", "AdMob", "PlayStation", "Android", "UI"])
def test_ordinary_words_are_not_codes(word: str) -> None:
    assert not looks_like_code(word)


def test_a_new_order_comes_after_the_roots_and_moves_subtasks_and_bugs_down() -> None:
    placed = place(_view(), _draft(description="Thêm IAP, liên hệ TestBA"), frozenset(), date(2026, 10, 13))

    assert (placed.stt, placed.how) == (3, Placement.NEW)
    new = placed.view.rows[2]
    assert (new.title, new.kind, new.assignees, new.status, new.priority_raw, new.created) == (
        "Demo 2.0.0 - Add IAP",
        "Task",
        (),
        "",
        "high",
        date(2026, 10, 13),
    )
    assert new.description == f"Thêm IAP, liên hệ {PERSON}"
    assert [(row.stt, row.kind, row.id) for row in placed.view.rows] == [
        (1, "Task", "a"),
        (2, "Task", "b"),
        (3, "Task", ""),
        (4, "Subtask", "s"),
    ]
    assert placed.view.bugs[0].stt == 5


def test_an_id_or_the_same_title_finds_the_order_and_gives_it_the_description() -> None:
    by_id = place(_view(), _draft(order_id="b", description="Sửa UI"), frozenset(), date(2026, 10, 13))
    by_title = place(_view(), _draft(title="1.0.1 - ADD ads", description="x"), frozenset(), date(2026, 10, 13))

    assert (by_id.stt, by_id.how, by_id.view.rows[1].description, len(by_id.view.rows)) == (
        2,
        Placement.BY_ID,
        "Sửa UI",
        3,
    )
    assert (by_title.stt, by_title.how) == (1, Placement.BY_TITLE)


def test_an_unknown_id_or_a_title_found_twice_is_an_input_error() -> None:
    twice = SprintView("Sprint 10", 10, None, None, (_row(1, "Same", order_id="a"), _row(2, "same", order_id="b")))

    with pytest.raises(InputError, match="Không có đơn gốc ID 'zz' trong Sprint 10"):
        place(_view(), _draft(order_id="zz"), frozenset(), date(2026, 10, 13))
    with pytest.raises(InputError, match="Có 2 đơn tên 'Same' trong Sprint 10; ghi ID của đơn vào file đơn."):
        place(twice, _draft(title="Same"), frozenset(), date(2026, 10, 13))


def test_the_report_keeps_the_risks_of_the_order_its_pic_and_the_sprint_only() -> None:
    view = _view()
    placed = place(view, _draft(), frozenset(), date(2026, 10, 13))
    size = SizeEstimate(Size.M, "", False)
    rows = [row for row in placed.view.rows if row.kind == "Task"]
    items = (
        Assignment(Order(rows[0], Priority.NORMAL), size, Source.PREASSIGNED, (MINH.name,), ("MinhNM",), "", ()),
        Assignment(Order(rows[2], Priority.HIGH), size, Source.PROPOSED, (LINH.name,), ("LinhNV",), "r", ("MinhNM",)),
    )

    def risk(code: str, where: str, stt: int | None) -> Risk:
        return Risk(RiskLevel.HIGH, code, RiskGroup.CAPACITY, where, "", "", "", "TM", None, stt)

    risks = (
        risk("DUE-AT-RISK", "Đơn STT 3", 3),
        risk("DUE-AT-RISK", "Đơn STT 1", 1),
        risk("CAPACITY-DEV", "LinhNV", None),
        risk("CAPACITY-DEV", "MinhNM", None),
        risk("CAPACITY-SPRINT", view.name, None),
    )
    findings = (
        Finding(Severity.WARN, "DUE-MISSING", "Đơn STT 3", "a"),
        Finding(Severity.WARN, "DUE-MISSING", "Đơn STT 1", "b"),
        Finding(Severity.WARN, "SIZE-AI-FAILED", "agy", "c"),
    )
    team = team_for((LINH, MINH), placed.view, date(2026, 10, 13))
    devs = summarize((LINH, MINH), {}, {}, items)
    result = Result(view.name, "Sprint 9", "", items, findings, devs, risks)

    report = order_report(result, placed, team, ())

    assert [(r.code, r.where) for r in report.risks] == [
        ("DUE-AT-RISK", "Đơn STT 3"),
        ("CAPACITY-DEV", "LinhNV"),
        ("CAPACITY-SPRINT", view.name),
    ]
    assert [f.where for f in report.findings] == ["Đơn STT 3", "agy"]
    assert [(line.code, line.role, line.familiarity) for line in report.devs] == [
        ("LinhNV", "PIC", "Chưa làm"),
        ("MinhNM", "Dự phòng 1", "Chưa làm"),
    ]


def test_every_risk_code_has_a_contingency_sentence() -> None:
    codes = {
        "CAPACITY-DEV",
        "CAPACITY-SPRINT",
        "SCOPE-ADDED",
        "CARRY-OVER",
        "PIC-UNFAMILIAR",
        "PIC-ABSENT",
        "DUE-AT-RISK",
        "STATUS-STUCK",
        "QA-RETURNS",
    }
    assert set(IF_IT_HAPPENS) == codes and all(text.endswith(".") for text in IF_IT_HAPPENS.values())
