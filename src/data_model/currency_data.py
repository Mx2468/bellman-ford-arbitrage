from pydantic import BaseModel

class CurrencyCodes(BaseModel):
    currencies: set[str]

class ForexDataWithBase(BaseModel):
    base: str
    rates: dict[str, float]