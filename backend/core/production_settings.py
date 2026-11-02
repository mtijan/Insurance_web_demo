"""Production configuration; environment values are required, never inferred."""
import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403


def required(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"Required production environment variable: {name}")
    return value


SECRET_KEY = required("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = required("DJANGO_ALLOWED_HOSTS").split(",")
if "*" in ALLOWED_HOSTS or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("Use explicit allowed hosts and a strong production secret.")
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql", "NAME": required("POSTGRES_DB"),
    "USER": required("POSTGRES_USER"), "PASSWORD": required("POSTGRES_PASSWORD"),
    "HOST": required("POSTGRES_HOST"), "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "OPTIONS": {"sslmode": os.environ.get("POSTGRES_SSLMODE", "verify-full")},
}}
MEDIA_ROOT = required("KEVIN_MEDIA_ROOT")
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
AUTH_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
CORS_ALLOWED_ORIGINS = required("DJANGO_TRUSTED_ORIGINS").split(",")
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
if any(not origin.startswith("https://") for origin in CORS_ALLOWED_ORIGINS):
    raise ImproperlyConfigured("Production trusted origins must use HTTPS.")
if os.environ.get("DJANGO_TRUST_PROXY") == "1":
    # Enable only behind an isolated proxy that replaces incoming forwarded headers.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
