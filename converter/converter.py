import importlib.util
import json
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
    generic_description: Optional[str]
    name: Optional[str]
    request: Type[BaseModel]
    response: Type[BaseModel]
    route_description: Optional[str]
    route_summary: Optional[str]
    summary: Optional[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if generic_description := kwargs.get("generic_description"):
            if not self.route_description:
                self.route_description = generic_description
            if not self.summary:
                self.summary = generic_description
            if not self.description:
                self.description = f"Data Product for {generic_description}"

        if not self.route_description:
            self.route_description = f"{self.name} Data Product"

        if not generic_description and (not self.description or not self.summary):
            raise ValueError(f"Please define required fields for {self.name}")


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

    @app.post(
        f"/{definition.name}",
        summary=definition.route_summary,
        description=definition.route_description,
        response_model=definition.response,
    )
    def request(
        params: definition.request,
        x_consent_token: Optional[str] = Header(
            None,
            description="Optional consent token",
        ),
        authorization: Optional[str] = Header(
            None, description='The login token. Value should be "Bearer [token]"'
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


def convert_data_product_definitions(src: Path, dest: Path):
    """
    Browse folder for definitions defined as python files
    and export them to corresponding OpenAPI specs in the output folder
    """

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
        else:
            print(f"Skipping {out_file}")
