from typing import List

from pydantic import Field

from converter import CamelCaseModel, DataProductDefinition


class CurrentAirQualityRequest(CamelCaseModel):
    lat: float = Field(
        ...,
        title="Latitude",
        description="The latitude coordinate of the desired location",
        example=60.192059,
        ge=-90,
        le=90,
    )
    lon: float = Field(
        ...,
        title="Longitude",
        description="The longitude coordinate of the desired location",
        example=24.945831,
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
        example=30,
    )
    timestamp: str = Field(
        ...,
        title="Timestamp",
        description="Current timestamp in RFC 3339 format",
        example="2020-04-03T13:00:00Z",
    )
    attribution: List[str] = Field(
        ...,
        title="Source Attribution",
        description="List of text to show required credits to data sources",
        example=["Moscow State environmental monitoring"],
    )


DEFINITION = DataProductDefinition(
    description="Data Product for current air quality index",
    request=CurrentAirQualityRequest,
    response=CurrentAirQualityResponse,
    route_description="Current air quality",
    summary="Air Quality Index",
)
