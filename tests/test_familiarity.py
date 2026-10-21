from datetime import date

from scrumbot.core.assign.familiarity import FamiliarityIndex
from scrumbot.core.model import Dev, HistoryOrder, Level


def dev(name: str, code: str) -> Dev:
    return Dev(name, code, Level.MIDDLE, True, ())


def history(app: str, title: str, people: tuple[str, ...], created: date) -> HistoryOrder:
    return HistoryOrder("Sprint 9", app, title, people, None, created)


def test_familiarity_keeps_only_pool_history_and_uses_last_original_row_on_same_date() -> None:
    linh = dev("Ngọc Văn Linh", "LinhNV")
    minh = dev("Nguyễn Nhật Minh", "MinhNM")
    index = FamiliarityIndex.build(
        (
            history("PS Remote", "old", (linh.name,), date(2026, 9, 1)),
            history("PS Remote", "research", ("RnD",), date(2026, 10, 2)),
            history("PS Remote", "latest", (minh.name,), date(2026, 10, 1)),
            history("psremote", "same day later", (linh.name,), date(2026, 10, 1)),
        ),
        (linh, minh),
    )

    linhs = index.get(linh, "PS Remote")
    minhs = index.get(minh, "PS Remote")
    assert (linhs.rank, linhs.versions, linhs.latest.title if linhs.latest else None) == (0, 2, "same day later")
    assert (minhs.rank, minhs.versions) == (1, 1)
    assert index.is_new_app("Unknown")
    assert index.get(minh, "").rank == 2
