from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PersonResponse(BaseModel):
    """Kurzansicht einer Person für die Personenauswahl."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(
        description="Stabile numerische ID der Person.",
        examples=[1],
    )
    display_name: str = Field(
        description="Anzeigename der Person.",
        examples=["Person 1"],
    )
