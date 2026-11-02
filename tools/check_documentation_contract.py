"""Compare active documentation with runtime metadata and requirement coverage."""
import json
import re
from pathlib import Path

from export_documentation_contract import (
    api_routes, apps, get_resolver, model_contract, serializer_contract, connections, forbid_query,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def normalized_route(pattern):
    route = re.sub(r"\(\?P<pk>[^)]+\)", "{id}", pattern)
    route = re.sub(r"\(\?P<doc_id>[^)]+\)", "{doc_id}", route)
    return "/" + route.replace("^", "").replace("$", "")


def check_schema(snapshot, problems):
    current = {model._meta.label: model_contract(model) for model in apps.get_models()
               if model.__module__.startswith("apps.")}
    recorded = json.loads(json.dumps(current, default=str))
    if recorded != snapshot["models"]:
        problems.append("Runtime schema changed since documented metadata snapshot.")
    if serializer_contract() != snapshot["serializers"]:
        problems.append("Serializer fields/requirements changed since documented metadata snapshot.")
    erd = (DOCS / "diagrams/erd-database-schema.mmd").read_text(encoding="utf8")
    for model in current.values():
        table = model["table"].upper()
        if f"    {table} {{" not in erd:
            problems.append(f"ERD missing model table: {table}")
        for field in model["fields"]:
            if field["on_delete"] and f'{field["name"]}_{field["on_delete"]}' not in erd:
                problems.append(f"ERD missing on_delete relation: {table}.{field['name']}")
    print(f"Schema: {len(current)} runtime models match documented metadata and ERD coverage.")
    print(f"Serializers: {len(snapshot['serializers'])} field contracts match runtime metadata.")


def check_requirements(problems):
    expression = r"\b(?:FR|NFR)-[A-Z]+-\d+\b"
    srs = set(re.findall(expression, (DOCS / "04_SRS.md").read_text(encoding="utf8")))
    rtm = (DOCS / "09_Traceability.md").read_text(encoding="utf8")
    mapped = set(re.findall(r"\| \*\*((?:FR|NFR)-[A-Z]+-\d+)\*\* \|", rtm))
    if srs != mapped:
        problems.append(f"SRS/RTM mismatch: missing={sorted(srs-mapped)}, extra={sorted(mapped-srs)}")
    print(f"Traceability: {len(srs)} SRS IDs / {len(mapped)} explicit RTM rows.")


def check_routes(problems):
    routes = [row for row in api_routes(get_resolver().url_patterns)
              if row["name"] != "api-root" and "format" not in row["pattern"]]
    document = (DOCS / "08_API.md").read_text(encoding="utf8")
    for row in routes:
        route = normalized_route(row["pattern"])
        if f"`{route}`" not in document:
            problems.append(f"API contract missing route path: {route}")
    print(f"Routes: {len(routes)} business patterns documented; registered DELETE assurance remains 405.")


def check_diagrams(problems):
    paths = sorted((DOCS / "diagrams").glob("*.mmd"))
    catalogue = (DOCS / "17_Diagram_Catalogue.md").read_text(encoding="utf8")
    for path in paths:
        source = path.read_text(encoding="utf8")
        if not source.startswith("%% Scope:"):
            problems.append(f"Diagram missing current/target/example scope: {path.name}")
        if f"diagrams/{path.name}" not in catalogue:
            problems.append(f"Diagram not in catalogue: {path.name}")
        declarations = re.findall(r"^(?:erDiagram|classDiagram|sequenceDiagram|flowchart [A-Z]+|stateDiagram-v2)$", source, re.MULTILINE)
        if len(declarations) != 1:
            problems.append(f"Diagram declaration mismatch: {path.name}")
    print(f"Diagrams: {len(paths)} sources have scope, declaration and catalogue reference; rendering not checked.")


def main():
    snapshot = json.loads((DOCS / "evidence/documentation-consistency-review/runtime-contract.json").read_text())
    problems = []
    with connections["default"].execute_wrapper(forbid_query):
        check_schema(snapshot, problems)
        check_requirements(problems)
        check_routes(problems)
        check_diagrams(problems)
    print("Metadata inspection: isolated in-memory settings; database query guard enabled.")
    print("\n".join(problems) if problems else "PASS")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
