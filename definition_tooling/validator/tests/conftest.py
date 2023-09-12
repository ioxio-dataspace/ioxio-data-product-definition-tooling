import json
from copy import deepcopy
from pathlib import Path

import pytest

SPECS_ROOT_DIR = Path(__file__).absolute().parent / "data"
COMPANY_BASIC_INFO: dict = json.loads(
    (SPECS_ROOT_DIR / "CompanyBasicInfo.json").read_text(encoding="utf8")
)


@pytest.fixture
def company_basic_info():
    """
    Fixture that returns a deepcopy of the Company Basic Info to use in tests.
    The tests can freely modify it and corrupt it (easier than having multiple corrupt
    definitions in the repo).

    For performance reasons we load it once from filesystem (outside the fixture).
    """
    return deepcopy(COMPANY_BASIC_INFO)
