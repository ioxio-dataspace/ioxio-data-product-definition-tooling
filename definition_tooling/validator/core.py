import json
from pathlib import Path
from typing import Union

from semver import Version

from definition_tooling.api_errors import DATA_PRODUCT_ERRORS
from definition_tooling.validator import errors as err
from definition_tooling.validator.utils import parse_version_without_patch


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


def validate_version(spec: dict, spec_path: Path, root_path: Path):
    """
    Validate version in definition and filename.

    Definitions in "test/" and "draft/" namespaces should:
    - have versions < 0.1.0
    - not have any version in the filename

    All other definitions should:
    - have version >= 0.1.0
    - have the _v{MAJOR}.{MINOR} number in the filename
    - have versions that match the version in the filename

    :param spec: OpenAPI spec
    :param spec_path: Path to the actual definition
    :param root_path: Path to the root of definitions
    :raises VersionError: When there's a problem with the version number.
    """
    try:
        version = Version.parse(spec["info"]["version"])
    except (ValueError, TypeError, KeyError):
        raise err.InvalidOrMissingVersion

    test_definition = spec_path.is_relative_to(root_path / "test")
    draft_definition = spec_path.is_relative_to(root_path / "draft")
    _, __, file_version_str = spec_path.stem.partition("_v")

    if test_definition or draft_definition:
        if file_version_str:
            raise err.UnexpectedVersionInFilename
        if version >= Version.parse("0.1.0"):
            raise err.TooHighVersion
    else:
        try:
            file_version = parse_version_without_patch(file_version_str)
        except ValueError:
            raise err.InvalidOrMissingVersionInFileName

        if file_version != Version(
            version.major, version.minor, 0, version.prerelease, version.build
        ):
            raise err.VersionMissmatch

        if version < Version.parse("0.1.0"):
            raise err.TooLowVersion


def validate_spec(spec: dict, spec_path: Path, root_path: Path):
    """
    Validate that OpenAPI spec looks like a data product definition. For example, that
    it only has one POST method defined.

    :param spec: OpenAPI spec
    :param spec_path: Path to the actual definition
    :param root_path: Path to the root of specs
    :raises OpenApiValidationError: When OpenAPI spec is incorrect
    """
    if "servers" in spec:
        raise err.ServersShouldNotBeDefined

    if not spec.get("openapi", "").startswith("3."):
        raise err.UnsupportedVersion("Validator supports only OpenAPI 3.x specs")

    for field in {"title", "description"}:
        if not spec.get("info", {}).get(field):
            raise err.MandatoryField(f'{field} is a required field in "info" section')

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

    for field in {"summary", "description"}:
        if not post_route.get(field):
            raise err.MandatoryField(f"{field} is a required field for POST route")

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

    for code in {*DATA_PRODUCT_ERRORS, 422}:
        if not responses.get(str(code)):
            raise err.HTTPResponseIsMissing(f"Missing response for status code {code}")

    headers = [
        param.get("name", "").lower()
        for param in post_route.get("parameters", [])
        if param.get("in") == "header"
    ]
    if "authorization" not in headers:
        raise err.AuthorizationHeaderMissing
    if "x-authorization-provider" not in headers:
        raise err.AuthProviderHeaderMissing

    validate_version(spec=spec, spec_path=spec_path, root_path=root_path)


class DefinitionValidator:
    def __init__(
        self,
        spec_path: Union[str, Path],
        root_path: Union[str, Path],
    ):
        self.root_path = Path(root_path)
        self.spec_path = Path(spec_path)

    def validate(self):
        try:
            spec = json.loads(self.spec_path.read_text(encoding="utf8"))
        except json.JSONDecodeError:
            raise err.InvalidJSON(f"Incorrect JSON: {self.spec_path}")
        except Exception as e:
            raise err.ValidatorError(f"Failed to validate {self.spec_path}: {e}")
        self.validate_spec(spec, spec_path=self.spec_path, root_path=self.root_path)

    @classmethod
    def validate_spec(cls, spec: dict, spec_path: Path, root_path: Path):
        # it's moved to separate function to reduce indentation
        return validate_spec(spec, spec_path=spec_path, root_path=root_path)
