import logging

from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.coach_message_generator import CoachMessageGenerator

logger = logging.getLogger(__name__)


class FallbackCoachMessageGenerator:
    """
    Versucht zuerst den primären Message-Generator und fällt bei einem
    Formulierungsfehler auf einen deterministischen Generator zurück.

    Die fachliche Trainingsentscheidung ist zu diesem Zeitpunkt bereits
    abgeschlossen. Der Fallback betrifft ausschließlich die sprachliche
    Formulierung der Coach-Nachricht.
    """

    def __init__(
        self,
        *,
        primary: CoachMessageGenerator,
        fallback: CoachMessageGenerator,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(self, *, context: CoachMessageContext) -> str:
        try:
            message = self._primary.generate(context=context)
        except Exception:
            logger.exception(
                "Primary coach message generator failed; using deterministic fallback",
            )
            return self._fallback.generate(context=context)

        if message.strip():
            return message

        logger.warning(
            "Primary coach message generator returned an empty message; using deterministic fallback",
        )
        return self._fallback.generate(context=context)
