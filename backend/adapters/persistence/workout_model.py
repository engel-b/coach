from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adapters.persistence.database import Base


class WorkoutModel(Base):
    __tablename__ = "workout"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    person_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    total_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    elapsed_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    distance_m: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    phases: Mapped[list["WorkoutPhaseModel"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutPhaseModel.position",
    )


class WorkoutPhaseModel(Base):
    __tablename__ = "workout_phase"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    workout_id: Mapped[str] = mapped_column(
        ForeignKey("workout.id"),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    phase_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_heart_rate_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_heart_rate_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    workout: Mapped[WorkoutModel] = relationship(
        back_populates="phases",
    )
