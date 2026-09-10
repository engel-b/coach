from features.check_in.persistence.sqlalchemy_check_in_repository import (
    SqlAlchemyCheckInRepository,
)
from features.check_in.service.check_in_service import CheckInService
from features.person.persistence.sqlalchemy_person_profile_repository import (
    SqlAlchemyPersonProfileRepository,
)
from features.person.persistence.sqlalchemy_person_profile_writer import (
    SqlAlchemyPersonProfileWriter,
)
from features.person.persistence.sqlalchemy_person_repository import (
    SqlAlchemyPersonRepository,
)
from features.person.service.management_service import PersonManagementService
from features.person.service.person_service import PersonService
from features.person.service.profile_service import PersonProfileService
from features.telemetry.service.broadcaster import TelemetryBroadcaster
from features.telemetry.service.service import TelemetryService
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.workout.persistence.sqlalchemy_workout_repository import (
    SqlAlchemyWorkoutRepository,
)
from features.workout.persistence.sqlalchemy_workout_video_repository import (
    SqlAlchemyWorkoutVideoRepository,
)
from features.workout.service.video_catalog_service import VideoCatalogService
from features.workout.service.workout_service import WorkoutService

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
