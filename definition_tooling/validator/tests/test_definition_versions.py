import json

import pytest

from definition_tooling.validator import errors as err
from definition_tooling.validator.core import DefinitionValidator


@pytest.fixture()
def spec(company_basic_info):
    """
    Make spec an alias of company_basic_info to shorten down the tests.
    """
    yield company_basic_info


@pytest.fixture()
def validate_definition(tmp_path):
    def validate_definition_(file: str, spec: dict):
        spec_path = tmp_path / f"{file}.json"
        spec_path.parent.mkdir(parents=True)
        spec_path.write_text(json.dumps(spec))
        DefinitionValidator(spec_path=spec_path, root_path=tmp_path).validate()

    return validate_definition_


@pytest.fixture()
def check_version_error(tmp_path):
    def check_version_error_(file: str, spec: dict, exception):
        spec_path = tmp_path / f"{file}.json"
        spec_path.parent.mkdir(parents=True)
        spec_path.write_text(json.dumps(spec))
        with pytest.raises(exception):
            DefinitionValidator(spec_path=spec_path, root_path=tmp_path).validate()

    return check_version_error_


def test_missing_version(check_version_error, spec):
    del spec["info"]["version"]
    check_version_error("Company/BasicInfo_v1.0", spec, err.InvalidOrMissingVersion)


@pytest.mark.parametrize(
    "version",
    [
        "1",
        "1.0",
        "1.0.0.0",
        "-1.0.0",
        "abc",
        None,
    ],
)
def test_invalid_version(check_version_error, spec, version: str):
    spec["info"]["version"] = version
    check_version_error("Company/BasicInfo_v1.0", spec, err.InvalidOrMissingVersion)


@pytest.mark.parametrize(
    "folder",
    [
        "draft",
        "test",
    ],
)
def test_version_in_filename_when_not_expected(check_version_error, spec, folder: str):
    spec["info"]["version"] = "0.0.1"
    check_version_error(
        f"{folder}/Company/BasicInfo_v0.0", spec, err.UnexpectedVersionInFilename
    )


@pytest.mark.parametrize(
    "folder,version",
    [
        ["draft", "1.0.0"],
        ["draft", "0.1.0"],
        ["test", "1.0.0"],
        ["test", "0.1.0"],
    ],
)
def test_too_high_version(check_version_error, spec, folder: str, version: str):
    spec["info"]["version"] = version
    check_version_error(f"{folder}/Company/BasicInfo", spec, err.TooHighVersion)


@pytest.mark.parametrize(
    "version,file_version",
    [
        ["0.0.1", "0.0"],
        ["0.0.2", "0.0"],
    ],
)
def test_too_low_version(check_version_error, spec, version: str, file_version: str):
    spec["info"]["version"] = version
    check_version_error(f"Company/BasicInfo_v{file_version}", spec, err.TooLowVersion)


@pytest.mark.parametrize(
    "filename",
    [
        "Company/BasicInfo",
        "Company/BasicInfo_vabc",
        "Company/BasicInfo_v1",
        "Company/BasicInfo_v1.1.0",
        "Company/BasicInfo_v_1.0",
        "Company/BasicInfo_1.1",
    ],
)
def test_incorrect_filename_version(check_version_error, spec, filename: str):
    check_version_error(filename, spec, err.InvalidOrMissingVersionInFileName)


@pytest.mark.parametrize(
    "version,file_version",
    [
        ["1.0.0", "1.1"],
        ["1.1.0", "1.0"],
        ["2.0.0", "1.0"],
    ],
)
def test_version_missmatch(check_version_error, spec, version: str, file_version: str):
    spec["info"]["version"] = version
    check_version_error(
        f"Company/BasicInfo_v{file_version}", spec, err.VersionMissmatch
    )


@pytest.mark.parametrize(
    "version,filename",
    [
        ["0.0.1", "test/Company/BasicInfo"],
        ["0.0.2", "test/Company/BasicInfo"],
        ["0.0.1", "draft/Company/BasicInfo"],
        ["0.0.200", "draft/Company/BasicInfo"],
        ["0.1.0", "Company/BasicInfo_v0.1"],
        ["0.1.1", "Company/BasicInfo_v0.1"],
        ["0.1.2", "Company/BasicInfo_v0.1"],
        ["1.0.0", "Company/BasicInfo_v1.0"],
        ["1.1.0-beta", "Company/BasicInfo_v1.1-beta"],
        ["1.1.0-beta.2", "Company/BasicInfo_v1.1-beta.2"],
        ["1.1.0", "Company/BasicInfo_v1.1"],
        ["12.34.56", "Company/BasicInfo_v12.34"],
    ],
)
def test_valid_versions(validate_definition, spec, version: str, filename: str):
    spec["info"]["version"] = version
    validate_definition(filename, spec)
