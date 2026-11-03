"""Input invariants shared by API and direct draft services."""
import unicodedata

from rest_framework.exceptions import ValidationError


def normalize_name(value):
    if not isinstance(value, str):
        raise ValidationError({"policy_holder_name": "Use a name of 3-100 characters."})
    name = unicodedata.normalize("NFC", value.strip())
    if not 3 <= len(name) <= 100:
        raise ValidationError({"policy_holder_name": "Use a name of 3-100 characters."})
    # Unicode letters and their combining marks support names across scripts.
    if not any(char.isalpha() for char in name) or any(
        not (char.isalpha() or unicodedata.category(char).startswith("M") or char in " '.’-‐")
        for char in name
    ):
        raise ValidationError({"policy_holder_name": "Use letters, spaces, apostrophes, dots or hyphens."})
    return name


def validate_draft_input(data):
    cleaned = dict(data)
    if "vehicle_object" in cleaned:
        value = cleaned["vehicle_object"]
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 50:
            raise ValidationError({"vehicle_object": "Use 1-50 characters."})
        cleaned["vehicle_object"] = value.strip()
    if "policy_holder_name" in cleaned:
        cleaned["policy_holder_name"] = normalize_name(cleaned["policy_holder_name"])
    return cleaned
