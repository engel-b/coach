from sqlalchemy import select

from adapters.persistence.check_in_model import CheckInModel
from adapters.persistence.database import create_session
from domains.check_in.check_in import CheckIn


class SqlAlchemyCheckInRepository:
    """
    Produktive Check-in-Persistenz über SQLAlchemy.

    Der Rest der Anwendung kennt SQLAlchemy nicht.
    """

    def save(
        self,
        check_in: CheckIn,
    ) -> None:
        with create_session() as session:
            model = CheckInModel(
                person_id=check_in.person_id,
                timestamp=check_in.timestamp,
                energy=check_in.energy,
                recovery=check_in.recovery,
                muscle_soreness=check_in.muscle_soreness,
                stress=check_in.stress,
                available_training_minutes=(check_in.available_training_minutes),
            )

            session.add(model)
            session.commit()

    def get_latest_for_person(
        self,
        person_id: int,
    ) -> CheckIn | None:
        with create_session() as session:
            statement = (
                select(CheckInModel)
                .where(CheckInModel.person_id == person_id)
                .order_by(CheckInModel.timestamp.desc())
                .limit(1)
            )

            model = session.scalar(statement)

            if model is None:
                return None

            return CheckIn(
                person_id=model.person_id,
                timestamp=model.timestamp,
                energy=model.energy,
                recovery=model.recovery,
                muscle_soreness=model.muscle_soreness,
                stress=model.stress,
                available_training_minutes=(model.available_training_minutes),
            )
