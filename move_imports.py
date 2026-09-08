from pathlib import Path
import ast
import subprocess

ROOT = Path("backend")

MOVES = {
    "domains/check_in/check_in.py":
        "features/check_in/domain/check_in.py",
    "domains/check_in/repository.py":
        "features/check_in/domain/repository.py",
    "application/check_in/service.py":
        "features/check_in/service/service.py",
    "contracts/check_in.py":
        "features/check_in/api/contracts/check_in.py",
    "apps/api/routers/check_ins.py":
        "features/check_in/api/router.py",
    "adapters/persistence/check_in_model.py":
        "features/check_in/persistence/check_in_model.py",
    "adapters/persistence/in_memory_check_in_repository.py":
        "features/check_in/persistence/in_memory_check_in_repository.py",
    "adapters/persistence/sqlalchemy_check_in_repository.py":
        "features/check_in/persistence/sqlalchemy_check_in_repository.py",
    "tests/application/check_in/test_check_in_service.py":
        "tests/features/check_in/service/test_check_in_service.py",
}

IMPORTS = {
    "domains.check_in.check_in":
        "features.check_in.domain.check_in",
    "domains.check_in.repository":
        "features.check_in.domain.repository",
    "application.check_in.service":
        "features.check_in.service.service",
    "contracts.check_in":
        "features.check_in.api.contracts.check_in",
    "apps.api.routers.check_ins":
        "features.check_in.api.router",
    "adapters.persistence.check_in_model":
        "features.check_in.persistence.check_in_model",
    "adapters.persistence.in_memory_check_in_repository":
        "features.check_in.persistence.in_memory_check_in_repository",
    "adapters.persistence.sqlalchemy_check_in_repository":
        "features.check_in.persistence.sqlalchemy_check_in_repository",
}


def git_mv(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "mv", str(source), str(target)],
        check=True,
    )


def replace_module(name: str) -> str:
    """Ersetzt einen vollständigen Modulpfad oder dessen Untermodul."""
    for old, new in sorted(
        IMPORTS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if name == old:
            return new
        if name.startswith(old + "."):
            return new + name[len(old):]
    return name


def rewrite_imports(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    tree = ast.parse(original, filename=str(path))

    replacements: list[tuple[int, int, str]] = []
    lines = original.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module is None:
                continue

            old = node.module
            new = replace_module(old)
            if new == old:
                continue

            line_index = node.lineno - 1
            line = lines[line_index]
            prefix = "from "
            start = line.find(prefix) + len(prefix)
            end = line.find(" import ", start)

            if start < len(prefix) or end < 0:
                raise RuntimeError(f"Import nicht eindeutig: {path}:{node.lineno}")

            replacements.append(
                (node.lineno, start, new)
            )

        elif isinstance(node, ast.Import):
            # In diesem Projekt werden die betroffenen Module über
            # 'from ... import ...' eingebunden. Andere Importformen
            # werden nicht automatisch verändert.
            continue

    for line_number, start, new in sorted(replacements, reverse=True):
        index = line_number - 1
        line = lines[index]
        end = line.find(" import ", start)
        lines[index] = line[:start] + new + line[end:]

    updated = "".join(lines)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"Importe aktualisiert: {path}")


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit("Bitte im Projektroot ausführen.")

    # Vor dem ersten git mv alle Pfade prüfen.
    for source_name, target_name in MOVES.items():
        source = ROOT / source_name
        target = ROOT / target_name

        if not source.is_file():
            raise SystemExit(f"Quelldatei fehlt: {source}")
        if target.exists():
            raise SystemExit(f"Ziel existiert bereits: {target}")

    for source_name, target_name in MOVES.items():
        git_mv(ROOT / source_name, ROOT / target_name)

    packages = [
        "features/check_in",
        "features/check_in/domain",
        "features/check_in/service",
        "features/check_in/api",
        "features/check_in/api/contracts",
        "features/check_in/persistence",
        "tests/features/check_in",
        "tests/features/check_in/service",
    ]

    for package in packages:
        directory = ROOT / package
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").touch(exist_ok=True)

    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        rewrite_imports(path)

    print("Check-in-Umzug abgeschlossen. Bitte make check ausführen.")


if __name__ == "__main__":
    main()