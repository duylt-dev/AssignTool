"""The standard input and its JSON form (bot spec §8.3): a round trip, the defaults of optional fields, and every
message of a JSON form that does not fit."""

from __future__ import annotations

import copy
import json
import unicodedata
from datetime import date, datetime

import pytest

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import FORMAT, Inputs, Task
from scrumbot.core.model import Dev, Level, OrderDraft, OrderKind, RuleKind, TeamRule
from tests.api_builders import LINH, POOL, api_inputs, history, item, orders, sprint, sprints

S10 = sprint("S10", "Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17))


def _inputs() -> Inputs:
    return api_inputs(
        sprints(S10),
        {"S10": orders(item("a", people=(LINH,), due=date(2026, 10, 16), hours=8), item("s", parent="a", bug=True))},
        history(("a", None, "in progress", datetime(2026, 10, 7, 9))),
        devs=(*POOL[:3], Dev("Người Nghỉ", "NghiNN", Level.SENIOR, False, (date(2026, 10, 8),))),
        order=OrderDraft(
            title="Demo 1.0.2",
            app="Demo",
            priority_raw="high",
            due=date(2026, 10, 16),
            origin="web",
            kind=OrderKind.FEATURE,
            owner="TaiDT – BA",
            evidence="Ảnh dashboard",
        ),
        rules=(TeamRule(kind=RuleKind.PIN, dev="LinhNV", line=3, app="Demo", note="giữ app"),),
    )


def _plain() -> dict[str, object]:
    return json.loads(json.dumps(_inputs().to_dict(), ensure_ascii=False))


def test_the_json_form_round_trips_with_the_format_first_and_texts_as_written() -> None:
    plain = _plain()

    assert Inputs.from_dict(plain) == _inputs()
    assert list(plain) == [
        "format",
        "source",
        "fetched_at",
        "sprints",
        "lists",
        "history_lists",
        "status_changes",
        "devs",
        "rules",
        "rules_source",
        "order",
    ]
    assert plain["format"] == FORMAT == "scrumbot-input/2"
    assert (plain["order"]["kind"], plain["order"]["owner"], plain["order"]["evidence"]) == (
        "feature",
        "TaiDT – BA",
        "Ảnh dashboard",
    )
    assert plain["fetched_at"] == "2026-10-13T09:00:00"
    assert [dev["level"] for dev in plain["devs"]] == ["middle+", "middle", "junior+", "senior"]
    assert plain["rules"][0]["kind"] == "Chỉ định"
    assert plain["status_changes"] == [{"task_id": "a", "new": "in progress", "at": "2026-10-07T09:00:00"}]


def test_optional_fields_may_be_absent_or_null_and_text_is_nfc() -> None:
    plain = _plain()
    task = plain["lists"]["S10"][0]
    for key in ("parent_id", "is_bug", "status", "status_kind", "assignees", "due", "hours", "updated", "closed"):
        task.pop(key)
    task["app"] = None
    task["title"] = unicodedata.normalize("NFD", "Thêm ads")
    for key in ("history_lists", "status_changes", "rules", "rules_source"):
        plain.pop(key)
    plain["order"] = {"title": "Đơn"}

    inputs = Inputs.from_dict(plain)

    assert inputs.lists["S10"][0] == Task(id="a", title="Thêm ads", created=datetime(2026, 10, 1, 9))
    assert (inputs.history_lists, inputs.status_changes, inputs.rules, inputs.rules_source) == ((), (), (), "")
    assert inputs.order == OrderDraft(title="Đơn")


def _broken(path: str, value: object) -> dict[str, object]:
    plain = copy.deepcopy(_plain())
    *parents, last = path.split(".")
    target = plain
    for part in parents:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if value is KeyError:
        del target[last]
    else:
        target[int(last) if isinstance(target, list) else last] = value
    return plain


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([], "Dữ liệu đầu vào không đúng dạng: không phải bảng."),
        (_broken("format", KeyError), "Dữ liệu đầu vào không đúng dạng: format: thiếu."),
        (
            _broken("format", "scrumbot-input/1"),
            "Dữ liệu đầu vào không đúng dạng: format 'scrumbot-input/1', cần scrumbot-input/2.",
        ),
        (_broken("devs", KeyError), "Dữ liệu đầu vào không đúng dạng: devs: thiếu."),
        (_broken("devs", {"a": 1}), "Dữ liệu đầu vào không đúng dạng: devs: không phải danh sách."),
        (_broken("devs.1.level", "lead"), "Dữ liệu đầu vào không đúng dạng: devs[1].level: 'lead' không hợp lệ."),
        (_broken("devs.0.active", "Y"), "Dữ liệu đầu vào không đúng dạng: devs[0].active: không phải đúng/sai."),
        (_broken("sprints.0.total", "1"), "Dữ liệu đầu vào không đúng dạng: sprints[0].total: không phải số nguyên."),
        (_broken("lists", []), "Dữ liệu đầu vào không đúng dạng: lists: không phải bảng."),
        (
            _broken("order.due", "16/10/2026"),
            "Dữ liệu đầu vào không đúng dạng: order.due: không phải ngày YYYY-MM-DD.",
        ),
        (
            _broken("fetched_at", 20261013),
            "Dữ liệu đầu vào không đúng dạng: fetched_at: không phải thời điểm YYYY-MM-DDTHH:MM:SS.",
        ),
        (_broken("rules.0.kind", "Cấm"), "Dữ liệu đầu vào không đúng dạng: rules[0].kind: 'Cấm' không hợp lệ."),
        (_broken("order.title", None), "Dữ liệu đầu vào không đúng dạng: order.title: thiếu."),
        (_broken("order.kind", "rnd"), "Dữ liệu đầu vào không đúng dạng: order.kind: 'rnd' không hợp lệ."),
    ],
)
def test_a_json_form_that_does_not_fit_names_the_first_field(data: object, message: str) -> None:
    with pytest.raises(InputError) as caught:
        Inputs.from_dict(data)
    assert str(caught.value) == message


def test_a_task_in_a_list_is_named_by_list_and_index() -> None:
    plain = _plain()
    plain["lists"]["S10"][1]["created"] = "hôm qua"

    with pytest.raises(InputError, match=r"lists\[S10\]\[1\]\.created: không phải thời điểm"):
        Inputs.from_dict(plain)
