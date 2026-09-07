from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from adapters.persistence.database import Base


class WorkoutVideoModel(Base):
    """
    Persistente Metadaten eines Trainingsvideos.

    Die MP4-Datei wird nicht in der Datenbank gespeichert.
    """

    __tablename__ = "workout_video"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )