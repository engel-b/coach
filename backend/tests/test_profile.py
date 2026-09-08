from datetime import date

from domains.person.profile import PersonProfile, TrainingGoal


def test_existing_profile_remains_compatible() -> None:
    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.GENERAL_FITNESS,
    )

    assert profile.person_id == 1
    assert profile.start_weight_kg is None
    assert profile.target_weight_kg is None


def test_weight_loss_profile_can_store_goal_weights() -> None:
    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.WEIGHT_LOSS,
        start_weight_kg=95.5,
        target_weight_kg=82.0,
    )

    assert profile.start_weight_kg == 95.5
    assert profile.target_weight_kg == 82.0


def test_muscle_gain_is_available() -> None:
    assert TrainingGoal.MUSCLE_GAIN.value == "muscle_gain"


def test_existing_training_goals_keep_their_values() -> None:
    assert TrainingGoal.GENERAL_FITNESS.value == "general_fitness"
    assert TrainingGoal.WEIGHT_LOSS.value == "weight_loss"
    assert TrainingGoal.ENDURANCE.value == "endurance"
