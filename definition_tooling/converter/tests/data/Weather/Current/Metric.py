from pydantic import Field

from converter import CamelCaseModel, DataProductDefinition


class CurrentWeatherMetricRequest(CamelCaseModel):
    lat: float = Field(
        ...,
        title="Latitude",
        description="The latitude coordinate of the desired location",
        ge=-90.0,
        le=90.0,
        example=60.192059,
    )
    lon: float = Field(
        ...,
        title="Longitude",
        description="The longitude coordinate of the desired location",
        ge=-180.0,
        le=180.0,
        example=24.945831,
    )


class CurrentWeatherMetricResponse(CamelCaseModel):
    humidity: float = Field(..., title="Current relative air humidity in %", example=72)
    pressure: float = Field(..., title="Current air pressure in hPa", example=1007)
    rain: bool = Field(
        ..., title="Rain status", description="If it's currently raining or not."
    )
    temp: float = Field(
        ..., title="Current temperature in Celsius", example=17.3, ge=-273.15
    )
    wind_speed: float = Field(..., title="Current wind speed in m/s", example=2.1, ge=0)
    wind_direction: float = Field(
        ...,
        title="Current wind direction in meteorological wind direction degrees",
        ge=0,
        le=360,
        example=220.0,
    )


DEFINITION = DataProductDefinition(
    description="Data Product for current weather with metric units",
    request=CurrentWeatherMetricRequest,
    response=CurrentWeatherMetricResponse,
    route_description="Current weather in metric units",
    summary="Current Weather (Metric)",
    requires_authorization=True,
    requires_consent=True,
)
