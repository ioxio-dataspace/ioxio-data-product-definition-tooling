import re
from typing import Any, Dict

from semver import Version

_MAJOR_MINOR_NO_PATCH_REGEX_TEMPLATE = r"""
        ^
        (?P<major>0|[1-9]\d*)
        (?:
            \.
            (?P<minor>0|[1-9]\d*)
        )
        (?:-(?P<prerelease>
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        ))?
        (?:\+(?P<build>
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        ))?
        $
    """
_MAJOR_MINOR_NO_PATCH_REGEX = re.compile(
    _MAJOR_MINOR_NO_PATCH_REGEX_TEMPLATE.format(opt_patch=""),
    re.VERBOSE,
)


def parse_version_without_patch(version: str) -> Version:
    """
    Parse a version string that has no PATCH to a Version.

    :param version: version string
    :return: A Version
    :raise ValueError: If version is invalid

    >>> parse_version_without_patch('1.0')
    Version(major=1, minor=0, patch=0, prerelease=None, build=None)
    >>> parse_version_without_patch('1.0-beta.2')
    Version(major=1, minor=0, patch=0, prerelease='beta.2', build=None)
    """

    match = _MAJOR_MINOR_NO_PATCH_REGEX.match(version)
    if match is None:
        raise ValueError(f"{version} is not valid version string without patch")

    matched_version_parts: Dict[str, Any] = match.groupdict()
    matched_version_parts["patch"] = 0

    return Version(**matched_version_parts)
