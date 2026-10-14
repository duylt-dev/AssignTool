"""The core API (bot spec §8.2, §8.4, §8.5) with an input built in Python, as an integrating website would: no HTTP, no
file. Prepare and decide, the outcome and its JSON form, the sizer, and the checks of every input."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime

import pytest

from scrumbot import core
from scrumbot.core import Dev, Inputs, Level, OrderDraft, RuleKind, SprintInfo, Status, Task, TeamRule
from scrumbot.core.errors import InputError
from scrumbot.core.model import HistoryOrder, Order, Placement, Priority, Size, SizeEstimate
from scrumbot.core.sizing import Sizing, size_orders
from tests.api_builders import LINH, MINH, POOL

NOW = datetime(2026, 10, 14, 10, 30)
DESCRIPTION = "Thêm quảng cáo xen kẽ ở màn hình chính và màn kết quả."
S9 = SprintInfo(
    id="S9", name="Sprint 9 (9/21 - 10/2)", kind="sprint", total=1, start=date(2026, 9, 21), end=date(2026, 10, 2)
)
S10 = SprintInfo(
    id="S10", name="Sprint 10 (10/6 - 10/17)", kind="sprint", total=2, start=date(2026, 10, 6), end=date(2026, 10, 17)
)
LISTS = {
    "S9": (
        Task(
            id="old",
            title="Demo 1.0.0",
            created=datetime(2026, 9, 22, 9),
            assignees=(LINH,),
            status="done",
            status_kind="done",
            app="Demo",
        ),
    ),
    "S10": (
        Task(
            id="held",
            title="Other 2.0",
            created=datetime(2026, 10, 6, 9),
            assignees=(MINH,),
            status="in progress",
            app="Other",
        ),
        Task(id="empty", title="Demo 1.0.1", created=datetime(2026, 10, 7, 9), status="ready to progress", app="Demo"),
    ),
}
FILED = OrderDraft(title="Demo 1.0.2", app="Demo", priority_raw="high", due=date(2026, 10, 16), description=DESCRIPTION)


def _inputs(order: OrderDraft = FILED, **changes: object) -> Inputs:
    inputs = Inputs(source="test", fetched_at=NOW, sprints=(S9, S10), lists=LISTS, devs=POOL, order=order)
    return replace(inputs, **changes)


def _no_ai(*_: object) -> Sizing:
    raise AssertionError("the sizer must not be called")


def test_without_ai_the_new_order_gets_a_pic_and_every_order_is_m() -> None:
    outcome = core.evaluate(_inputs(), now=NOW)

    assert outcome.status is Status.PROPOSED
    assert (outcome.order.title, outcome.order.stt, outcome.order.placement) == ("Demo 1.0.2", 3, Placement.NEW)
    assert outcome.assignment is not None and outcome.assignment.pic_codes == ("LinhNV",)
    assert outcome.assignment.size == SizeEstimate(Size.M, "", True)
    assert outcome.sizing_note == "tắt AI (mọi đơn M)"
    assert (outcome.run_at, outcome.sprint.previous) == (NOW, "Sprint 9 (9/21 - 10/2)")
    assert [dev.code for dev in outcome.devs] == ["LinhNV", "MinhNM", "AnTD", "TiếnBV"]


def test_the_outcome_as_json_follows_bot_spec_8_4() -> None:
    plain = json.loads(json.dumps(core.evaluate(_inputs(), now=NOW).to_dict(), ensure_ascii=False))

    assert list(plain) == [
        "format",
        "status",
        "run_at",
        "source",
        "freshness",
        "sprint",
        "order",
        "review",
        "assignment",
        "size",
        "risks",
        "sprint_risks",
        "devs",
        "findings",
    ]
    assert (plain["format"], plain["status"], plain["run_at"]) == (
        "scrumbot-outcome/1",
        "proposed",
        "2026-10-14T10:30:00",
    )
    assert plain["order"]["placement"] == "new" and plain["order"]["due"] == "2026-10-16"
    assert plain["assignment"]["pic_codes"] == ["LinhNV"] and len(plain["assignment"]["backups"]) == 2
    assert plain["size"] == {
        "size": "M",
        "hours": 16,
        "is_default": True,
        "reason": "",
        "kind": "",
        "kind_label": "",
        "items": [],
        "tech_risks": [],
        "questions": [],
        "remembered": False,
        "note": "tắt AI (mọi đơn M)",
    }
    assert plain["devs"][0]["level"] == "middle+"
    for risk in plain["risks"]:
        assert risk["level"] in ("high", "medium", "low") and risk["if_it_happens"]
    assert set(plain["sprint_risks"]) == {"high", "medium", "low"}


def test_a_blocked_order_is_never_sized_and_has_no_pic_nor_register() -> None:
    blocked = OrderDraft(title="Demo 1.0.2", priority_raw="urgent", description="ngắn")

    outcome = core.evaluate(_inputs(blocked), now=NOW, sizer=_no_ai)
    plain = outcome.to_dict()

    assert outcome.status is Status.NOT_READY
    assert [item.code for item in outcome.review] == ["REVIEW-APP", "REVIEW-DUE", "REVIEW-DESC"]
    assert (plain["assignment"], plain["size"], plain["risks"], plain["devs"], plain["findings"]) == (
        None,
        None,
        [],
        [],
        [],
    )
    assert plain["sprint_risks"] == {"high": 0, "medium": 0, "low": 0}


def test_an_order_already_held_is_kept_and_not_reviewed() -> None:
    outcome = core.evaluate(_inputs(OrderDraft(title="x", order_id="held")), now=NOW)

    assert outcome.status is Status.PRE_ASSIGNED and outcome.review == ()
    assert outcome.order.placement is Placement.BY_ID and outcome.order.title == "Other 2.0"
    assert outcome.assignment is not None
    assert (outcome.assignment.pic_codes, outcome.assignment.backups) == (("MinhNM",), ())


def test_the_sizer_gets_the_orders_the_history_and_the_filed_order_as_fresh() -> None:
    seen: list[tuple[tuple[int, ...], int, frozenset[int]]] = []

    def sizer(orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]) -> Sizing:
        seen.append((tuple(order.row.stt for order in orders), len(examples), fresh))
        return Sizing({3: SizeEstimate(Size.L, "lớn", False)}, (), "AI (thử, 1/3 đơn)")

    outcome = core.evaluate(_inputs(), now=NOW, sizer=sizer)

    assert seen == [((1, 2, 3), 1, frozenset({3}))]  # the history window holds the order of Sprint 9
    assert outcome.assignment is not None and outcome.assignment.size == SizeEstimate(Size.L, "lớn", False)
    assert outcome.sizing_note == "AI (thử, 1/3 đơn)"


def test_an_order_the_sizer_leaves_out_is_m() -> None:
    def sizer(orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]) -> Sizing:
        return Sizing({2: SizeEstimate(Size.S, "", False), 99: SizeEstimate(Size.XL, "", False)}, (), "AI")

    prepared = core.prepare(_inputs(), now=NOW)
    orders = tuple(Order(row, Priority.NORMAL) for row in prepared.placed.view.rows if row.kind == "Task")

    sizes = size_orders(orders, (), frozenset(), sizer).sizes

    assert sizes == {
        1: SizeEstimate(Size.M, "", True),
        2: SizeEstimate(Size.S, "", False),
        3: SizeEstimate(Size.M, "", True),
    }


def test_the_run_day_is_the_day_of_now_unless_given_and_keeps_the_time_of_now() -> None:
    assert (core.prepare(_inputs(), now=NOW).today, core.prepare(_inputs(), now=NOW).run_at) == (NOW.date(), NOW)
    given = core.prepare(_inputs(), now=NOW, today=date(2026, 10, 8))
    assert (given.today, given.run_at) == (date(2026, 10, 8), datetime(2026, 10, 8, 10, 30))


def test_the_json_input_decides_as_the_python_one() -> None:
    inputs = _inputs()

    from_json = core.evaluate(Inputs.from_dict(json.loads(json.dumps(inputs.to_dict()))), now=NOW)

    assert from_json.to_dict() == core.evaluate(inputs, now=NOW).to_dict()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"devs": ()}, "Dữ liệu đầu vào không có dev nào."),
        ({"devs": (*POOL, Dev(LINH, "Linh2", Level.SENIOR, True))}, f"Dữ liệu đầu vào trùng tên dev '{LINH}'."),
        ({"devs": (*POOL, Dev("Khác", "linhnv", Level.SENIOR, True))}, "Dữ liệu đầu vào trùng mã dev 'linhnv'."),
        (
            {"rules": (TeamRule(kind=RuleKind.PIN, dev="Nobody", line=3, app="Demo"),), "rules_source": "web"},
            "File 'web', dòng 3: không có dev mã 'Nobody' trong file dev.",
        ),
    ],
)
def test_every_input_is_checked_whatever_adapter_built_it(changes: dict[str, object], message: str) -> None:
    with pytest.raises(InputError) as caught:
        core.prepare(_inputs(**changes), now=NOW)
    assert str(caught.value) == message
