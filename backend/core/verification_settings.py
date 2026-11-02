"""Isolated SQLite and media paths, supplied by the verification runner only."""
import os

from .settings import *  # noqa: F403

DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.environ["KEVIN_VERIFICATION_DATABASE"],
}}
MEDIA_ROOT = os.environ["KEVIN_VERIFICATION_MEDIA"]
