"""The core API (bot spec §8.2, §8.4, §8.5) with an input built in Python, as an integrating website would: no HTTP, no
file. Place, review and assign, the passed review that assign needs, the outcome and its JSON form, the asker and the
sizer, and the checks of every input."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime

import pytest

from scrumbot import core
from scrumbot.core import (
    AiReview,
    Dev,
    Inputs,
    Level,
    OrderDraft,
    OrderKind,
    RuleKind,
    SprintInfo,
    Status,
    Task,
    TeamRule,
)
from scrumbot.core.assign.sizing import Sizing, size_orders
from scrumbot.core.errors import InputError
from scrumbot.core.model import HistoryOrder, Order, Placement, Priority, Size, SizeEstimate, SprintRow
from tests.api_builders import LINH, MINH, POOL

NOW = datetime(2026, 10, 14, 10, 30)
DESCRIPTION = "Thêm quảng cáo xen kẽ ở màn hình chính và màn kết quả. Nghiệm thu khi: hiện sau màn kết quả."
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
FILED = OrderDraft(
    title="Demo 1.0.2",
    app="Demo",
    priority_raw="high",
    due=date(2026, 10, 16),
    description=DESCRIPTION,
    owner="TaiDT – BA",
    evidence="Ảnh dashboard doanh thu",
)


def _inputs(order: OrderDraft = FILED, **changes: object) -> Inputs:
    inputs = Inputs(source="test", fetched_at=NOW, sprints=(S9, S10), lists=LISTS, devs=POOL, order=order)
    return replace(inputs, **changes)


def _no_ai(*_: object) -> Sizing:
    raise AssertionError("the AI must not be called")


def _assigned(inputs: Inputs | None = None, sizer: core.Sizer | None = None) -> core.Outcome:
    """Review, then assign with the fingerprint of that review, as the CLI does across its two runs."""
    reviewed = core.review(core.place(inputs or _inputs(), now=NOW))
    passed = {reviewed.order.fingerprint} if reviewed.status is Status.READY else set()
    return core.assign(core.place(inputs or _inputs(), now=NOW), reviewed=passed, sizer=sizer)


def test_without_ai_the_new_order_gets_a_pic_and_every_order_is_m() -> None:
    outcome = _assigned()

    assert outcome.status is Status.PROPOSED and outcome.ai is None
    assert (outcome.order.title, outcome.order.stt, outcome.order.placement) == ("Demo 1.0.2", 3, Placement.NEW)
    assert outcome.assignment is not None and outcome.assignment.pic_codes == ("LinhNV",)
    assert outcome.assignment.size == SizeEstimate(Size.M, "", True)
    assert outcome.sizing_note == "tắt AI (mọi đơn M)"
    assert (outcome.run_at, outcome.sprint.previous) == (NOW, "Sprint 9 (9/21 - 10/2)")
    assert [dev.code for dev in outcome.devs] == ["LinhNV", "MinhNM", "AnTD", "TiếnBV"]


def test_the_outcome_as_json_follows_bot_spec_8_4() -> None:
    plain = json.loads(json.dumps(_assigned().to_dict(), ensure_ascii=False))

    assert list(plain) == [
        "format",
        "status",
        "run_at",
        "source",
        "freshness",
        "sprint",
        "order",
        "review",
        "ai",
        "assignment",
        "size",
        "risks",
        "sprint_risks",
        "devs",
        "findings",
    ]
    assert (plain["format"], plain["status"], plain["run_at"], plain["ai"]) == (
        "scrumbot-outcome/3",
        "proposed",
        "2026-10-14T10:30:00",
        None,
    )
    assert plain["order"]["placement"] == "new" and plain["order"]["due"] == "2026-10-16"
    assert (plain["order"]["kind"], plain["order"]["owner"], plain["order"]["evidence"]) == (
        None,
        "TaiDT – BA",
        "Ảnh dashboard doanh thu",
    )
    assert len(plain["order"]["fingerprint"]) == 16 and int(plain["order"]["fingerprint"], 16) >= 0
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
        "remembered": False,
        "note": "tắt AI (mọi đơn M)",
    }
    assert plain["devs"][0]["level"] == "middle+"
    for risk in plain["risks"]:
        assert risk["level"] in ("high", "medium", "low") and risk["if_it_happens"]
    assert set(plain["sprint_risks"]) == {"high", "medium", "low"}


def test_a_ready_order_gets_the_check_and_the_questions_of_the_asker_and_nothing_of_assign() -> None:
    seen: list[tuple[SprintRow, OrderKind | None]] = []

    def asker(row: SprintRow, kind: OrderKind | None) -> AiReview:
        seen.append((row, kind))
        return AiReview("ads", True, (), ("Màn kết quả là màn nào?",), True, "AI (thử)")

    outcome = core.review(core.place(_inputs(), now=NOW), asker)
    plain = outcome.to_dict()

    assert outcome.status is Status.READY and outcome.review == ()
    assert [(row.stt, row.title, row.description, kind) for row, kind in seen] == [(3, "Demo 1.0.2", DESCRIPTION, None)]
    assert plain["ai"] == {
        "kind": "ads",
        "checked": True,
        "missing": [],
        "questions": ["Màn kết quả là màn nào?"],
        "answered": True,
        "note": "AI (thử)",
    }
    assert (plain["assignment"], plain["size"], plain["risks"], plain["devs"], plain["findings"]) == (
        None,
        None,
        [],
        [],
        [],
    )


def test_a_review_without_ai_is_ready_with_no_check_and_no_question() -> None:
    outcome = core.review(core.place(_inputs(), now=NOW))

    assert (outcome.status, outcome.ai) == (Status.READY, AiReview(note="tắt AI"))


def test_the_points_the_asker_names_block_the_order_in_the_template_s_words() -> None:
    """D65: the AI's template check blocks; the message is the template's, the questions stay."""

    def asker(row: SprintRow, kind: OrderKind | None) -> AiReview:
        return AiReview("ads", True, (4, 99), ("Preload ở đâu?",), True, "AI (thử)")

    placed = core.place(_inputs(), now=NOW)
    outcome = core.review(placed, asker)

    assert outcome.status is Status.NOT_READY
    assert [(item.code, item.message) for item in outcome.review] == [
        (
            "REVIEW-TEMPLATE",
            "Mô tả chưa đủ ý của mẫu Quảng cáo (AI chấm): Luồng hiển thị (link Flow), tần suất, preload.",
        )
    ]
    assert outcome.ai is not None and outcome.ai.questions == ("Preload ở đâu?",)
    with pytest.raises(InputError, match="chưa qua review"):
        core.assign(placed, reviewed=set())


def test_the_file_s_type_reaches_the_asker_and_wins_over_the_ai_s() -> None:
    seen: list[OrderKind | None] = []

    def asker(row: SprintRow, kind: OrderKind | None) -> AiReview:
        seen.append(kind)
        return AiReview("other", True, (), (), True, "AI (thử)")

    outcome = core.review(core.place(_inputs(replace(FILED, kind=OrderKind.ADS)), now=NOW), asker)

    assert seen == [OrderKind.ADS]
    assert outcome.status is Status.READY and outcome.order.kind is OrderKind.ADS
    assert outcome.ai == AiReview("ads", True, (), (), True, "AI (thử)")


def test_an_order_outside_the_8_types_is_ready_without_a_check() -> None:
    def asker(row: SprintRow, kind: OrderKind | None) -> AiReview:
        return AiReview("other", True, (1,), (), True, "AI (thử)")

    outcome = core.review(core.place(_inputs(), now=NOW), asker)

    assert (outcome.status, outcome.ai) == (Status.READY, AiReview("other", False, (1,), (), True, "AI (thử)"))


def test_a_blocked_order_never_reaches_the_ai_and_has_no_pic_nor_register() -> None:
    blocked = OrderDraft(title="Demo 1.0.2", priority_raw="urgent", description="ngắn")

    outcome = core.review(core.place(_inputs(blocked), now=NOW), _no_ai)
    plain = outcome.to_dict()

    assert outcome.status is Status.NOT_READY
    assert [item.code for item in outcome.review] == [
        "REVIEW-APP",
        "REVIEW-DUE",
        "REVIEW-OWNER",
        "REVIEW-EVIDENCE",
        "REVIEW-DESC",
        "REVIEW-ACCEPT",
    ]
    assert (plain["ai"], plain["assignment"], plain["size"], plain["risks"], plain["devs"]) == (
        None,
        None,
        None,
        [],
        [],
    )
    assert plain["sprint_risks"] == {"high": 0, "medium": 0, "low": 0}


def test_an_order_already_held_is_not_reviewed_and_is_kept_without_a_passed_review() -> None:
    held = _inputs(OrderDraft(title="x", order_id="held"))

    reviewed = core.review(core.place(held, now=NOW), _no_ai)
    outcome = core.assign(core.place(held, now=NOW), reviewed=())

    assert (reviewed.status, reviewed.review, reviewed.ai) == (Status.PRE_ASSIGNED, (), None)
    assert outcome.status is Status.PRE_ASSIGNED and outcome.review == ()
    assert outcome.order.placement is Placement.BY_ID and outcome.order.title == "Other 2.0"
    assert outcome.assignment is not None
    assert (outcome.assignment.pic_codes, outcome.assignment.backups) == (("MinhNM",), ())


@pytest.mark.parametrize(
    "order",
    [
        FILED,  # never reviewed
        OrderDraft(title="Demo 1.0.2", priority_raw="urgent", description="ngắn"),  # reviewed, not ready
    ],
)
def test_assign_refuses_an_order_without_a_passed_review(order: OrderDraft) -> None:
    placed = core.place(_inputs(replace(order, origin="input/don/a.md")), now=NOW)
    core.review(placed)

    with pytest.raises(InputError) as caught:
        core.assign(placed, reviewed=set(), sizer=_no_ai)

    assert str(caught.value) == (
        "Đơn chưa qua review, hoặc đã đổi sau lần review đạt gần nhất: review lại 'input/don/a.md' trước khi giao."
    )


@pytest.mark.parametrize(
    "change",
    [
        {"description": DESCRIPTION + " Thêm màn cài đặt."},
        {"app": "Other"},
        {"priority_raw": "normal"},
        {"due": date(2026, 10, 17)},
        {"title": "Demo 1.0.3"},
        {"kind": OrderKind.ADS},
        {"owner": "ThuDH – MO"},
        {"evidence": "Email Google Play"},
    ],
)
def test_an_order_changed_after_its_review_needs_another(change: dict[str, object]) -> None:
    passed = {core.review(core.place(_inputs(), now=NOW)).order.fingerprint}
    changed = core.place(_inputs(replace(FILED, **change)), now=NOW)

    with pytest.raises(InputError, match="chưa qua review"):
        core.assign(changed, reviewed=passed)


def test_the_fingerprint_is_the_order_not_the_run() -> None:
    first = core.place(_inputs(), now=NOW)
    later = core.place(_inputs(replace(FILED, origin="khác.md")), now=datetime(2026, 10, 15, 8), sprint_id="S10")

    assert first.fingerprint == later.fingerprint
    assert core.assign(later, reviewed={first.fingerprint}).status is Status.PROPOSED


def test_the_sizer_gets_the_orders_the_history_and_the_filed_order_as_fresh() -> None:
    seen: list[tuple[tuple[int, ...], int, frozenset[int]]] = []

    def sizer(orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]) -> Sizing:
        seen.append((tuple(order.row.stt for order in orders), len(examples), fresh))
        return Sizing({3: SizeEstimate(Size.L, "lớn", False)}, (), "AI (thử, 1/3 đơn)")

    outcome = _assigned(sizer=sizer)

    assert seen == [((1, 2, 3), 1, frozenset({3}))]  # the history window holds the order of Sprint 9
    assert outcome.assignment is not None and outcome.assignment.size == SizeEstimate(Size.L, "lớn", False)
    assert outcome.sizing_note == "AI (thử, 1/3 đơn)"


def test_an_order_the_sizer_leaves_out_is_m() -> None:
    def sizer(orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]) -> Sizing:
        return Sizing({2: SizeEstimate(Size.S, "", False), 99: SizeEstimate(Size.XL, "", False)}, (), "AI")

    placed = core.place(_inputs(), now=NOW)
    orders = tuple(Order(row, Priority.NORMAL) for row in placed.order.view.rows if row.kind == "Task")

    sizes = size_orders(orders, (), frozenset(), sizer).sizes

    assert sizes == {
        1: SizeEstimate(Size.M, "", True),
        2: SizeEstimate(Size.S, "", False),
        3: SizeEstimate(Size.M, "", True),
    }


def test_the_run_day_is_the_day_of_now_unless_given_and_keeps_the_time_of_now() -> None:
    assert (core.place(_inputs(), now=NOW).today, core.place(_inputs(), now=NOW).run_at) == (NOW.date(), NOW)
    given = core.place(_inputs(), now=NOW, today=date(2026, 10, 8))
    assert (given.today, given.run_at) == (date(2026, 10, 8), datetime(2026, 10, 8, 10, 30))


def test_the_json_input_decides_as_the_python_one() -> None:
    inputs = _inputs()

    from_json = _assigned(Inputs.from_dict(json.loads(json.dumps(inputs.to_dict()))))

    assert from_json.to_dict() == _assigned(inputs).to_dict()


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
        core.place(_inputs(**changes), now=NOW)
    assert str(caught.value) == message
