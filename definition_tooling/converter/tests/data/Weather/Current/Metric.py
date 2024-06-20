from pydantic import Field

from definition_tooling.converter import CamelCaseModel, DataProductDefinition


class CurrentWeatherMetricRequest(CamelCaseModel):
    lat: float = Field(
        ...,
        title="Latitude",
        description="The latitude coordinate of the desired location",
        ge=-90.0,
        le=90.0,
        examples=[60.192059],
    )
    lon: float = Field(
        ...,
        title="Longitude",
        description="The longitude coordinate of the desired location",
        ge=-180.0,
        le=180.0,
        examples=[24.945831],
    )


class CurrentWeatherMetricResponse(CamelCaseModel):
    humidity: float = Field(
        ..., title="Current relative air humidity in %", examples=[72]
    )
    pressure: float = Field(..., title="Current air pressure in hPa", examples=[1007])
    rain: bool = Field(
        ..., title="Rain status", description="If it's currently raining or not."
    )
    temp: float = Field(
        ..., title="Current temperature in Celsius", examples=[17.3], ge=-273.15
    )
    wind_speed: float = Field(
        ..., title="Current wind speed in m/s", examples=[2.1], ge=0
    )
    wind_direction: float = Field(
        ...,
        title="Current wind direction in meteorological wind direction degrees",
        ge=0,
        le=360,
        examples=[220.0],
    )


DEFINITION = DataProductDefinition(
    version="1.0.0",
    title="Current weather in a given location",
    description="Current weather in a given location in metric units",
    request=CurrentWeatherMetricRequest,
    response=CurrentWeatherMetricResponse,
    requires_authorization=True,
    requires_consent=True,
    tags={"temperature", "wind", "rain", "humidity"},
)
