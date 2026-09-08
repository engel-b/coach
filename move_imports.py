#!/usr/bin/env python3
"""Move the remaining device/telemetry code without changing behavior."""
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("backend")
MOVES = json.loads('{"adapters/bluetooth/discovery.py": "features/telemetry/adapters/bluetooth/discovery.py", "adapters/bluetooth/ftms/adapter.py": "features/telemetry/adapters/bluetooth/ftms/adapter.py", "adapters/bluetooth/ftms/constants.py": "features/telemetry/adapters/bluetooth/ftms/constants.py", "adapters/bluetooth/ftms/parser.py": "features/telemetry/adapters/bluetooth/ftms/parser.py", "adapters/bluetooth/heart_rate/adapter.py": "features/telemetry/adapters/bluetooth/heart_rate/adapter.py", "adapters/bluetooth/heart_rate/constants.py": "features/telemetry/adapters/bluetooth/heart_rate/constants.py", "adapters/bluetooth/heart_rate/parser.py": "features/telemetry/adapters/bluetooth/heart_rate/parser.py", "adapters/websocket/backend_client.py": "features/telemetry/adapters/websocket/backend_client.py", "application/telemetry/broadcaster.py": "features/telemetry/service/broadcaster.py", "application/telemetry/models.py": "features/telemetry/service/models.py", "application/telemetry/service.py": "features/telemetry/service/service.py", "apps/api/routers/devices.py": "features/telemetry/api/devices_router.py", "apps/api/routers/telemetry.py": "features/telemetry/api/router.py", "contracts/device.py": "features/telemetry/api/contracts/device.py", "contracts/telemetry.py": "features/telemetry/api/contracts/telemetry.py", "domains/health/device.py": "features/telemetry/domain/health/device.py", "domains/health/device_events.py": "features/telemetry/domain/health/device_events.py", "domains/health/heart_rate.py": "features/telemetry/domain/health/heart_rate.py", "domains/health/heart_rate_source.py": "features/telemetry/domain/health/heart_rate_source.py", "domains/telemetry/bike.py": "features/telemetry/domain/telemetry/bike.py", "domains/telemetry/bike_source.py": "features/telemetry/domain/telemetry/bike_source.py", "tests/adapters/bluetooth/ftms/test_bike_adapter.py": "tests/features/telemetry/adapters/bluetooth/ftms/test_bike_adapter.py", "tests/adapters/bluetooth/ftms/test_indoor_bike_parser.py": "tests/features/telemetry/adapters/bluetooth/ftms/test_indoor_bike_parser.py", "tests/adapters/bluetooth/heart_rate/test_device.py": "tests/features/telemetry/adapters/bluetooth/heart_rate/test_device.py", "tests/adapters/bluetooth/heart_rate/test_heart_rate.py": "tests/features/telemetry/adapters/bluetooth/heart_rate/test_heart_rate.py", "tests/adapters/bluetooth/heart_rate/test_heart_rate_parser.py": "tests/features/telemetry/adapters/bluetooth/heart_rate/test_heart_rate_parser.py", "tests/adapters/bluetooth/test_discovery.py": "tests/features/telemetry/adapters/bluetooth/test_discovery.py", "tests/application/telemetry/test_telemetry_service.py": "tests/features/telemetry/service/test_telemetry_service.py", "tests/domains/telemetry/test_bike_telemetry.py": "tests/features/telemetry/domain/test_bike_telemetry.py"}')
IMPORTS = json.loads('{"adapters.bluetooth": "features.telemetry.adapters.bluetooth", "adapters.bluetooth.discovery": "features.telemetry.adapters.bluetooth.discovery", "adapters.bluetooth.ftms.adapter": "features.telemetry.adapters.bluetooth.ftms.adapter", "adapters.bluetooth.ftms.constants": "features.telemetry.adapters.bluetooth.ftms.constants", "adapters.bluetooth.ftms.parser": "features.telemetry.adapters.bluetooth.ftms.parser", "adapters.bluetooth.heart_rate.adapter": "features.telemetry.adapters.bluetooth.heart_rate.adapter", "adapters.bluetooth.heart_rate.constants": "features.telemetry.adapters.bluetooth.heart_rate.constants", "adapters.bluetooth.heart_rate.parser": "features.telemetry.adapters.bluetooth.heart_rate.parser", "adapters.websocket": "features.telemetry.adapters.websocket", "adapters.websocket.backend_client": "features.telemetry.adapters.websocket.backend_client", "application.telemetry": "features.telemetry.service", "application.telemetry.broadcaster": "features.telemetry.service.broadcaster", "application.telemetry.models": "features.telemetry.service.models", "application.telemetry.service": "features.telemetry.service.service", "apps.api.routers.devices": "features.telemetry.api.devices_router", "apps.api.routers.telemetry": "features.telemetry.api.router", "contracts.device": "features.telemetry.api.contracts.device", "contracts.telemetry": "features.telemetry.api.contracts.telemetry", "domains.health": "features.telemetry.domain.health", "domains.health.device": "features.telemetry.domain.health.device", "domains.health.device_events": "features.telemetry.domain.health.device_events", "domains.health.heart_rate": "features.telemetry.domain.health.heart_rate", "domains.health.heart_rate_source": "features.telemetry.domain.health.heart_rate_source", "domains.telemetry": "features.telemetry.domain.telemetry", "domains.telemetry.bike": "features.telemetry.domain.telemetry.bike", "domains.telemetry.bike_source": "features.telemetry.domain.telemetry.bike_source"}')

def translate(name):
    for old, new in sorted(IMPORTS.items(), key=lambda item: -len(item[0])):
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
                segment = lines[node.lineno - 1][node.col_offset:]
                if not segment.startswith("from " + old + " import"):
                    raise RuntimeError(f"Unsupported import: {path}:{node.lineno}")
                start = offsets[node.lineno - 1] + node.col_offset + 5
                edits.append((start, start + len(old), new))
        elif isinstance(node, ast.Import):
            start = offsets[node.lineno - 1] + node.col_offset
            end = offsets[node.end_lineno - 1] + node.end_col_offset
            segment = text[start:end]
            pattern = r"(?<![\w.])(" + "|".join(
                re.escape(x) for x in sorted(IMPORTS, key=len, reverse=True)
            ) + r")(?![\w.])"
            updated = re.sub(pattern, lambda m: translate(m.group(0)), segment)
            if updated != segment:
                edits.append((start, end, updated))
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    ast.parse(text, filename=str(path))
    return text

def main():
    if not ROOT.is_dir():
        raise SystemExit("Run from the repository root.")
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
    for source, target in MOVES.items():
        destination = ROOT / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", str(ROOT / source), str(destination)], check=True)
    for path, text in changes.items():
        relative = str(path.relative_to(ROOT))
        destination = ROOT / MOVES.get(relative, relative)
        destination.write_text(text, encoding="utf-8")
    for target in MOVES.values():
        directory = (ROOT / target).parent
        while directory != ROOT:
            if directory.is_relative_to(ROOT / "features") or directory.is_relative_to(ROOT / "tests/features"):
                (directory / "__init__.py").touch(exist_ok=True)
            directory = directory.parent
    print(f"Moved {len(MOVES)} files; updated {len(changes)} files.")
    print("Run: make format && make check")

if __name__ == "__main__":
    main()
