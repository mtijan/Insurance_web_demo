"""Export runtime model/serializer/route metadata without reading application data."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["DJANGO_SETTINGS_MODULE"] = "core.verification_settings"
os.environ["KEVIN_VERIFICATION_DATABASE"] = ":memory:"
os.environ["KEVIN_VERIFICATION_MEDIA"] = str(ROOT / ".unused-documentation-media")

import django

django.setup()

from django.apps import apps
from django.db import connections
from django.urls import URLResolver, get_resolver


def model_contract(model):
    fields = []
    for field in model._meta.fields:
        relation = getattr(field, "remote_field", None)
        fields.append({
            "name": field.name, "type": field.get_internal_type(),
            "max_length": field.max_length, "null": field.null, "blank": field.blank,
            "unique": field.unique, "max_digits": getattr(field, "max_digits", None),
            "decimal_places": getattr(field, "decimal_places", None),
            "related_model": relation.model._meta.label if relation else None,
            "on_delete": relation.on_delete.__name__ if relation else None,
        })
    return {"table": model._meta.db_table, "fields": fields,
            "constraints": [str(constraint) for constraint in model._meta.constraints],
            "unique_together": model._meta.unique_together}


def api_routes(patterns, prefix=""):
    rows = []
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            rows.extend(api_routes(pattern.url_patterns, route))
        elif route.startswith("api/v1/"):
            actions = getattr(pattern.callback, "actions", {})
            view = getattr(pattern.callback, "cls", None)
            methods = sorted(actions) if actions else [
                method for method in ("get", "post", "put", "patch", "delete")
                if view and hasattr(view, method)]
            rows.append({"name": pattern.name, "pattern": route, "methods": methods,
                         "actions": actions, "view": view.__name__ if view else None})
    return rows


def serializer_contract():
    from apps.assurances import serializers as assurance
    from apps.users import serializers as users
    from apps.documents.serializers import AssuranceDocumentSerializer

    serializers = [assurance.AssuranceDraftCreateSerializer, assurance.AssuranceDetailSerializer,
                   assurance.AssuranceListSerializer, users.UserCreateUpdateSerializer,
                   users.UserSummarySerializer, AssuranceDocumentSerializer]
    return {serializer.__name__: {
        name: {"required": field.required, "read_only": field.read_only,
               "write_only": field.write_only, "max_length": getattr(field, "max_length", None),
               "min_value": str(getattr(field, "min_value", None)),
               "source": field.source}
        for name, field in serializer().fields.items()
    } for serializer in serializers}


def main():
    destination = Path(sys.argv[1])
    with connections["default"].execute_wrapper(forbid_query):
        models = {model._meta.label: model_contract(model) for model in apps.get_models()
                  if model.__module__.startswith("apps.")}
        result = {"scope": "metadata only; no database queries", "models": models,
                  "routes": api_routes(get_resolver().url_patterns), "serializers": serializer_contract()}
    destination.write_text(json.dumps(result, indent=2, default=str), encoding="utf8")
    print(f"Exported {len(models)} models and {len(result['routes'])} named route patterns.")


def forbid_query(execute, sql, params, many, context):
    raise RuntimeError("Documentation metadata export must not execute database queries.")


if __name__ == "__main__":
    main()
