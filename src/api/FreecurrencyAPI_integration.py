import requests
import os
from typing import Optional

BASE_URL = "https://api.freecurrencyapi.com/v1"
STATUS_URL = f"{BASE_URL}/status"
LATEST_RATES_URL = f"{BASE_URL}/latest"

#TODO: Add currency list validation (https://freecurrencyapi.com/docs/currency-list)


class FreeCurrencyAPI:
    _key: Optional[str] = None

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
                    return os.environ["FREECURRENCYAPI_KEY"]
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
                               currencies_to_obtain: Optional[tuple[str, ...]] = None) -> dict:
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
                  "currencies": ",".join(currencies_to_obtain)}
        if self.check_status():
            response = requests.get(LATEST_RATES_URL, headers=headers, params=params, timeout=30)
            print(response.json())
            if response.status_code == 200:
                return response.json()["data"]
            else:
                raise ConnectionError(f"The API returned an error: {response.json()['message']}")
        else:
            raise ConnectionError("Your API Quota has been exhausted")



