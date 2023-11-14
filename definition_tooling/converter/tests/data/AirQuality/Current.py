from typing import List

from pydantic import Field

from definition_tooling.converter import CamelCaseModel, DataProductDefinition


class CurrentAirQualityRequest(CamelCaseModel):
    lat: float = Field(
        ...,
        title="Latitude",
        description="The latitude coordinate of the desired location",
        examples=[60.192059],
        ge=-90,
        le=90,
    )
    lon: float = Field(
        ...,
        title="Longitude",
        description="The longitude coordinate of the desired location",
        examples=[24.945831],
        ge=-180,
        le=180,
    )


class CurrentAirQualityResponse(CamelCaseModel):
    air_quality_index: int = Field(
        ...,
        title="Air Quality Index",
        description=(
            "Current air quality index.\nRanges:\n0-50 Good;\n51-100 Moderate;\n"
            "101-150 Unhealthy For Sensitive Groups;\n151-200 Unhealthy;\n"
            "201-300 Very Unhealthy;\n301+ Hazardous"
        ),
        ge=0,
        examples=[30],
    )
    timestamp: str = Field(
        ...,
        title="Timestamp",
        description="Current timestamp in RFC 3339 format",
        examples=["2020-04-03T13:00:00Z"],
    )
    attribution: List[str] = Field(
        ...,
        title="Source Attribution",
        description="List of text to show required credits to data sources",
        examples=[["Moscow State environmental monitoring"]],
    )


DEFINITION = DataProductDefinition(
    version="1.0.0",
    title="Air Quality Index",
    description="Data Product for current air quality index",
    request=CurrentAirQualityRequest,
    response=CurrentAirQualityResponse,
)
