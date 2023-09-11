import pytest
from semver import Version

from definition_tooling.validator.utils import parse_version_without_patch


@pytest.mark.parametrize(
    "version_string,expected",
    [
        ["0.0", "0.0.0"],
        ["0.1", "0.1.0"],
        ["0.1-beta", "0.1.0-beta"],
        ["0.1-beta.2", "0.1.0-beta.2"],
        ["0.1-beta.2+build", "0.1.0-beta.2+build"],
    ],
)
def test_parse_version_without_patch(version_string: str, expected: str):
    assert parse_version_without_patch(version_string) == Version.parse(expected)


@pytest.mark.parametrize(
    "version_string",
    [
        "",
        "0",
        "1",
        "a.b",
        "1.1.1",
    ],
)
def test_invalid_parse_version_without_patch(version_string):
    with pytest.raises(ValueError):
        parse_version_without_patch(version_string)
