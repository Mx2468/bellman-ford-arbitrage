from pydantic import BaseModel

# TODO: Define a currency code type with appropriate validation 

class ForexDataWithBase(BaseModel):
    base: str
    rates: dict[str, float]