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
        examples=["coffee"],
    )


class CoffeeBrewingResponse(CamelCaseModel):
    ok: bool = Field(
        ...,
        title="OK",
        examples=[True],
    )


@ErrorResponse(description="I'm a teapot")
class TeaPotError(CamelCaseModel):
    ok: bool = Field(
        ...,
        title="OK",
        examples=[False],
    )
    error_message: str = Field(
        ...,
        title="Error message",
        examples=["I'm a teapot"],
    )


DEFINITION = DataProductDefinition(
    version="0.1.0",
    title="Coffee brewer",
    description="Coffee brewer",
    request=CoffeeBrewingRequest,
    response=CoffeeBrewingResponse,
    error_responses={
        418: TeaPotError,
    },
    deprecated=True,
    # On purpose duplicate tag to verify the final spec doesn't have any duplicates
    tags=["coffee", "brewer", "coffee"],
)
