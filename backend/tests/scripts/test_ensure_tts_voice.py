from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import ensure_tts_voice as voices


@pytest.fixture
def model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "de_DE-thorsten-medium.onnx"

    class FakeVoice:
        @staticmethod
        def load(path: Path, **_kwargs: object) -> object:
            if path.read_bytes() != b"valid voice":
                raise ValueError("INVALID_PROTOBUF")
            return object()

    monkeypatch.setattr(
        voices, "import_module", lambda _name: SimpleNamespace(PiperVoice=FakeVoice)
    )
    return path


def write_voice(path: Path, content: bytes) -> None:
    path.write_bytes(content)
    Path(f"{path}.json").write_text("{}", encoding="utf-8")


def test_loadable_voice_does_not_download(model: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_voice(model, b"valid voice")

    def unexpected_download(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("existing valid voice should not be downloaded")

    monkeypatch.setattr(voices.subprocess, "run", unexpected_download)
    voices.ensure_tts_voice(model)


def test_corrupt_voice_is_backed_up_and_replaced_only_after_validation(
    model: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_voice(model, b"broken")

    def download(args: list[str], **_kwargs: object) -> None:
        directory = Path(args[args.index("--data-dir") + 1])
        write_voice(directory / "de_DE-thorsten-medium.onnx", b"valid voice")

    monkeypatch.setattr(voices.subprocess, "run", download)
    voices.ensure_tts_voice(model)

    assert model.read_bytes() == b"valid voice"
    assert [p.read_bytes() for p in model.parent.glob(f"{model.name}.bak.*")] == [b"broken"]


def test_failed_download_keeps_original_voice(model: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_voice(model, b"broken")

    def download(args: list[str], **_kwargs: object) -> None:
        directory = Path(args[args.index("--data-dir") + 1])
        write_voice(directory / "de_DE-thorsten-medium.onnx", b"still broken")

    monkeypatch.setattr(voices.subprocess, "run", download)
    with pytest.raises(ValueError, match="INVALID_PROTOBUF"):
        voices.ensure_tts_voice(model)

    assert model.read_bytes() == b"broken"
    assert not list(model.parent.glob(f"{model.name}.bak.*"))


def test_missing_config_is_restored_after_validated_download(
    model: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model.write_bytes(b"valid voice")

    def download(args: list[str], **_kwargs: object) -> None:
        directory = Path(args[args.index("--data-dir") + 1])
        write_voice(directory / "de_DE-thorsten-medium.onnx", b"valid voice")

    monkeypatch.setattr(voices.subprocess, "run", download)
    voices.ensure_tts_voice(model)

    assert Path(f"{model}.json").is_file()
