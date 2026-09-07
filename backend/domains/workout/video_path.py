from pathlib import PurePosixPath


class InvalidWorkoutVideoPathError(ValueError):
    """Der Dateipfad eines Trainingsvideos ist ungültig."""


def validate_workout_video_path(file_path: str) -> str:
    """
    Validiert einen relativen MP4-Pfad im Videoverzeichnis.

    Erlaubt:
        cycling/alpen.mp4

    Nicht erlaubt:
        ../secret.mp4
        /etc/passwd
        https://example.com/video.mp4
        cycling\\alpen.mp4
    """

    if not file_path or file_path != file_path.strip():
        raise InvalidWorkoutVideoPathError(
            "Video path must not be empty or contain surrounding whitespace"
        )

    if "\\" in file_path:
        raise InvalidWorkoutVideoPathError(
            "Video path must use forward slashes"
        )

    path = PurePosixPath(file_path)

    if path.is_absolute():
        raise InvalidWorkoutVideoPathError(
            "Video path must be relative"
        )

    if any(part in {"", ".", ".."} for part in file_path.split("/")):
        raise InvalidWorkoutVideoPathError(
            "Video path must not contain empty or traversal segments"
        )

    if ":" in file_path or "?" in file_path or "#" in file_path:
        raise InvalidWorkoutVideoPathError(
            "Video path contains unsupported characters"
        )

    if path.suffix.lower() != ".mp4":
        raise InvalidWorkoutVideoPathError(
            "Video path must point to an MP4 file"
        )

    return file_path