import requests
import os
from typing import Optional, Annotated
from pydantic import BaseModel, Field, AfterValidator

BASE_URL = "https://api.freecurrencyapi.com/v1"
STATUS_URL = f"{BASE_URL}/status"
LATEST_RATES_URL = f"{BASE_URL}/latest"
CURRENCY_LIST_URL = f"{BASE_URL}/currencies"

#TODO: Add currency list validation (https://freecurrencyapi.com/docs/currency-list)

from api.api_keys import FreeCurrencyAPIKey
FREECURRENCYAPI_KEY = FreeCurrencyAPIKey

def get_currency_list() -> set[str]:
    """
    Obtains the list of currencies supported by the API
    
    Returns:
        A tuple of currency codes
    
    Raises:
        ConnectionError: If the API returns an error
    """
    headers = {"apikey": FREECURRENCYAPI_KEY}
    response = requests.get(CURRENCY_LIST_URL, headers=headers, timeout=30)
    if response.status_code == 200:
        return set(response.json()["data"].keys())
    else:
        raise ConnectionError(f"The API returned an error: {response.json()['message']}")
    
def validate_currencies(currency_codes: set[str]) -> set[str]:
    """
    Validates the currencies to obtain
    
    Args:
        currency_codes: A tuple of currency codes to validate
    
    Returns:
        True if the currencies are valid, False otherwise
    
    Raises:
        ValueError: If the currency is not supported by the API
    """
    valid_currencies = set(get_currency_list())
    for currency in currency_codes:
        if currency not in valid_currencies:
            raise ValueError(f"The currency {currency} is not supported by the API")
    return currency_codes


class CurrencyCodes(BaseModel):
    currencies: Annotated[set[str], AfterValidator(validate_currencies)]

    def __str__(self) -> str:
        return ",".join(self.currencies)
    

class FreeCurrencyAPI:
    _key: Optional[str] = FREECURRENCYAPI_KEY

    def __init__(self, key=None):
        if key:
            self._key = key
        else:
            self._key = self.get_API_key()

    def get_API_key(self) -> str:
        """
        Attempt to obtain the API key from either the passed in variable to the class, an auxillary file, or environment variables
        """
        if self._key:
            return self._key
        else:
            try:
                from api.api_keys import FreeCurrencyAPIKey
                return FreeCurrencyAPIKey
            except:
                try:
                    return os.environ.get("FREECURRENCYAPI_KEY")
                except:
                    raise ValueError("The key has not been provided ")

    def check_status(self) -> bool:
        """
        Checks the status of the API status endpoint to see if a successful call can be made
        
        Returns:
            True if the API is available and can be called, False otherwise
        
        Raises:
            ConnectionError: If the API is not available or the API Quota has been exhausted
        """
        response = requests.get(STATUS_URL, params={"apikey": self.get_API_key()}, timeout=5)
        if response.status_code == 200:
            return True
        elif response.status_code == 429: #429 is the status code for rate limit exceeded
            raise ConnectionError("Your API Quota has been exhausted")
        else:
            raise ConnectionError(f"The API returned an {response.status_code} error")

    def get_exchange_rate_data(self, 
                               base_currency: str, 
                               currencies_to_obtain: CurrencyCodes) -> dict:
        """
        Obtains the latest exchange rate data
        
        Args:
            base_currency: A string containing the base currency code
            currencies_to_obtain: An optional list of currency codes for which to obtain the rates (defaults to fetching all rates) 

        Returns:
            A dictionary containing all the exchange rates for currencies from the base currency 

        Raises:
        """
        headers = {"apikey": self.get_API_key()}
        params = {"base_currency": base_currency,
                  "currencies": str(currencies_to_obtain)}
        if self.check_status():
            response = requests.get(LATEST_RATES_URL, headers=headers, params=params, timeout=30)
            print(response.json())
            if response.status_code == 200:
                return response.json()["data"]
            else:
                raise ConnectionError(f"The API returned an error: {response.json()['message']}")
        else:
            raise ConnectionError("Your API Quota has been exhausted")

def main():
    """
    Main method to demonstrate the FreeCurrencyAPI integration.
    """
    # Create an instance of the FreeCurrencyAPI
    api = FreeCurrencyAPI()
    
    # Example: Get exchange rates for USD as base currency
    base_currency = "USD"
    currencies_to_obtain = CurrencyCodes(currencies={"EUR", "GBP", "JPY", "CAD"})

    print(f"Fetching exchange rates for {base_currency}...")
    exchange_data = api.get_exchange_rate_data(
        base_currency=base_currency,
        currencies_to_obtain=currencies_to_obtain
    )
    
    print(f"Exchange rates from {base_currency}:")
    for currency, rate in exchange_data.items():
        print(f"  {base_currency} -> {currency}: {rate}")


if __name__ == "__main__":
    main()
