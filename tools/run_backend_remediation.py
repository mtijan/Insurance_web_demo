"""Collect isolated, non-destructive remediation evidence with real exit codes."""
import argparse
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
EVIDENCE = ROOT / "docs/evidence/backend-quality-remediation"


def execute(command, environment, output):
    started = perf_counter()
    result = subprocess.run([sys.executable, *command], cwd=BACKEND, env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf8", errors="replace")
    elapsed = perf_counter() - started
    label = "python " + " ".join(command)
    output.write_text(f"Command: {label}\n{result.stdout}\nExit: {result.returncode}; Wall duration: {elapsed:.3f}s\n", encoding="utf8")
    print(f"{output.name}: exit={result.returncode}, wall={elapsed:.3f}s", flush=True)
    return {"command": label, "exit": result.returncode, "wall_seconds": round(elapsed, 3)}


def production_environment(environment, directory):
    return {**environment, "DJANGO_SETTINGS_MODULE": "core.production_settings",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_ALLOWED_HOSTS": "verification.example.test",
            "DJANGO_TRUSTED_ORIGINS": "https://verification.example.test",
            "POSTGRES_DB": "verification_only", "POSTGRES_USER": "verification_only",
            "POSTGRES_PASSWORD": secrets.token_urlsafe(32), "POSTGRES_HOST": "127.0.0.1",
            "KEVIN_MEDIA_ROOT": str(Path(directory) / "media")}


def commands(test_labels):
    if test_labels:
        return [("tests.log", ["manage.py", "test", *test_labels, "--verbosity", "2"])]
    return [
        ("django-check.log", ["manage.py", "check"]),
        ("migration-check.log", ["manage.py", "makemigrations", "--check", "--dry-run"]),
        ("migrate.log", ["manage.py", "migrate", "--noinput"]),
        ("seed-first.log", ["manage.py", "seed_initial_users"]),
        ("seed-repeat.log", ["manage.py", "seed_initial_users"]),
        ("regression.log", ["manage.py", "test", "apps", "--verbosity", "2"]),
        ("audit-probes.log", ["manage.py", "test", "quality_review", "--verbosity", "2"]),
        ("all-tests.log", ["manage.py", "test", "apps", "quality_review", "--verbosity", "1"]),
        ("structure.log", [str(ROOT / "tools/check_backend_structure.py")]),
    ]


def main():
    started_at = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="final")
    parser.add_argument("--tests", nargs="*")
    options = parser.parse_args()
    output = EVIDENCE / options.phase
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with TemporaryDirectory(prefix=".verification-fixes-", dir=BACKEND) as directory:
        environment = {**os.environ, "DJANGO_SETTINGS_MODULE": "core.verification_settings",
                       "KEVIN_VERIFICATION_DATABASE": str(Path(directory) / "isolated.sqlite3"),
                       "KEVIN_VERIFICATION_MEDIA": str(Path(directory) / "media"),
                       "PYTHONIOENCODING": "utf8", "PYTHONUNBUFFERED": "1"}
        for filename, command in commands(options.tests):
            results.append(execute(command, environment, output / filename))
        if not options.tests:
            results.append(execute(["manage.py", "check", "--deploy", "--fail-level", "WARNING"],
                                   production_environment(environment, directory), output / "deployment-check.log"))
    summary = {"started_at": started_at,
               "completed_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
               "python": sys.version.split()[0], "database": "isolated SQLite",
               "temporary_resources_removed": True, "results": results}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
    return int(any(result["exit"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
