from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PersonResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    display_name: str
