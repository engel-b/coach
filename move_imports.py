from pathlib import Path

ROOT = Path("backend")

REPLACEMENTS = {
    "adapters.persistence.sqlalchemy_person_profile_repository": (
        "features.person.persistence.sqlalchemy_person_profile_repository"
    ),
    "adapters.persistence.sqlalchemy_person_profile_writer": (
        "features.person.persistence.sqlalchemy_person_profile_writer"
    ),
    "adapters.persistence.sqlalchemy_person_repository": (
        "features.person.persistence.sqlalchemy_person_repository"
    ),
    "adapters.persistence.person_model": (
        "features.person.persistence.person_model"
    ),
    "contracts.person_profile": (
        "features.person.api.contracts.person_profile"
    ),
    "contracts.person_create": (
        "features.person.api.contracts.person_create"
    ),
    "contracts.person": (
        "features.person.api.contracts.person"
    ),
    "apps.api.routers.persons": (
        "features.person.api.router"
    ),
}

for path in ROOT.rglob("*.py"):
    if ".venv" in path.parts or "__pycache__" in path.parts:
        continue

    original = path.read_text(encoding="utf-8")
    updated = original

    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(path)