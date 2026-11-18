"""Baseline Gunicorn WSGI configuration for Kevin Assurance.

Run from backend/ with explicit production environment variables injected by
the process manager (`DJANGO_SETTINGS_MODULE=core.production_settings`).
"""
import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
# Keep vault MEDIA_ROOT on a single-host local POSIX filesystem for flock safety.
workers = int(os.environ.get("GUNICORN_WORKERS", str(max(2, min(4, multiprocessing.cpu_count())))))
worker_class = "sync"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
limit_request_line = 4094
limit_request_fields = 100
accesslog = "-"
errorlog = "-"
wsgi_app = "core.wsgi:application"
