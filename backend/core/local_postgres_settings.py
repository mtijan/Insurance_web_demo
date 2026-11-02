"""Opt-in PostgreSQL development settings; never load production credentials."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env.postgres.local", override=False)

from .settings import *  # noqa: E402,F403


def required_local(name):
    value = os.environ.get(name)
    if not value or not value.strip():
        raise ImproperlyConfigured(f"Required local environment variable: {name}")
    return value


_host = required_local("POSTGRES_HOST")
_database = required_local("POSTGRES_DB")
_user = required_local("POSTGRES_USER")
if (_host not in {"127.0.0.1", "localhost", "::1"}
        or _database != "kevin_assurance_local" or _user != "kevin_assurance_local"):
    raise ImproperlyConfigured("Local PostgreSQL requires loopback and the dedicated project database/role.")

SECRET_KEY = required_local("DJANGO_SECRET_KEY")
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": _database,
    "USER": _user,
    "PASSWORD": required_local("POSTGRES_PASSWORD"),
    "HOST": _host,
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "OPTIONS": {"sslmode": os.environ.get("POSTGRES_SSLMODE", "prefer"), "connect_timeout": 5},
    "TEST": {"NAME": "test_kevin_assurance_local"},
}}
