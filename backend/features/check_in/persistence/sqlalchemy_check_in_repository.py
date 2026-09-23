from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from features.check_in.domain.check_in import CheckIn
from features.check_in.persistence.check_in_model import CheckInModel


class SqlAlchemyCheckInRepository:
    """
    Produktive Check-in-Persistenz über SQLAlchemy.

    Der Rest der Anwendung kennt SQLAlchemy nicht.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
    ) -> None:
        self._session_factory = session_factory

    def save(
        self,
        check_in: CheckIn,
    ) -> None:
        with self._session_factory() as session:
            model = CheckInModel(
                person_id=check_in.person_id,
                timestamp=check_in.timestamp,
                energy=check_in.energy,
                recovery=check_in.recovery,
                muscle_soreness=check_in.muscle_soreness,
                stress=check_in.stress,
                available_training_minutes=(check_in.available_training_minutes),
                current_weight_kg=check_in.current_weight_kg,
                sleep_hours=check_in.sleep_hours,
                steps=check_in.steps,
                resting_heart_rate_bpm=check_in.resting_heart_rate_bpm,
            )

            session.add(model)
            session.commit()

    def get_latest_for_person(
        self,
        person_id: int,
    ) -> CheckIn | None:
        with self._session_factory() as session:
            statement = (
                select(CheckInModel)
                .where(CheckInModel.person_id == person_id)
                .order_by(CheckInModel.timestamp.desc(), CheckInModel.id.desc())
                .limit(1)
            )

            model = session.scalar(statement)

            if model is None:
                return None

            return self._to_domain(model)

    def get_history_for_person(
        self,
        person_id: int,
        limit: int,
    ) -> list[CheckIn]:
        with self._session_factory() as session:
            statement = (
                select(CheckInModel)
                .where(CheckInModel.person_id == person_id)
                .order_by(
                    CheckInModel.timestamp.desc(),
                    CheckInModel.id.desc(),
                )
                .limit(limit)
            )
            models = session.scalars(statement).all()
            return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: CheckInModel) -> CheckIn:
        return CheckIn(
            person_id=model.person_id,
            timestamp=model.timestamp,
            energy=model.energy,
            recovery=model.recovery,
            muscle_soreness=model.muscle_soreness,
            stress=model.stress,
            available_training_minutes=model.available_training_minutes,
            current_weight_kg=model.current_weight_kg,
            sleep_hours=model.sleep_hours,
            steps=model.steps,
            resting_heart_rate_bpm=model.resting_heart_rate_bpm,
        )
