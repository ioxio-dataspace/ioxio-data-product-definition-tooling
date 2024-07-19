import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type

from deepdiff import DeepDiff
from fastapi import FastAPI, Header
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetJsonSchemaHandler,
    ValidationError,
    field_validator,
)
from pydantic.alias_generators import to_camel
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from rich import print
from semver import Version
from typing_extensions import Annotated

from definition_tooling.api_errors import DATA_PRODUCT_ERRORS


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ErrorModel(BaseModel):
    """
    Wrapper used for error responses, see ErrorResponse decorator for more details.

    Encapsulates the actual model and a description for the error.
    """

    model: Type[BaseModel]
    description: str


class ErrorResponse:
    """
    Decorator that should be used around any models that define an error to be used in
    DataProductDefinition.error_responses. It will wrap the class in an ErrorModel in
    order to define and store a custom description for the error in addition to the
    actual model.

    Usage:

    @ErrorResponse(description="Not found")
    class NotFoundResponse(CamelCaseModel):
        ...


    DEFINITION = DataProductDefinition(
        ...
        error_responses={
            404: NotFoundResponse,
        }
    )
    """

    def __init__(self, description: str) -> None:
        self.description = description

    def __call__(self, model_cls: Type[BaseModel]) -> ErrorModel:
        return ErrorModel(
            model=model_cls,
            description=self.description,
        )


ERROR_CODE = Annotated[int, Field(ge=400, lt=600)]


class PydanticVersion(Version):
    """
    This class is based on:
    https://python-semver.readthedocs.io/en/latest/advanced/combine-pydantic-and-semver.html
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Version:
            return Version.parse(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Version),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Inject/mutate the pydantic field schema in-place."""
        return handler(core_schema.str_schema())


class DataProductDefinition(BaseModel):
    version: PydanticVersion = "0.0.1"
    deprecated: bool = False
    description: str
    error_responses: Dict[ERROR_CODE, ErrorModel] = {}
    request: Type[BaseModel]
    requires_authorization: bool = False
    requires_consent: bool = False
    response: Type[BaseModel]
    title: str
    tags: Iterable[str] = []

    @field_validator("error_responses")
    @classmethod
    def validate_error_responses(cls, v: Dict[ERROR_CODE, ErrorModel]):
        status_codes = set(v.keys())
        reserved_status_codes = set(DATA_PRODUCT_ERRORS.keys())
        overlapping = status_codes.intersection(reserved_status_codes)
        if overlapping:
            raise ValueError(
                "Can not contain reserved error code(s): "
                f"{', '.join(str(n) for n in overlapping)}"
            )
        return v


def export_openapi_spec(
    definition: DataProductDefinition, definition_name: str
) -> dict:
    """
    Given a data product definition, create a FastAPI application and a corresponding
    POST route. Then export its OpenAPI spec
    :param definition: Data product definition
    :return: OpenAPI spec
    """
    app = FastAPI(
        title=definition.title,
        description=definition.description,
        version=str(definition.version),
    )

    if definition.requires_authorization:
        authorization_header_type = str
        authorization_header_default_value = ...
    else:
        authorization_header_type = str
        authorization_header_default_value = ""

    if definition.requires_consent:
        consent_header_type = str
        consent_header_default_value = ...
        consent_header_description = "Consent token"
    else:
        consent_header_type = str
        consent_header_default_value = ""
        consent_header_description = "Optional consent token"

    responses = {
        code: {
            "model": error_model.model,
            "description": error_model.description,
        }
        for code, error_model in definition.error_responses.items()
    }
    responses.update(DATA_PRODUCT_ERRORS)

    @app.post(
        f"/{definition_name}",
        summary=definition.title,
        description=definition.description,
        response_model=definition.response,
        responses=responses,
        deprecated=definition.deprecated,
        tags=sorted(set(definition.tags)),
    )
    def request(
        params: definition.request,
        x_consent_token: consent_header_type = Header(
            consent_header_default_value,
            description=consent_header_description,
        ),
        authorization: authorization_header_type = Header(
            authorization_header_default_value,
            description='The login token. Value should be "Bearer [token]"',
        ),
        x_authorization_provider: Optional[str] = Header(
            None, description="The bare domain of the system that provided the token."
        ),
        x_api_key: Optional[str] = Header(
            None, title="X-API-Key", description="API key or token"
        ),
    ):
        pass

    openapi = app.openapi()

    for path, data in openapi["paths"].items():
        operation_id = data["post"]["operationId"].removesuffix("_post")
        openapi["paths"][path]["post"]["operationId"] = operation_id

    return openapi


def styled_error(error: str, path: Path) -> str:
    """
    Style error messages to make them clearer and easier to read
    """
    return f"[bold red]{error}[/bold red] in [yellow]{path}[/yellow]:exclamation:"


def convert_data_product_definitions(src: Path, dest: Path) -> bool:
    """
    Browse folder for definitions defined as python files
    and export them to corresponding OpenAPI specs in the output folder
    """

    should_fail_hook = False
    modified_files = []
    for p in src.glob("**/*.py"):
        # Get definition name based on file path
        definition_name = p.relative_to(src).with_suffix("").as_posix()

        # generate a python module name based on the definition name/path
        module_name = definition_name.replace(".", "_").replace("/", ".")
        spec = importlib.util.spec_from_file_location(name=module_name, location=str(p))
        if not spec.loader:
            raise RuntimeError(f"Failed to import {p} module")
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except ValidationError as e:
            should_fail_hook = True
            print(styled_error("Validation error", p))
            print(e)
            continue

        try:
            definition: DataProductDefinition = getattr(module, "DEFINITION")
        except AttributeError:
            print(styled_error("Error finding DEFINITION variable", p))
            continue

        openapi = export_openapi_spec(definition, definition_name)

        out_file = (dest / p.relative_to(src)).with_suffix(".json")

        current_spec = {}
        if out_file.exists():
            current_spec = json.loads(out_file.read_text(encoding="utf-8"))

        # Write resulted JSON only if it's changed to satisfy pre-commit hook
        if DeepDiff(current_spec, openapi, ignore_order=True) != {}:
            print(f"Exporting {out_file}")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(
                json.dumps(openapi, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            modified_files.append(out_file)
            # Hook should fail as we modified the file.
            should_fail_hook = True
        else:
            if file_is_untracked(out_file):
                print(f"Untracked {out_file}")
                should_fail_hook = True
            else:
                print(f"Skipping {out_file}")

    # Run hooks on all modified files at once to save overhead from subprocess
    if modified_files:
        run_pre_commit_hooks_on_files(modified_files)

    return should_fail_hook


def run_pre_commit_hooks_on_files(files: List[Path]) -> None:
    """
    Run pre-commit hooks on files.
    """
    files = [str(file) for file in files]
    subprocess.run(
        [
            "pre-commit",
            "run",
            "--files",
            *files,
        ],
        capture_output=True,
    )


def file_is_untracked(file: Path) -> bool:
    """
    Check if the file is untracked in git.
    """
    completed_process = subprocess.run(
        ["git", "status", "--short", str(file)],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return completed_process.stdout.startswith("??")
