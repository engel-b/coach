from pathlib import Path

ROOT = Path("backend")

REPLACEMENTS = {
    "domains.person.person_profile_writer": (
        "features.person.domain.person_profile_writer"
    ),
    "domains.person.person_repository": (
        "features.person.domain.person_repository"
    ),
    "domains.person.profile_repository": (
        "features.person.domain.profile_repository"
    ),
    "domains.person.profile_validation": (
        "features.person.domain.profile_validation"
    ),
    "domains.person.profile": (
        "features.person.domain.profile"
    ),
    "domains.person.person": (
        "features.person.domain.person"
    ),
    "application.person.management_service": (
        "features.person.application.management_service"
    ),
    "application.person.person_service": (
        "features.person.application.person_service"
    ),
    "application.person.profile_service": (
        "features.person.application.profile_service"
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