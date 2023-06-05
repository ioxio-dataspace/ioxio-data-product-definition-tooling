import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Type

from deepdiff import DeepDiff
from fastapi import FastAPI, Header
from pydantic import BaseModel, ValidationError, conint, validator
from rich import print
from stringcase import camelcase

from converter.errors import DATA_PRODUCT_ERRORS


class CamelCaseModel(BaseModel):
    class Config:
        alias_generator = camelcase
        allow_population_by_field_name = True


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


ERROR_CODE = conint(ge=400, lt=600)


class DataProductDefinition(BaseModel):
    description: Optional[str]
    name: Optional[str]
    request: Type[BaseModel]
    response: Type[BaseModel]
    route_description: Optional[str]
    route_summary: Optional[str]
    summary: str
    requires_authorization: bool = False
    requires_consent: bool = False
    error_responses: Dict[ERROR_CODE, ErrorModel] = {}
    deprecated: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.summary:
            if not self.route_description:
                self.route_description = self.summary
            if not self.description:
                self.description = self.summary
            if not self.route_summary:
                self.route_summary = self.summary

    @validator("error_responses")
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


def export_openapi_spec(definition: DataProductDefinition) -> dict:
    """
    Given a data product definition, create a FastAPI application and a corresponding
    POST route. Then export its OpenAPI spec
    :param definition: Data product definition
    :return: OpenAPI spec
    """
    app = FastAPI(
        title=definition.summary,
        description=definition.description,
        version="1.0.0",
    )

    if definition.requires_authorization:
        authorization_header_type = str
        authorization_header_default_value = ...
    else:
        authorization_header_type = Optional[str]
        authorization_header_default_value = None

    if definition.requires_consent:
        consent_header_type = str
        consent_header_default_value = ...
        consent_header_description = "Consent token"
    else:
        consent_header_type = Optional[str]
        consent_header_default_value = None
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
        f"/{definition.name}",
        summary=definition.route_summary,
        description=definition.route_description,
        response_model=definition.response,
        responses=responses,
        deprecated=definition.deprecated,
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
    for p in src.glob("**/*.py"):
        spec = importlib.util.spec_from_file_location(name=str(p), location=str(p))
        if not spec.loader:
            raise RuntimeError(f"Failed to import {p} module")
        try:
            module = spec.loader.load_module(str(p))
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

        # Get definition name based on file path
        definition.name = p.relative_to(src).with_suffix("").as_posix()
        if not definition.route_summary:
            definition.route_summary = definition.name

        openapi = export_openapi_spec(definition)

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
            run_pre_commit_hooks_on_file(out_file)
            # Hook should fail as we modified the file.
            should_fail_hook = True
        else:
            if file_is_untracked(out_file):
                print(f"Untracked {out_file}")
                should_fail_hook = True
            else:
                print(f"Skipping {out_file}")

    return should_fail_hook


def run_pre_commit_hooks_on_file(file: Path) -> None:
    """
    Run pre-commit hooks on a file.
    """
    subprocess.run(
        [
            "pre-commit",
            "run",
            "--files",
            str(file),
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
