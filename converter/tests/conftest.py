import pytest

from converter.tests.helpers import JSONSnapshotExtension


@pytest.fixture
def json_snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)
