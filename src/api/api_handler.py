import re
from typing import Dict, Tuple, Union

class APIHandler:
    def __init__(self):
        # Regex for validating 3-letter currency codes
        self.currency_code_pattern = re.compile(r'^[A-Za-z]{3}$')

    def parse_response(self, response: Dict) -> Dict[Tuple[str, str], float]:
        """
        Parse API response and convert it to a format suitable for graph creation.
        
        Args:
            response (dict): API response containing base currency and rates
            
        Returns:
            dict: Currency pairs and their exchange rates
            
        Raises:
            ValueError: If response format is invalid or contains invalid rates
        """
        if "base" not in response:
            raise KeyError("Response missing base currency")
        
        base_currency = response["base"].upper()
        self._validate_response_structure(response, base_currency)
        rates = self._validate_and_normalize_rates(response["rates"])
        return self._calculate_all_pairs(base_currency, rates)
    
    def _validate_response_structure(self, response: Dict, base_currency: str) -> None:
        """Validate the basic structure of the API response."""
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
            
        if "base" not in response:
            raise ValueError("Response missing base currency")
            
        if "rates" not in response:
            raise ValueError("Response missing rates data")
            
        if not isinstance(response["rates"], dict):
            raise ValueError("Rates must be a dictionary")
        
        if base_currency in response["rates"]:
            raise KeyError(f"Base currency {base_currency} found in rates")
            
        if len(response.keys()) > 2:
            raise ValueError("Response contains unexpected fields")
    
    def _validate_and_normalize_rates(self, rates: Dict) -> Dict[str, float]:
        """Validate and normalize currency rates."""
        if not rates:
            raise ValueError("Empty rates data")
            
        normalized_rates = {}
        
        for currency, rate in rates.items():
            # Validate currency code
            if not self.currency_code_pattern.match(currency):
                raise ValueError(f"Invalid currency code format: {currency}")
                
            # Validate rate value
            if not isinstance(rate, (int, float)):
                raise ValueError(f"Non-numeric rate for currency {currency}")
                
            if rate <= 0:
                raise ValueError(f"Invalid rate for {currency}: {rate}")
                
            # Normalize currency code to uppercase
            normalized_rates[currency.upper()] = float(rate)
            
        return normalized_rates
    
    def _calculate_all_pairs(self, base_currency: str, rates: Dict[str, float]) -> Dict[Tuple[str, str], float]:
        """Calculate all possible currency pairs and their rates."""
        pairs = {}
        currencies = list(rates.keys()) + [base_currency]
        
        for curr1 in currencies:
            for curr2 in currencies:
                if curr1 != curr2:
                    # Calculate rate based on whether it's base currency or not
                    if curr1 == base_currency:
                        pairs[(curr1, curr2)] = rates[curr2]
                    elif curr2 == base_currency:
                        pairs[(curr1, curr2)] = 1 / rates[curr1]
                    else:
                        # Cross rate calculation
                        pairs[(curr1, curr2)] = rates[curr2] / rates[curr1]
        
        return pairs 