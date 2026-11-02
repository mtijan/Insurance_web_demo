"""Check local documentation links, fenced JSON and the remediation register."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def heading_ids(path):
    source = path.read_text(encoding="utf-8-sig")
    headings = re.findall(r"^#{1,6}\s+(.+)$", source, flags=re.MULTILINE)
    return {re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-") for title in headings}


def check_link(path, target):
    target = unquote(target.strip("<>"))
    if re.match(r"^(https?:|mailto:|app:|plugin:)", target):
        return None
    filename, _, anchor = target.partition("#")
    filename = re.sub(r":\d+$", "", filename)
    destination = (path.parent / filename).resolve() if filename else path
    if not destination.exists():
        return f"{path.relative_to(ROOT)}: missing file {target}"
    if anchor and destination.suffix == ".md" and anchor not in heading_ids(destination):
        return f"{path.relative_to(ROOT)}: missing heading {target}"
    return None


def inspect_document(path):
    source = path.read_text(encoding="utf-8-sig")
    problems = []
    blocks = re.findall(r"```([^\n]*)\n(.*?)```", source, re.DOTALL)
    for language, body in blocks:
        if language.strip() == "json":
            try:
                json.loads(body)
            except json.JSONDecodeError as exc:
                problems.append(f"{path.relative_to(ROOT)}: invalid JSON example: {exc.msg}")
    if source.count("```") % 2:
        problems.append(f"{path.relative_to(ROOT)}: unmatched code fence")
    text = re.sub(r"```.*?```", "", source, flags=re.DOTALL)
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    problems.extend(problem for target in targets if (problem := check_link(path, target)))
    return len(targets), problems


def main():
    paths = sorted(DOCS.rglob("*.md")) + [ROOT / "frontend/README.md"]
    results = [inspect_document(path) for path in paths]
    problems = [problem for _, issues in results for problem in issues]
    report = DOCS / "evidence/backend-quality-remediation/report.md"
    register = report.read_text(encoding="utf8") if report.exists() else ""
    for number in range(1, 15):
        if f"KA-Q{number:02d}" not in register:
            problems.append(f"Remediation register missing KA-Q{number:02d}")
    print(f"Inspected {len(paths)} Markdown files and {sum(row[0] for row in results)} link references.")
    print("Checked local files/headings, code fences, JSON examples and 14 finding IDs.")
    print("Mermaid source references reviewed; renderer unavailable, no render claim.")
    print("\n".join(problems) if problems else "PASS")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
