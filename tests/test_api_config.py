"""API configuration (bot spec §2.1, A54, A64): environment over `.env`, lenient lines, production refused."""

from __future__ import annotations

from pathlib import Path

import pytest

from scrumbot.core.errors import InputError
from scrumbot.input.dev_api.config import load_config


def _env_file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(text, encoding="utf-8")
    return path


def test_spaces_around_equals_quotes_and_comments_are_accepted(tmp_path: Path) -> None:
    path = _env_file(
        tmp_path, "# token\nSCRUMBOT_API_TOKEN = 'abc def'\nSCRUMBOT_API_BASE=\"https://devclickup.datlt.site/\"\n"
    )

    config = load_config({}, path)

    assert (config.base, config.token, config.host) == (
        "https://devclickup.datlt.site",
        "abc def",
        "devclickup.datlt.site",
    )
    assert "abc def" not in repr(config)


def test_the_environment_wins_over_the_file(tmp_path: Path) -> None:
    path = _env_file(tmp_path, "SCRUMBOT_API_TOKEN=file\nSCRUMBOT_API_BASE=https://devclickup.datlt.site\n")

    config = load_config({"SCRUMBOT_API_TOKEN": "shell"}, path)

    assert (config.token, config.base) == ("shell", "https://devclickup.datlt.site")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            "SCRUMBOT_API_BASE=https://devclickup.datlt.site\n",
            "Thiếu SCRUMBOT_API_TOKEN (trong .env hoặc biến môi trường).",
        ),
        ("SCRUMBOT_API_TOKEN=x\n", "Thiếu SCRUMBOT_API_BASE (trong .env hoặc biến môi trường), ví dụ"),
        (
            "SCRUMBOT_API_TOKEN=x\nSCRUMBOT_API_BASE=https://circle.datlt.site\n",
            "SCRUMBOT_API_BASE trỏ tới production (circle.datlt.site); bot chỉ đọc server dev (confirm.md D49).",
        ),
        ("SCRUMBOT_API_TOKEN=x\nSCRUMBOT_API_BASE=https://www.circle.datlt.site\n", "trỏ tới production"),
    ],
)
def test_missing_values_and_the_production_server_are_input_errors(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(InputError, match=message.replace("(", r"\(").replace(")", r"\)").replace(".", r"\.")):
        load_config({}, _env_file(tmp_path, text))


def test_no_env_file_and_no_environment_is_a_missing_token(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="Thiếu SCRUMBOT_API_TOKEN"):
        load_config({}, tmp_path / "absent.env")
