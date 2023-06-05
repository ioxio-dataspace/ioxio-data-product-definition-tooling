from pydantic import Field

from converter import CamelCaseModel, DataProductDefinition, ErrorResponse


class BasicCompanyInfoRequest(CamelCaseModel):
    company_id: str = Field(
        ...,
        title="Company ID",
        description="The ID of the company",
        example="2464491-9",
    )


class BasicCompanyInfoResponse(CamelCaseModel):
    name: str = Field(
        ..., title="Name of the company", example="Digital Living International Oy"
    )
    company_id: str = Field(..., title="ID of the company", example="2464491-9")
    company_form: str = Field(
        ..., title="The company form of the company", example="LLC"
    )
    registration_date: str = Field(
        ..., title="Date of registration for the company", example="2012-02-23"
    )


@ErrorResponse(description="Unavailable for some legal reasons")
class UnavailableForLegalReasonsResponse(CamelCaseModel):
    reasons: str = Field(
        ...,
        title="Reason",
        description="The reason why the data is not available",
    )


DEFINITION = DataProductDefinition(
    description="Data Product for basic company info",
    request=BasicCompanyInfoRequest,
    response=BasicCompanyInfoResponse,
    route_description="Information about the company",
    summary="Basic Company Info",
    error_responses={
        422: UnavailableForLegalReasonsResponse,
    },
)
