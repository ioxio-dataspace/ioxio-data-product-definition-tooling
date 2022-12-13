"""
Predefined errors that the product gateway or productizers can return.

These errors can not be overridden by the data product definition itself.
"""
from typing import Any, Union

from pydantic import BaseModel, Field


class BaseApiError(BaseModel):
    __status__: int
    message: str


class AuthorizationRequired(BaseApiError):
    __status__ = 401
    message: str = "Authorization is required to access this data source"


class AuthorizationRequiredForUnpublished(BaseApiError):
    __status__ = 401
    message: str = "Unpublished data sources require preview token"


class ResponseFor401(BaseModel):
    __status__ = 401
    __root__: Union[AuthorizationRequired, AuthorizationRequiredForUnpublished]


class ConsentRequired(BaseApiError):
    __status__ = 403
    message: str = "Consent is required to access this data source"


class DataSourceNotFound(BaseApiError):
    __status__ = 404
    message: str = "Requested data source is not found"


class DoesNotConformToDefinition(BaseApiError):
    __status__ = 502
    message: str = "Response from the data source does not conform to definition"


class DataSourceError(BaseApiError):
    __status__ = 502
    message: str = "Data source returned an error"
    status: int = Field(
        ...,
        title="Status code",
        description="Status code from the data source",
        ge=400,
    )
    error: Any = Field(
        ...,
        title="Original error",
        description="Raw error from the data source",
    )


class ResponseFor502(BaseModel):
    __status__ = 502
    __root__: Union[DoesNotConformToDefinition, DataSourceError]


class DataSourceUnavailable(BaseApiError):
    __status__ = 503
    message: str = "Error while communicating with the data source"


class DataSourceTimeout(BaseApiError):
    __status__ = 504
    message: str = "Timeout reached while communicating with the data source"


DATA_PRODUCT_ERRORS = {
    resp.__status__: {"model": resp}
    for resp in [
        ResponseFor401,
        ConsentRequired,
        DataSourceNotFound,
        ResponseFor502,
        DataSourceUnavailable,
        DataSourceTimeout,
    ]
}
