import json
from urllib.request import Request, urlopen

from features.training.domain.coach_message import CoachMessageContext


class LocalLlmCoachMessageGenerator:
    """
    Formuliert einen bereits entschiedenen CoachMessageContext über ein lokales,
    OpenAI-kompatibles Chat-Completions-API.

    Der Adapter darf keine Trainingsentscheidung treffen. Fehler, Timeouts und
    leere Antworten werden absichtlich nach außen gegeben, damit der umgebende
    FallbackCoachMessageGenerator deterministisch übernehmen kann.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 4.0,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must not be empty")
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self._endpoint_url = f"{base_url.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._timeout_seconds = timeout_seconds

    def generate(self, *, context: CoachMessageContext) -> str:
        payload = {
            "model": self._model,
            "temperature": 0.3,
            "max_tokens": 100,
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        self._context_payload(context),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                },
            ],
        }
        request = Request(
            self._endpoint_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=self._timeout_seconds) as response:
            response_body = response.read().decode("utf-8")

        return self._extract_message(response_body)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Du formulierst einen bereits fachlich geprüften Fitness-Coach-Text. "
            "Du darfst keine neuen Fakten, Ursachen, Diagnosen oder Zusammenhänge hinzufügen. "
            "Nenne ausschließlich Informationen, die ausdrücklich in der Eingabe stehen. "
            "Erfinde insbesondere keine Ursachen für Gewichtsveränderungen. "
            "Ändere keine Zahlen, keinen Workout-Typ und keine Dauer. "
            "Antworte auf Deutsch in höchstens zwei kurzen vollständigen Sätzen."
        )

    @staticmethod
    def _context_payload(context: CoachMessageContext) -> dict[str, object]:
        progress = context.weight_goal_progress
        weight_goal: dict[str, object] | None = None
        if progress is not None:
            weight_goal = {
                "status": progress.status.value,
                "start_weight_kg": progress.start_weight_kg,
                "current_weight_kg": progress.current_weight_kg,
                "target_weight_kg": progress.target_weight_kg,
                "remaining_kg": progress.remaining_kg,
                "lost_since_start_kg": progress.lost_since_start_kg,
                "progress_percent": progress.progress_percent,
            }

        return {
            "workout_type": context.workout_type.value,
            "total_duration_minutes": context.total_duration_minutes,
            "reason_codes": [reason.value for reason in context.reason_codes],
            "training_goal": context.training_goal.value,
            "readiness_max_duration_minutes": context.readiness_max_duration_minutes,
            "weight_trend": {
                "direction": context.weight_trend_direction.value,
                "kg_per_week": context.weight_trend_kg_per_week,
            },
            "weight_goal_progress": weight_goal,
        }

    @staticmethod
    def _extract_message(response_body: str) -> str:
        parsed: object = json.loads(response_body)
        if not isinstance(parsed, dict):
            raise TypeError("LLM response must be a JSON object")

        choices = parsed.get("choices")
        if not isinstance(choices, list) or not choices:
            raise TypeError("LLM response contains no choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise TypeError("LLM response choice has invalid shape")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise TypeError("LLM response contains no message")

        content = message.get("content")
        if not isinstance(content, str):
            raise TypeError("LLM response message contains no text")

        print(f"LLM coach response: {content!r}")
        return content.strip()
