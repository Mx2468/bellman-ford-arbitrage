import asyncio
import aiohttp
import os
from typing import Optional, List, Dict, Tuple
from pydantic import ValidationError
from data_model.currency_data import CurrencyCodes
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.freecurrencyapi.com/v1"
STATUS_URL = f"{BASE_URL}/status"
LATEST_RATES_URL = f"{BASE_URL}/latest"
CURRENCY_LIST_URL = f"{BASE_URL}/currencies"

FREECURRENCYAPI_KEY = os.environ.get("FREECURRENCYAPI_KEY")


class AsyncFreeCurrencyAPI:
    """Async version of the FreeCurrencyAPI for concurrent API calls."""
    
    def __init__(self, key: Optional[str] = None, max_concurrent_requests: int = 5):
        """
        Initialize the async API handler.
        
        Args:
            key: API key (optional, will use environment variable if not provided)
            max_concurrent_requests: Maximum number of concurrent API requests
        """
        self._key = key or FREECURRENCYAPI_KEY
        self.max_concurrent_requests = max_concurrent_requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        if not self._key:
            raise ValueError("API key must be provided either as parameter or FREECURRENCYAPI_KEY environment variable")

    async def _make_request(self, session: aiohttp.ClientSession, url: str, 
                           params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """
        Make an async HTTP request with rate limiting.
        
        Args:
            session: aiohttp client session
            url: Request URL
            params: Query parameters
            headers: Request headers
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ConnectionError: If API returns an error
            asyncio.TimeoutError: If request times out
        """
        async with self._semaphore:  # Rate limiting
            try:
                async with session.get(url, params=params, headers=headers, timeout=30) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    elif response.status == 429:
                        raise ConnectionError("API rate limit exceeded")
                    else:
                        error_msg = response_data.get('message', f'HTTP {response.status}')
                        raise ConnectionError(f"API returned error: {error_msg}")
                        
            except asyncio.TimeoutError:
                raise ConnectionError("Request timed out")
            except aiohttp.ClientError as e:
                raise ConnectionError(f"Network error: {str(e)}")

    async def check_status(self) -> bool:
        """
        Check if the API is available asynchronously.
        
        Returns:
            True if API is available, False otherwise
            
        Raises:
            ConnectionError: If API is not available or quota exhausted
        """
        headers = {"apikey": self._key}
        params = {"apikey": self._key}
        
        async with aiohttp.ClientSession() as session:
            try:
                await self._make_request(session, STATUS_URL, params=params, headers=headers)
                return True
            except ConnectionError:
                raise

    async def get_currency_list(self) -> set[str]:
        """
        Get the list of supported currencies asynchronously.
        
        Returns:
            Set of currency codes
            
        Raises:
            ConnectionError: If API returns an error
        """
        headers = {"apikey": self._key}
        
        async with aiohttp.ClientSession() as session:
            response_data = await self._make_request(session, CURRENCY_LIST_URL, headers=headers)
            return set(response_data["data"].keys())

    async def get_exchange_rate_data(self, base_currency: str, 
                                   currencies_to_obtain: Optional[CurrencyCodes] = None) -> Dict:
        """
        Get exchange rate data for a single base currency asynchronously.
        
        Args:
            base_currency: Base currency code
            currencies_to_obtain: Specific currencies to fetch (optional)
            
        Returns:
            Dictionary containing exchange rates
            
        Raises:
            ConnectionError: If API returns an error
        """
        headers = {"apikey": self._key}
        params = {"base_currency": base_currency}
        
        if currencies_to_obtain:
            params["currencies"] = str(currencies_to_obtain)
        
        async with aiohttp.ClientSession() as session:
            # Check status first
            await self.check_status()
            
            logger.info(f"Fetching exchange rates for base currency: {base_currency}")
            response_data = await self._make_request(session, LATEST_RATES_URL, 
                                                   params=params, headers=headers)
            return response_data["data"]

    async def get_multiple_exchange_rates(self, base_currencies: List[str], 
                                        currencies_to_obtain: Optional[CurrencyCodes] = None) -> Dict[str, Dict]:
        """
        Get exchange rate data for multiple base currencies concurrently.
        
        Args:
            base_currencies: List of base currency codes
            currencies_to_obtain: Specific currencies to fetch for each base (optional)
            
        Returns:
            Dictionary mapping base currency to its exchange rates
            
        Raises:
            ConnectionError: If any API call fails
        """
        logger.info(f"Fetching exchange rates for {len(base_currencies)} base currencies")
        
        async def fetch_with_delay(base_currency: str) -> Tuple[str, Dict]:
            """Fetch data for a single currency."""
            try:
                data = await self.get_exchange_rate_data(base_currency, currencies_to_obtain)
                logger.info(f"Successfully fetched data for {base_currency}")
                return base_currency, data
            except Exception as e:
                logger.error(f"Failed to fetch data for {base_currency}: {str(e)}")
                raise ConnectionError(f"Failed to fetch data for {base_currency}: {str(e)}")

        # Create tasks with staggered delays to respect rate limits
        tasks = []
        for base_currency in base_currencies:
            task = fetch_with_delay(base_currency)
            tasks.append(task)

        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            exchange_data = {}
            errors = []
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                else:
                    base_currency, data = result
                    exchange_data[base_currency] = data
            
            if errors:
                logger.warning(f"Some requests failed: {errors}")
                if len(errors) == len(base_currencies):
                    raise ConnectionError(f"All requests failed: {errors}")
            
            logger.info(f"Successfully fetched data for {len(exchange_data)} out of {len(base_currencies)} currencies")
            return exchange_data
            
        except Exception as e:
            logger.error(f"Error in concurrent API calls: {str(e)}")
            raise

    async def validate_currencies_async(self, currency_codes: set[str]) -> set[str]:
        """
        Validate currencies against the API's supported list asynchronously.
        
        Args:
            currency_codes: Set of currency codes to validate
            
        Returns:
            Set of valid currency codes
            
        Raises:
            ValueError: If any currency is not supported
        """
        valid_currencies = await self.get_currency_list()
        
        invalid_currencies = currency_codes - valid_currencies
        if invalid_currencies:
            raise ValueError(f"The following currencies are not supported by the API: {invalid_currencies}")
        
        return currency_codes


async def main():
    """
    Demonstration of the async API functionality.
    """
    try:
        # Create async API instance
        api = AsyncFreeCurrencyAPI()
        
        # Test single currency fetch
        print("Testing single currency fetch...")
        usd_rates = await api.get_exchange_rate_data("USD")
        print(f"USD rates sample: {dict(list(usd_rates.items())[:3])}")
        
        # Test multiple currency fetch
        print("\nTesting multiple currency fetch...")
        base_currencies = ["USD", "EUR", "GBP"]
        all_rates = await api.get_multiple_exchange_rates(base_currencies)
        
        print("Successfully fetched rates for:")
        for base_currency, rates in all_rates.items():
            print(f"  {base_currency}: {len(rates)} exchange rates")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
