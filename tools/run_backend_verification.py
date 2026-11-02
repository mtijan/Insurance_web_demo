"""Run reproducible local checks with isolated seed database and media storage."""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
EVIDENCE = ROOT / "docs" / "evidence" / "p0-be-05-p1-be-06"


def run_command(arguments, environment, log):
    command = [sys.executable, *arguments]
    label = "python " + " ".join(arguments)
    started = perf_counter()
    result = subprocess.run(command, cwd=BACKEND, env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    elapsed = perf_counter() - started
    output = f"\nCommand: {label}\n{result.stdout}\nExit: {result.returncode}; Wall duration: {elapsed:.3f}s\n"
    print(output, flush=True)
    log.write(output)
    log.flush()
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".verification-", dir=BACKEND) as directory:
        environment = os.environ.copy()
        environment.update({
            "DJANGO_SETTINGS_MODULE": "core.verification_settings",
            "KEVIN_VERIFICATION_DATABASE": str(Path(directory) / "seed.sqlite3"),
            "KEVIN_VERIFICATION_MEDIA": str(Path(directory) / "media"),
            "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
        })
        commands = [
            ["manage.py", "check"], ["manage.py", "makemigrations", "--check", "--dry-run"],
            ["manage.py", "migrate", "--noinput"],
            ["manage.py", "seed_initial_users"], ["manage.py", "seed_initial_users"],
            ["manage.py", "test", "apps", "--verbosity", "2"],
            [str(ROOT / "tools" / "check_backend_structure.py")],
        ]
        with (EVIDENCE / "backend-verification.log").open("w", encoding="utf-8") as log:
            log.write(f"Started: {datetime.now(ZoneInfo('Asia/Jakarta')).isoformat()}\n")
            log.write("Settings: core.verification_settings; isolated SQLite and media.\n")
            log.write("Seed command runs only against disposable synthetic data.\n")
            log.write(f"Python: {sys.version.split()[0]}\n")
            for command in commands:
                run_command(command, environment, log)
    print("Isolated verification database and media cleaned up.", flush=True)


if __name__ == "__main__":
    main()
