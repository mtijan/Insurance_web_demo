"""Record regression results and independent audit probes without changing app data."""
import ast
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zoneinfo import ZoneInfo

from check_backend_structure import complexity

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
EVIDENCE = ROOT / "docs" / "evidence" / "backend-quality-review"


def record_command(arguments, environment, filename):
    started = perf_counter()
    result = subprocess.run([sys.executable, "manage.py", *arguments], cwd=BACKEND,
                            env=environment, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace")
    report = f"Command: python manage.py {' '.join(arguments)}\n{result.stdout}"
    report += f"\nExit: {result.returncode}; Wall duration: {perf_counter() - started:.3f}s\n"
    (EVIDENCE / filename).write_text(report, encoding="utf-8")
    print(report, flush=True)
    return result.returncode


def record_structure():
    paths = sorted((BACKEND / "apps").rglob("*.py")) + sorted((BACKEND / "core").glob("*.py"))
    functions, maximum, violations, branch_violations = [], 0, [], []
    for path in paths:
        source = path.read_text(encoding="utf-8-sig")
        maximum = max(maximum, len(source.splitlines()))
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = node.end_lineno - node.lineno + 1
                functions.append(length)
                if length > 40:
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno} {node.name}: {length} lines")
                branches = complexity(node)
                if branches > 10:
                    branch_violations.append(
                        f"{path.relative_to(ROOT)}:{node.lineno} {node.name}: {branches}",
                    )
    report = f"Audited {len(paths)} backend Python files, {len(functions)} functions.\n"
    report += f"Maximum file: {maximum} lines; maximum function: {max(functions)} lines.\n"
    report += "Function limit violations:\n" + "\n".join(violations) + "\n"
    report += "Branch complexity > 10 (AST estimate):\n" + "\n".join(branch_violations) + "\n"
    (EVIDENCE / "structure.log").write_text(report, encoding="utf-8")
    print(report, flush=True)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".verification-review-", dir=BACKEND) as directory:
        environment = os.environ.copy()
        environment.update({
            "DJANGO_SETTINGS_MODULE": "core.verification_settings",
            "KEVIN_VERIFICATION_DATABASE": str(Path(directory) / "review.sqlite3"),
            "KEVIN_VERIFICATION_MEDIA": str(Path(directory) / "media"),
            "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
        })
        (EVIDENCE / "environment.log").write_text(
            f"Started: {datetime.now(ZoneInfo('Asia/Jakarta')).isoformat()}\n"
            f"Python: {sys.version.split()[0]}; isolated SQLite and media.\n"
            "No production code or existing local data modified. Audit probes assert desired behavior.\n",
            encoding="utf-8",
        )
        commands = [
            (["check"], "django-check.log"),
            (["makemigrations", "--check", "--dry-run"], "migration-check.log"),
            (["test", "apps", "--verbosity", "1"], "regression.log"),
            (["test", "quality_review", "--verbosity", "2"], "audit-probes.log"),
            (["check", "--deploy"], "deployment-check.log"),
        ]
        for arguments, filename in commands:
            record_command(arguments, environment, filename)
        record_structure()
    print("Review complete; temporary database/media removed. Read findings before interpreting test status.")


if __name__ == "__main__":
    main()
