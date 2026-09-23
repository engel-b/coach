from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from adapters.persistence.database import Base


class CheckInModel(Base):
    """
    SQLAlchemy-Persistenzmodell.

    Wichtig:
    Das ist NICHT unser Domain-Modell CheckIn.

    Diese Klasse beschreibt lediglich die Datenbanktabelle.
    """

    __tablename__ = "check_in"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("person.id", name="fk_check_in_person", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    energy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    recovery: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    muscle_soreness: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    stress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    available_training_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    current_weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    sleep_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    steps: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    resting_heart_rate_bpm: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
