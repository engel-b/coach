from adapters.persistence.sqlalchemy_check_in_repository import (
    SqlAlchemyCheckInRepository,
)
from adapters.persistence.sqlalchemy_person_profile_repository import (
    SqlAlchemyPersonProfileRepository,
)
from adapters.persistence.sqlalchemy_person_profile_writer import (
    SqlAlchemyPersonProfileWriter,
)
from adapters.persistence.sqlalchemy_person_repository import (
    SqlAlchemyPersonRepository,
)
from adapters.persistence.sqlalchemy_workout_repository import (
    SqlAlchemyWorkoutRepository,
)
from adapters.persistence.sqlalchemy_workout_video_repository import (
    SqlAlchemyWorkoutVideoRepository,
)
from application.check_in.service import CheckInService
from application.person.management_service import PersonManagementService
from application.person.person_service import PersonService
from application.person.profile_service import PersonProfileService
from application.telemetry.broadcaster import TelemetryBroadcaster
from application.telemetry.service import TelemetryService
from application.workout.service import WorkoutService
from application.workout.video_catalog_service import VideoCatalogService
from domains.training.recommendation_engine import TrainingRecommendationEngine

# Composition Root der HTTP-Anwendung.
#
# Die Objekte leben aktuell für die gesamte Laufzeit des Backend-Prozesses.
# Später können wir hier bei Bedarf auf FastAPI-Dependencies umstellen,
# ohne die fachlichen Router erneut umzubauen.
telemetry_service = TelemetryService()

person_repository = SqlAlchemyPersonRepository()
person_service = PersonService(repository=person_repository)

person_profile_repository = SqlAlchemyPersonProfileRepository()
person_profile_service = PersonProfileService(
    repository=person_profile_repository,
)

person_profile_writer = SqlAlchemyPersonProfileWriter()
person_management_service = PersonManagementService(
    person_repository=person_repository,
    profile_writer=person_profile_writer,
)

check_in_repository = SqlAlchemyCheckInRepository()
check_in_service = CheckInService(
    repository=check_in_repository,
)

training_recommendation_engine = TrainingRecommendationEngine()

workout_repository = SqlAlchemyWorkoutRepository()
workout_video_repository = SqlAlchemyWorkoutVideoRepository()

workout_service = WorkoutService(
    repository=workout_repository,
    video_repository=workout_video_repository,
)

video_catalog_service = VideoCatalogService(
    repository=workout_video_repository,
)

telemetry_broadcaster = TelemetryBroadcaster()
