import pytest
from syrupy.extensions.json import JSONSnapshotExtension


@pytest.fixture
def json_snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)
