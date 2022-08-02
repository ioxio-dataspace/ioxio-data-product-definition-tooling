import json
from pathlib import Path

import pytest

from converter import (
    CamelCaseModel,
    DataProductDefinition,
    convert_data_product_definitions,
)


def test_air_quality(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "AirQuality" / "Current.json"
    assert dest_file.exists()

    dest_spec = json.loads(dest_file.read_text("utf-8"))
    assert json_snapshot == dest_spec


def test_current_weather_required_headers(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "Weather" / "Current" / "Metric.json"
    assert dest_file.exists()

    dest_spec = json.loads(dest_file.read_text("utf-8"))
    assert json_snapshot == dest_spec


def test_data_product_definition_fallbacks():
    summary = "FooBar summary"

    # Summary as fallback for description and route description
    dpd = DataProductDefinition(
        summary=summary,
        name="Foo/Bar",
        request=CamelCaseModel,
        response=CamelCaseModel,
    )
    assert dpd.description == summary
    assert dpd.summary == summary
    assert dpd.route_description == summary

    # Summary as fallback for route description only
    description = "FooBar description"
    dpd = DataProductDefinition(
        summary=summary,
        description=description,
        name="Foo/Bar",
        request=CamelCaseModel,
        response=CamelCaseModel,
    )
    assert dpd.description == description
    assert dpd.summary == summary
    assert dpd.route_description == summary

    # Summary as fallback for description only
    route_description = "FooBar route description"
    dpd = DataProductDefinition(
        summary=summary,
        route_description=route_description,
        name="Foo/Bar",
        request=CamelCaseModel,
        response=CamelCaseModel,
    )
    assert dpd.description == summary
    assert dpd.summary == summary
    assert dpd.route_description == route_description

    # Missing summary
    with pytest.raises(ValueError):
        DataProductDefinition(
            description=description,
            route_description=route_description,
            name="Foo/Bar",
            request=CamelCaseModel,
            response=CamelCaseModel,
        )
