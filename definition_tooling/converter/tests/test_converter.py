import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from definition_tooling.converter import (
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


def test_company_basic_info_errors(tmpdir, json_snapshot):
    """
    Test with a definition that includes custom error message
    """
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "Company" / "BasicInfo.json"
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


def test_teapot_deprecated(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "Appliance" / "CoffeeBrewer.json"
    assert dest_file.exists()

    dest_spec = json.loads(dest_file.read_text("utf-8"))
    assert json_snapshot == dest_spec


def test_required_fields():
    with pytest.raises(ValidationError):
        DataProductDefinition(
            title=None,
            description="Description",
            request=CamelCaseModel,
            response=CamelCaseModel,
        )
    with pytest.raises(ValidationError):
        DataProductDefinition(
            title="Title",
            description=None,
            request=CamelCaseModel,
            response=CamelCaseModel,
        )


def test_summary_and_route_description(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "AirQuality" / "Current.json"
    assert dest_file.exists()

    dest_spec = json.loads(dest_file.read_text("utf-8"))

    title = dest_spec["info"]["title"]
    summary = dest_spec["paths"]["/AirQuality/Current"]["post"]["summary"]
    assert title == summary

    desc = dest_spec["info"]["description"]
    route_desc = dest_spec["paths"]["/AirQuality/Current"]["post"]["description"]
    assert desc == route_desc


def test_tags(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    weather_file = out_dir / "Weather" / "Current" / "Metric.json"
    assert weather_file.exists()
    weather_spec = json.loads(weather_file.read_text("utf-8"))
    weather_tags = weather_spec["paths"]["/Weather/Current/Metric"]["post"]["tags"]
    # Check tags are alphabetically ordered and no duplicates
    assert weather_tags == ["humidity", "rain", "temperature", "wind"]

    coffee_file = out_dir / "Appliance" / "CoffeeBrewer.json"
    assert coffee_file.exists()
    coffee_spec = json.loads(coffee_file.read_text("utf-8"))
    coffee_tags = coffee_spec["paths"]["/Appliance/CoffeeBrewer"]["post"]["tags"]
    # Check tags are alphabetically ordered and no duplicates
    assert coffee_tags == ["brewer", "coffee"]
