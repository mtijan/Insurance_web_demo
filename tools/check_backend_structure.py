"""Check file/function size and branch complexity for all backend apps/core, audit guards and verification tools."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def complexity(function):
    count = 1
    for node in ast.walk(function):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While,
                             ast.ExceptHandler, ast.IfExp, ast.Assert)):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            count += 1 + len(node.ifs)
    return count


def inspect_file(path):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    length = len(source.splitlines())
    problems = [f"{path.name}: {length} lines > 300"] if length > 300 else []
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for function in functions:
        size = function.end_lineno - function.lineno + 1
        branches = complexity(function)
        if size > 40 or branches > 10:
            problems.append(f"{path.relative_to(ROOT)}:{function.lineno} "
                            f"{function.name}: lines={size}, complexity={branches}")
    longest = max((node.end_lineno - node.lineno + 1 for node in functions), default=0)
    branches = max((complexity(node) for node in functions), default=0)
    return length, longest, problems, len(functions), branches


def report_metrics(results, file_count):
    print(f"Inspected {file_count} Python files across all backend apps/core, quality_review and tools.")
    print(f"Maximum file length: {max(result[0] for result in results)} lines.")
    print(f"Maximum function length: {max(result[1] for result in results)} lines.")
    print(f"Total functions: {sum(result[3] for result in results)}.")
    print(f"Maximum branch complexity: {max(result[4] for result in results)}.")
    print("Branch complexity limit: 10 (AST estimate, including boolean branches).")


def main():
    files = set((BACKEND / "apps").rglob("*.py"))
    files.add(BACKEND / "manage.py")
    files.update((BACKEND / "core").rglob("*.py"))
    files.update((BACKEND / "quality_review").rglob("*.py"))
    files.update((ROOT / "tools").glob("*.py"))
    results = [inspect_file(path) for path in sorted(files)]
    problems = [problem for result in results for problem in result[2]]
    report_metrics(results, len(files))
    pricing = BACKEND / "apps/assurances/services/pricing_calculator.py"
    print(f"Pricing calculator length: {len(pricing.read_text().splitlines())} lines (limit 100).")
    if len(pricing.read_text().splitlines()) > 100:
        problems.append("pricing_calculator.py exceeds 100 lines")
    for problem in problems:
        print(problem)
    print("PASS" if not problems else "FAIL")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
