from pydantic import BaseModel

class ForexDataWithBase(BaseModel):
    base: str
    rates: dict[str, float]