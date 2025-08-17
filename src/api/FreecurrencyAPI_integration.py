import requests
import os
from typing import Optional

BASE_URL = "https://api.freecurrencyapi.com/v1"
STATUS_URL = f"{BASE_URL}/status"
LATEST_RATES_URL = f"{BASE_URL}/latest"

#TODO: Add currency list validation (https://freecurrencyapi.com/docs/currency-list)

class FreeCurrencyAPI:
    _key: Optional[str] = None

    def __init__(self, key):
        self._key = key 

    def get_API_key(self):
        """
        Attempt to obtain the API key from either the passed in variable to the class, an auxillary file, or environment variables
        """
        if self._key:
            return self._key
        else:
            try:
                from src.api.api_keys import FreeCurrencyAPIKey
                return FreeCurrencyAPIKey
            except:
                try:
                    return os.environ["FREECURRENCYAPI_KEY"]
                except:
                    raise ValueError("The key has not been provided ")

    def check_status(self):
        """
        Checks the status of the API status endpoint to see if a successful call can be made
        """
        response = requests.get(STATUS_URL, params={"apikey": self.get_API_key()}, timeout=5)
        remaining_calls = response["quotas"]["month"]["remaining"]
        if remaining_calls < 20:
            print(f"Warning: Your API quota only has {remaining_calls} calls remaining ")
        elif remaining_calls == 0:
            raise ConnectionError("Your API Quota has been exhausted")
        else:
            return remaining_calls > 0

    def get_exchange_rate_data(self, 
                               base_currency: str, 
                               currencies_to_obtain: Optional[list[str]] = None) -> dict:
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
            return response["data"]
        else:
            raise ConnectionError("Your API Quota has been exhausted")



