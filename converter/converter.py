import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Optional, Type

from deepdiff import DeepDiff
from fastapi import FastAPI, Header
from pydantic import BaseModel
from stringcase import camelcase


class CamelCaseModel(BaseModel):
    class Config:
        alias_generator = camelcase
        allow_population_by_field_name = True


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.summary:
            if not self.route_description:
                self.route_description = self.summary
            if not self.description:
                self.description = self.summary


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

    @app.post(
        f"/{definition.name}",
        summary=definition.route_summary,
        description=definition.route_description,
        response_model=definition.response,
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
        module = spec.loader.load_module(str(p))
        definition: DataProductDefinition = getattr(module, "DEFINITION")
        if not definition:
            raise ValueError(f"Error finding DEFINITION variable in {p}")

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
