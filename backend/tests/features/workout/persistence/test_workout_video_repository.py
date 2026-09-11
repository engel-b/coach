from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.sqlalchemy_workout_video_repository import (
    SqlAlchemyWorkoutVideoRepository,
)
from features.workout.persistence.workout_video_model import WorkoutVideoModel


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    """
    Erstellt für jeden Test eine vollständig isolierte SQLite-In-Memory-DB.

    StaticPool ist hier wichtig:
    SQLite-In-Memory-Datenbanken existieren normalerweise pro Connection.
    Da das Repository für save() und get() jeweils neue Sessions öffnet,
    müssen diese Sessions dieselbe Connection bzw. dieselbe In-Memory-DB
    verwenden.

    Java-Vergleich:
    Das entspricht ungefähr einer eigenen H2-In-Memory-Datenbank
    pro Testklasse/Test-Fixture.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Stellt sicher, dass das Model in Base.metadata registriert ist.
    assert WorkoutVideoModel.__tablename__ == "workout_video"

def test_unknown_workout_video_returns_none(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyWorkoutVideoRepository(
        session_factory=session_factory,
    )

    assert repository.get("does-not-exist") is None


def test_workout_video_can_be_saved_and_loaded(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyWorkoutVideoRepository(
        session_factory=session_factory,
    )

    video = WorkoutVideo(
        id="test-video",
        title="Testvideo",
        description="Nur für den Repository-Test",
        file_path="cycling/test.mp4",
        duration_seconds=123.5,
        active=True,
        created_at=datetime.now(UTC),
    )

    repository.save(video)

    loaded = repository.get("test-video")

    assert loaded is not None
    assert loaded.id == "test-video"
    assert loaded.title == "Testvideo"
    assert loaded.description == "Nur für den Repository-Test"
    assert loaded.file_path == "cycling/test.mp4"
    assert loaded.duration_seconds == 123.5
    assert loaded.active is True


def test_workout_video_can_be_updated(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyWorkoutVideoRepository(
        session_factory=session_factory,
    )
    created_at = datetime.now(UTC)

    repository.save(
        WorkoutVideo(
            id="test-video",
            title="Alter Titel",
            description="Alte Beschreibung",
            file_path="cycling/old.mp4",
            duration_seconds=100.0,
            active=True,
            created_at=created_at,
        )
    )
    repository.save(
        WorkoutVideo(
            id="test-video",
            title="Neuer Titel",
            description="Neue Beschreibung",
            file_path="cycling/new.mp4",
            duration_seconds=200.0,
            active=False,
            created_at=created_at,
        )
    )

    loaded = repository.get("test-video")

    assert loaded is not None
    assert loaded.title == "Neuer Titel"
    assert loaded.description == "Neue Beschreibung"
    assert loaded.file_path == "cycling/new.mp4"
    assert loaded.duration_seconds == 200.0
    assert loaded.active is False
