from pydantic import BaseModel, Field

from features.speech.service.speech_service import MAX_SPEECH_TEXT_LENGTH


class SynthesizeSpeechRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=MAX_SPEECH_TEXT_LENGTH,
        description="Text, der lokal als Sprache synthetisiert werden soll.",
        examples=["Dein Puls ist ueber dem Zielbereich. Nimm etwas Tempo heraus."],
    )
