from typing import Protocol

from features.training.domain.coach_message import CoachMessageContext


class CoachMessageGenerator(Protocol):
    """Port für die Formulierung bereits entschiedener Coach-Fakten."""

    def generate(self, *, context: CoachMessageContext) -> str:
        """Erzeugt eine Coach-Nachricht, ohne fachliche Entscheidungen zu treffen."""
        ...
