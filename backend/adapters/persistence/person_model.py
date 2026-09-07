from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adapters.persistence.database import Base


class PersonModel(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    profile: Mapped["PersonProfileModel | None"] = relationship(
        back_populates="person",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PersonProfileModel(Base):
    __tablename__ = "person_profile"

    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("person.id"),
        primary_key=True,
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    training_goal: Mapped[str] = mapped_column(String(50), nullable=False)
    max_heart_rate_bpm: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    start_weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    target_weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    person: Mapped[PersonModel] = relationship(back_populates="profile")
