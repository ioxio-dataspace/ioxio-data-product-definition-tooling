"""
Predefined errors that the product gateway or data sources can return.

These errors can not be overridden by the data product definition itself.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


def type_field(*, is_literal: bool = False, examples: Optional[List[str]] = None):
    return Field(
        ...,
        title="Error type",
        description="An identifier for the type of error.",
        pattern=None if is_literal else r"^[a-z0-9_]*$",
        examples=examples,
    )


def message_field(*, examples: Optional[List[str]] = None):
    return Field(
        ...,
        title="Error message",
        description="A human readable description of the error.",
        examples=examples,
    )


class BaseApiError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    __status__: int

    @classmethod
    def get_response_spec(cls):
        return {"model": cls}


class ApiError(BaseApiError):
    type: StrictStr = type_field(
        examples=["error_type"],
    )
    message: StrictStr = message_field()


class ApiOrExternalError(ApiError):
    @classmethod
    def get_response_spec(cls):
        return {"model": cls, "content": {"text/plain": {}, "text/html": {}}}


class BadRequest(ApiError):
    __status__ = 400
    type: StrictStr = type_field(examples=["validation_error"])
    message: StrictStr = message_field(
        examples=["Validation failed for fieldName: error description."]
    )


class Unauthorized(ApiError):
    __status__ = 401
    type: StrictStr = type_field(examples=["api_token_missing_or_invalid"])
    message: StrictStr = message_field(examples=["The API token has expired"])


class Forbidden(ApiError):
    __status__ = 403
    type: StrictStr = type_field(examples=["forbidden"])
    message: StrictStr = message_field(
        examples=["No access to requested data for group 'example'."]
    )


class NotFound(ApiError):
    __status__ = 404
    type: StrictStr = type_field(examples=["not_found"])
    message: StrictStr = message_field(examples=["Not found"])


# Note: 422 is added automatically by FastAPI


class RateLimitExceeded(ApiError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 429
    type: StrictStr = type_field(examples=["rate_limit_exceeded"])
    message: StrictStr = message_field(examples=["Rate limit exceeded"])


class DataSourceNotFound(ApiError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 444
    type: Literal["data_source_not_found"] = type_field(is_literal=True)
    message: StrictStr = message_field(
        examples=["Data source not found"],
    )


class DataSourceError(ApiError):
    __status__ = 500
    type: StrictStr = type_field(examples=["upstream_error"])
    message: StrictStr = message_field(
        examples=["Failed to connect to the upstream service, please try again later."]
    )


class BadGateway(ApiError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 502
    type: Literal["bad_gateway"] = type_field(is_literal=True)
    message: StrictStr = message_field(examples=["Bad Gateway"])


class ServiceUnavailable(ApiOrExternalError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 503
    type: Literal["service_unavailable"] = type_field(is_literal=True)
    message: StrictStr = message_field(examples=["Service Unavailable"])


class GatewayTimeout(ApiOrExternalError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 504
    type: Literal["gateway_timeout"] = type_field(is_literal=True)
    message: StrictStr = message_field(examples=["Gateway Timeout"])


class DoesNotConformToDefinition(ApiError):
    """
    This response is reserved by Product Gateway.
    """

    __status__ = 550
    type: Literal["does_not_conform_to_definition"] = type_field(is_literal=True)
    message: StrictStr = message_field(
        examples=["Response from data source does not conform to definition"],
    )
    data_source_status_code: StrictInt = Field(
        ...,
        title="Data source status code",
        description="HTTP status code returned from the data source",
        examples=[200],
    )


DATA_PRODUCT_ERRORS = {
    resp.__status__: resp.get_response_spec()
    for resp in [
        BadRequest,
        Unauthorized,
        Forbidden,
        NotFound,
        RateLimitExceeded,
        DataSourceNotFound,
        DataSourceError,
        BadGateway,
        ServiceUnavailable,
        GatewayTimeout,
        DoesNotConformToDefinition,
    ]
}
