from pydantic import Field

from definition_tooling.converter import (
    CamelCaseModel,
    DataProductDefinition,
    ErrorResponse,
)


class BasicCompanyInfoRequest(CamelCaseModel):
    company_id: str = Field(
        ...,
        title="Company ID",
        description="The ID of the company",
        examples=["2464491-9"],
    )


class BasicCompanyInfoResponse(CamelCaseModel):
    name: str = Field(
        ..., title="Name of the company", examples=["Digital Living International Oy"]
    )
    company_id: str = Field(..., title="ID of the company", examples=["2464491-9"])
    company_form: str = Field(
        ..., title="The company form of the company", examples=["LLC"]
    )
    registration_date: str = Field(
        ..., title="Date of registration for the company", examples=["2012-02-23"]
    )


@ErrorResponse(description="Unavailable for some legal reasons")
class UnavailableForLegalReasonsResponse(CamelCaseModel):
    reasons: str = Field(
        ...,
        title="Reason",
        description="The reason why the data is not available",
    )


DEFINITION = DataProductDefinition(
    version="1.0.0",
    title="Information about a company",
    description="Legal information about a company such as registration address",
    request=BasicCompanyInfoRequest,
    response=BasicCompanyInfoResponse,
    error_responses={
        422: UnavailableForLegalReasonsResponse,
    },
)
