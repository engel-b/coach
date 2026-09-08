#!/usr/bin/env python3
"""One-time, preflighted Training/Workout package migration."""
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("backend")
MOVES = json.loads('{"adapters/persistence/in_memory_workout_repository.py": "features/workout/persistence/in_memory_workout_repository.py", "adapters/persistence/in_memory_workout_video_repository.py": "features/workout/persistence/in_memory_workout_video_repository.py", "adapters/persistence/sqlalchemy_workout_repository.py": "features/workout/persistence/sqlalchemy_workout_repository.py", "adapters/persistence/sqlalchemy_workout_video_repository.py": "features/workout/persistence/sqlalchemy_workout_video_repository.py", "adapters/persistence/workout_model.py": "features/workout/persistence/workout_model.py", "adapters/persistence/workout_video_model.py": "features/workout/persistence/workout_video_model.py", "application/workout/service.py": "features/workout/service/service.py", "application/workout/video_catalog_service.py": "features/workout/service/video_catalog_service.py", "apps/api/recommendation.py": "features/training/api/recommendation.py", "apps/api/routers/training.py": "features/training/api/router.py", "apps/api/routers/workout_videos.py": "features/workout/api/videos_router.py", "apps/api/routers/workouts.py": "features/workout/api/router.py", "contracts/training.py": "features/training/api/contracts/training.py", "contracts/workout.py": "features/workout/api/contracts/workout.py", "contracts/workout_mapper.py": "features/workout/api/contracts/workout_mapper.py", "contracts/workout_video.py": "features/workout/api/contracts/workout_video.py", "domains/training/heart_rate.py": "features/training/domain/heart_rate.py", "domains/training/recommendation.py": "features/training/domain/recommendation.py", "domains/training/recommendation_engine.py": "features/training/domain/recommendation_engine.py", "domains/workout/repository.py": "features/workout/domain/repository.py", "domains/workout/session.py": "features/workout/domain/session.py", "domains/workout/summary.py": "features/workout/domain/summary.py", "domains/workout/video.py": "features/workout/domain/video.py", "domains/workout/video_path.py": "features/workout/domain/video_path.py", "domains/workout/video_repository.py": "features/workout/domain/video_repository.py", "tests/adapters/persistence/test_workout_video_repository.py": "tests/features/workout/persistence/test_workout_video_repository.py", "tests/application/workout/test_workout_service.py": "tests/features/workout/service/test_workout_service.py", "tests/apps/api/test_workout_api.py": "tests/features/workout/api/test_workout_api.py", "tests/apps/api/test_workout_video_api.py": "tests/features/workout/api/test_workout_video_api.py", "tests/domains/workout/test_workout_mapper.py": "tests/features/workout/domain/test_workout_mapper.py", "tests/domains/workout/test_workout_summary.py": "tests/features/workout/domain/test_workout_summary.py", "tests/domains/workout/test_workout_video_path.py": "tests/features/workout/domain/test_workout_video_path.py"}')
IMPORTS = json.loads('{"adapters.persistence.in_memory_workout_repository": "features.workout.persistence.in_memory_workout_repository", "adapters.persistence.in_memory_workout_video_repository": "features.workout.persistence.in_memory_workout_video_repository", "adapters.persistence.sqlalchemy_workout_repository": "features.workout.persistence.sqlalchemy_workout_repository", "adapters.persistence.sqlalchemy_workout_video_repository": "features.workout.persistence.sqlalchemy_workout_video_repository", "adapters.persistence.workout_model": "features.workout.persistence.workout_model", "adapters.persistence.workout_video_model": "features.workout.persistence.workout_video_model", "application.workout.service": "features.workout.service.service", "application.workout.video_catalog_service": "features.workout.service.video_catalog_service", "apps.api.recommendation": "features.training.api.recommendation", "apps.api.routers.training": "features.training.api.router", "apps.api.routers.workout_videos": "features.workout.api.videos_router", "apps.api.routers.workouts": "features.workout.api.router", "contracts.training": "features.training.api.contracts.training", "contracts.workout": "features.workout.api.contracts.workout", "contracts.workout_mapper": "features.workout.api.contracts.workout_mapper", "contracts.workout_video": "features.workout.api.contracts.workout_video", "domains.training.heart_rate": "features.training.domain.heart_rate", "domains.training.recommendation": "features.training.domain.recommendation", "domains.training.recommendation_engine": "features.training.domain.recommendation_engine", "domains.workout.repository": "features.workout.domain.repository", "domains.workout.session": "features.workout.domain.session", "domains.workout.summary": "features.workout.domain.summary", "domains.workout.video": "features.workout.domain.video", "domains.workout.video_path": "features.workout.domain.video_path", "domains.workout.video_repository": "features.workout.domain.video_repository"}')

def module_name(path):
    return path[:-3].replace("/", ".")

def translate(name):
    for old, new in sorted(IMPORTS.items(), key=lambda x: -len(x[0])):
        if name == old or name.startswith(old + "."):
            return new + name[len(old):]
    return name

def rewrite(text, path):
    tree = ast.parse(text, filename=str(path))
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            old = node.module
            new = translate(old)
            if new != old:
                line = lines[node.lineno - 1]
                prefix = line[:node.col_offset]
                segment = line[node.col_offset:]
                if not segment.startswith("from " + old + " import"):
                    raise RuntimeError(f"Unsupported import: {path}:{node.lineno}")
                start = offsets[node.lineno - 1] + node.col_offset + 5
                edits.append((start, start + len(old), new))
        elif isinstance(node, ast.Import):
            start = offsets[node.lineno - 1] + node.col_offset
            end = offsets[node.end_lineno - 1] + node.end_col_offset
            segment = text[start:end]
            # Replace complete dotted names only, preserving aliases.
            import re
            pattern = r"(?<![\\w.])(" + "|".join(
                re.escape(x) for x in sorted(IMPORTS, key=len, reverse=True)
            ) + r")(?![\\w.])"
            updated = re.sub(pattern, lambda m: translate(m.group(0)), segment)
            if updated != segment:
                edits.append((start, end, updated))
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    ast.parse(text, filename=str(path))
    return text

def main():
    for source, target in MOVES.items():
        if not (ROOT / source).is_file() or (ROOT / target).exists():
            raise SystemExit(f"Missing source or occupied target: {source} -> {target}")
    changes = {}
    for path in ROOT.rglob("*.py"):
        if any(x in path.parts for x in (".venv", "__pycache__")):
            continue
        original = path.read_text(encoding="utf-8")
        updated = rewrite(original, path)
        if updated != original:
            changes[path] = updated
    # Validate every rewritten file before moving anything.
    for path, text in changes.items():
        ast.parse(text, filename=str(path))
    for source, target in MOVES.items():
        destination = ROOT / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", str(ROOT / source), str(destination)], check=True)
    for path, text in changes.items():
        destination = ROOT / MOVES.get(str(path.relative_to(ROOT)), str(path.relative_to(ROOT)))
        destination.write_text(text, encoding="utf-8")
    for target in MOVES.values():
        directory = (ROOT / target).parent
        while directory != ROOT:
            if directory.is_relative_to(ROOT / "features") or directory.is_relative_to(ROOT / "tests/features"):
                (directory / "__init__.py").touch(exist_ok=True)
            directory = directory.parent
    print(f"Moved {len(MOVES)} files; updated {len(changes)} import-bearing files.")
    print("Next: make format && make check")

if __name__ == "__main__":
    main()
