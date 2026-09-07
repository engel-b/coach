import pytest

from domains.workout.video_path import (
    InvalidWorkoutVideoPathError,
    validate_workout_video_path,
)


@pytest.mark.parametrize(
    "file_path",
    [
        "cycling/alpen.mp4",
        "alpen.mp4",
        "cycling/2026/alpen.MP4",
    ],
)
def test_valid_video_paths_are_accepted(file_path: str) -> None:
    assert validate_workout_video_path(file_path) == file_path


@pytest.mark.parametrize(
    "file_path",
    [
        "",
        " ",
        " cycling/alpen.mp4",
        "cycling/alpen.mp4 ",
        "../secret.mp4",
        "cycling/../secret.mp4",
        "/etc/passwd",
        "//server/share/video.mp4",
        "C:/videos/alpen.mp4",
        r"cycling\alpen.mp4",
        "https://example.com/video.mp4",
        "cycling//alpen.mp4",
        "cycling/./alpen.mp4",
        "cycling/alpen.mp4?download=1",
        "cycling/alpen.mp4#fragment",
        "cycling/alpen.avi",
    ],
)
def test_invalid_video_paths_are_rejected(file_path: str) -> None:
    with pytest.raises(InvalidWorkoutVideoPathError):
        validate_workout_video_path(file_path)