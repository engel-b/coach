from features.speech.domain.tts import SynthesizedSpeech, TextToSpeech

MAX_SPEECH_TEXT_LENGTH = 500


class SpeechService:
    def __init__(self, tts: TextToSpeech) -> None:
        self._tts = tts

    def synthesize(self, text: str) -> SynthesizedSpeech:
        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError("text must not be empty")

        if len(normalized_text) > MAX_SPEECH_TEXT_LENGTH:
            raise ValueError(f"text must not exceed {MAX_SPEECH_TEXT_LENGTH} characters")

        return self._tts.synthesize(normalized_text)
