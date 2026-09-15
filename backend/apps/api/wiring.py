import os
from pathlib import Path

from adapters.llm.local_llm_coach_message_generator import LocalLlmCoachMessageGenerator
from apps.api.live_coaching_event_publisher import LiveCoachingEventPublisher
from apps.api.live_coaching_lifecycle import LiveCoachingLifecycle
from features.check_in.persistence.sqlalchemy_check_in_repository import (
    SqlAlchemyCheckInRepository,
)
from features.check_in.service.check_in_service import CheckInService
from features.coaching.api.broadcaster import LiveCoachingBroadcaster
from features.coaching.domain.live_coaching import LiveCoachingRules
from features.coaching.service.live_coaching_coordinator import LiveCoachingCoordinator
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
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
from features.speech.adapters.piper_tts import PiperTtsAdapter
from features.speech.service.speech_service import SpeechService
from features.telemetry.service.broadcaster import TelemetryBroadcaster
from features.telemetry.service.service import TelemetryService
from features.training.domain.coach_message_generator import CoachMessageGenerator
from features.training.domain.readiness import ReadinessRules
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.training.domain.weight_trend import WeightTrendRules
from features.training.service.fallback_coach_message_generator import (
    FallbackCoachMessageGenerator,
)
from features.training.service.pre_workout_coaching_planner import PreWorkoutCoachingPlanner
from features.training.service.pre_workout_reason_builder import PreWorkoutReasonBuilder
from features.training.service.readiness_service import ReadinessService
from features.training.service.weight_goal_progress_service import WeightGoalProgressService
from features.training.service.weight_trend_service import WeightTrendService
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
live_coaching_engine = LiveCoachingEngine(
    rules=LiveCoachingRules(
        deviation_seconds_before_action=20.0,
    )
)
live_coaching_coordinator = LiveCoachingCoordinator(
    coaching_engine=live_coaching_engine,
)
live_coaching_broadcaster = LiveCoachingBroadcaster()
live_coaching_event_publisher = LiveCoachingEventPublisher(
    broadcaster=live_coaching_broadcaster,
)
live_coaching_lifecycle = LiveCoachingLifecycle(
    coordinator=live_coaching_coordinator,
    decision_handler=live_coaching_event_publisher.publish,
    runtime_handler=live_coaching_event_publisher.publish_runtime_event,
)

telemetry_service = TelemetryService()
telemetry_service.add_heart_rate_handler(
    live_coaching_lifecycle.handle_heart_rate,
)

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
weight_trend_rules = WeightTrendRules(
    window_days=30,
    min_sample_count=3,
    min_span_days=7.0,
    stable_threshold_kg_per_week=0.10,
)
weight_trend_service = WeightTrendService(rules=weight_trend_rules)
weight_goal_progress_service = WeightGoalProgressService()
readiness_rules = ReadinessRules(
    short_sleep_hours=6.0,
    high_daily_steps=12_000,
    recent_training_window_days=3,
    high_recent_training_minutes=90.0,
    high_recent_workout_count=3,
    caution_duration_cap_minutes=30,
)
readiness_service = ReadinessService(rules=readiness_rules)

template_pre_workout_message_generator = PreWorkoutReasonBuilder()

pre_workout_message_generator: CoachMessageGenerator
local_llm_enabled = os.environ.get("HEALTH_COACH_LLM_ENABLED", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
if local_llm_enabled:
    local_llm_message_generator = LocalLlmCoachMessageGenerator(
        base_url=os.environ.get("HEALTH_COACH_LLM_BASE_URL", "http://127.0.0.1:8080"),
        model=os.environ.get("HEALTH_COACH_LLM_MODEL", "local-coach"),
        timeout_seconds=float(os.environ.get("HEALTH_COACH_LLM_TIMEOUT_SECONDS", "4.0")),
    )
    pre_workout_message_generator = FallbackCoachMessageGenerator(
        primary=local_llm_message_generator,
        fallback=template_pre_workout_message_generator,
    )
else:
    pre_workout_message_generator = template_pre_workout_message_generator

pre_workout_coaching_planner = PreWorkoutCoachingPlanner(
    engine=training_recommendation_engine,
    message_generator=pre_workout_message_generator,
)

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


piper_model_path = Path(
    os.environ.get(
        "HEALTH_COACH_PIPER_MODEL",
        "models/piper/de_DE-thorsten-medium.onnx",
    )
)
speech_service = SpeechService(
    tts=PiperTtsAdapter(model_path=piper_model_path),
)
