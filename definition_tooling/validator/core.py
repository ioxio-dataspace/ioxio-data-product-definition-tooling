import abc
import json
from pathlib import Path
from typing import Union

from definition_tooling.api_errors import DATA_PRODUCT_ERRORS
from definition_tooling.validator import errors as err


class BaseValidator:
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def validate(self):
        try:
            spec = json.loads(self.path.read_text(encoding="utf8"))
        except json.JSONDecodeError:
            raise err.InvalidJSON(f"Incorrect JSON: {self.path}")
        except Exception as e:
            raise err.ValidatorError(f"Failed to validate {self.path}: {e}")
        self.validate_spec(spec)

    @abc.abstractmethod
    def validate_spec(self, spec: dict):
        raise NotImplementedError


class DefaultValidator(BaseValidator):
    def validate_spec(self, spec: dict):
        if not spec.get("openapi", "").startswith("3"):
            raise err.UnsupportedVersion


def validate_component_schema(spec: dict, components_schema: dict):
    if not spec["content"].get("application/json"):
        raise err.WrongContentType
    ref = spec["content"]["application/json"].get("schema", {}).get("$ref")
    if not ref:
        raise err.SchemaMissing(
            'Request or response model is missing from "schema/$ref" section'
        )
    if not ref.startswith("#/components/schemas/"):
        raise err.SchemaMissing(
            "Request and response models must be defined in the"
            '"#/components/schemas/" section'
        )
    model_name = ref.split("/")[-1]
    if not components_schema.get(model_name):
        raise err.SchemaMissing(f"Component schema is missing for {model_name}")


def validate_spec(spec: dict):
    """
    Validate that OpenAPI spec looks like a data product definition. For example, that
    it only has one POST method defined.

    :param spec: OpenAPI spec
    :raises OpenApiValidationError: When OpenAPI spec is incorrect
    """
    if "servers" in spec:
        raise err.ServersShouldNotBeDefined

    if not spec.get("openapi", "").startswith("3"):
        raise err.UnsupportedVersion

    paths = spec.get("paths", {})
    if not paths:
        raise err.NoEndpointsDefined
    if len(paths) > 1:
        raise err.OnlyOneEndpointAllowed

    post_route = {}
    for name, path in paths.items():
        methods = list(path)
        if "post" not in methods:
            raise err.PostMethodIsMissing
        if methods != ["post"]:
            raise err.OnlyPostMethodAllowed
        post_route = path["post"]

    component_schemas = spec.get("components", {}).get("schemas")
    if not component_schemas:
        raise err.SchemaMissing('No "components/schemas" section defined')

    if "security" in post_route:
        raise err.SecurityShouldNotBeDefined

    if post_route.get("requestBody", {}).get("content"):
        validate_component_schema(post_route["requestBody"], component_schemas)

    responses = post_route.get("responses", {})
    if not responses.get("200") or not responses["200"].get("content"):
        raise err.ResponseBodyMissing
    validate_component_schema(responses["200"], component_schemas)

    for code in list(DATA_PRODUCT_ERRORS) + [422]:
        if not responses.get(str(code)):
            raise err.HTTPResponseIsMissing(f"Missing response for {code} status code")

    headers = [
        param.get("name", "").lower()
        for param in post_route.get("parameters", [])
        if param.get("in") == "header"
    ]
    if "authorization" not in headers:
        raise err.AuthorizationHeaderMissing
    if "x-authorization-provider" not in headers:
        raise err.AuthProviderHeaderMissing


class DefinitionValidator(BaseValidator):
    def validate_spec(self, spec: dict):
        # it's moved to separate function to reduce indentation
        return validate_spec(spec)
