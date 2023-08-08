from pydantic import Field

from definition_tooling.converter import (
    CamelCaseModel,
    DataProductDefinition,
    ErrorResponse,
)


class CoffeeBrewingRequest(CamelCaseModel):
    brew: str = Field(
        ...,
        title="Brew",
        description="Kind of drink to brew",
        example="coffee",
    )


class CoffeeBrewingResponse(CamelCaseModel):
    ok: bool = Field(
        ...,
        title="OK",
        example=True,
    )


@ErrorResponse(description="I'm a teapot")
class TeaPotError(CamelCaseModel):
    ok: bool = Field(
        ...,
        title="OK",
        example=False,
    )
    error_message: str = Field(
        ...,
        title="Error message",
        example="I'm a teapot",
    )


DEFINITION = DataProductDefinition(
    request=CoffeeBrewingRequest,
    response=CoffeeBrewingResponse,
    summary="Coffee brewer",
    error_responses={
        418: TeaPotError,
    },
    deprecated=True,
)
