from __future__ import annotations

import pytest
from protocol.common import Version, parse_version


@pytest.mark.parametrize(
    ("version", "expected_version", "expected_string"),
    [
        ("", Version(0, 0, 0, "unknown"), "0.0.0-unknown"),
        ("1", Version(1, 0, 0, ""), "1.0.0"),
        ("1.2", Version(1, 2, 0, ""), "1.2.0"),
        ("1.2.3", Version(1, 2, 3, ""), "1.2.3"),
        ("1.2.3-dev", Version(1, 2, 3, "dev"), "1.2.3-dev"),
    ],
    ids=["empty", "major", "minor", "patch", "dev"],
)
def test_parse_version(
    version: str, expected_version: Version, expected_string: str
) -> None:
    parsed = parse_version(version)
    assert parsed == expected_version
    assert parsed.to_string() == expected_string


@pytest.mark.parametrize(
    "invalid_version", ["a", "a.b", "a.1", "1.a", "1.1.a", "1.1.1.a", "1.1.1.1"]
)
def test_invalid_version(invalid_version: str) -> None:
    with pytest.raises(ValueError):
        parse_version(invalid_version)


@pytest.mark.parametrize(
    ["a", "b", "expected"],
    [
        ("1.0.0", "1.0.0", False),
        ("1.0.0", "1.0.1", True),
        ("1.0.0", "1.1.0", True),
        ("1.0.0", "2.0.0", True),
        ("1.0.0-preview.1", "1.0.0-preview.2", True),
        ("1.0.1", "1.0.0", False),
        ("1.1.0", "1.0.0", False),
        ("2.0.0", "1.0.0", False),
        ("1.0.0-preview.2", "1.0.0-preview.1", False),
    ],
)
def test_version_less_than(a: str, b: str, expected: bool) -> None:
    assert (parse_version(a) < parse_version(b)) is expected


@pytest.mark.parametrize(
    ["a", "b", "expected"],
    [
        ("1.0.0", "1.0.0", False),
        ("1.0.0", "1.0.1", False),
        ("1.0.0", "1.1.0", False),
        ("1.0.0", "2.0.0", False),
        ("1.0.0-preview.1", "1.0.0-preview.2", False),
        ("1.0.1", "1.0.0", True),
        ("1.1.0", "1.0.0", True),
        ("2.0.0", "1.0.0", True),
        ("1.0.0-preview.2", "1.0.0-preview.1", True),
    ],
)
def test_version_greater_than(a: str, b: str, expected: bool) -> None:
    assert (parse_version(a) > parse_version(b)) is expected


def test_version_invalid_equal_comparison() -> None:
    with pytest.raises(TypeError) as exc:
        assert Version(1, 0, 0, "") == "1.0.0"
    assert exc.match("cannot compare version with type <class 'str'>")


def test_version_invalid_less_than_comparison() -> None:
    with pytest.raises(TypeError) as exc:
        assert Version(1, 0, 0, "") < "1.0.0"  # type: ignore
    assert exc.match("cannot compare version with type <class 'str'>")


def test_version_invalid_greater_than_comparison() -> None:
    with pytest.raises(TypeError) as exc:
        assert Version(1, 0, 0, "") > "1.0.0"  # type: ignore
    assert exc.match("cannot compare version with type <class 'str'>")


def test_version_repr() -> None:
    assert repr(Version(1, 2, 3, "dev")) == "Version(1, 2, 3, 'dev')"
    assert repr(Version(1, 2, 3, "")) == "Version(1, 2, 3, '')"
