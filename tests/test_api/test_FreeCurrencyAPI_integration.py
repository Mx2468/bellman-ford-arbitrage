import pytest
import requests
from unittest.mock import patch, Mock, MagicMock
from api.FreecurrencyAPI_integration import (
    FreeCurrencyAPI, 
    get_currency_list, 
    validate_currencies,
    FreeCurrencyAPICurrencyCodes,
    BASE_URL,
    STATUS_URL,
    LATEST_RATES_URL,
    CURRENCY_LIST_URL
)
from data_model.currency_data import CurrencyCodes


class TestGetCurrencyList:
    """Test the get_currency_list function"""
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_currency_list_success(self, mock_get):
        """Test successful currency list retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "USD": {"symbol": "$", "name": "US Dollar"},
                "EUR": {"symbol": "€", "name": "Euro"},
                "GBP": {"symbol": "£", "name": "British Pound"}
            }
        }
        mock_get.return_value = mock_response
        
        result = get_currency_list()
        
        assert result == {"USD", "EUR", "GBP"}
        mock_get.assert_called_once_with(CURRENCY_LIST_URL, headers={"apikey": "test_key"}, timeout=30)
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_currency_list_api_error(self, mock_get):
        """Test currency list retrieval with API error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_get.return_value = mock_response
        
        with pytest.raises(ConnectionError, match="The API returned an error: Invalid API key"):
            get_currency_list()
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_currency_list_empty_response(self, mock_get):
        """Test currency list retrieval with empty data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}
        mock_get.return_value = mock_response
        
        result = get_currency_list()
        
        assert result == set()


class TestValidateCurrencies:
    """Test the validate_currencies function"""
    
    @patch('api.FreecurrencyAPI_integration.get_currency_list')
    def test_validate_currencies_all_valid(self, mock_get_currency_list):
        """Test validation with all valid currencies"""
        mock_get_currency_list.return_value = {"USD", "EUR", "GBP", "JPY", "CAD"}
        currencies_to_validate = {"USD", "EUR", "GBP"}
        
        result = validate_currencies(currencies_to_validate)
        
        assert result == currencies_to_validate
    
    @patch('api.FreecurrencyAPI_integration.get_currency_list')
    def test_validate_currencies_invalid_currency(self, mock_get_currency_list):
        """Test validation with invalid currency"""
        mock_get_currency_list.return_value = {"USD", "EUR", "GBP"}
        currencies_to_validate = {"USD", "EUR", "INVALID"}
        
        with pytest.raises(ValueError, match="The currency INVALID is not supported by the API"):
            validate_currencies(currencies_to_validate)
    
    @patch('api.FreecurrencyAPI_integration.get_currency_list')
    def test_validate_currencies_empty_set(self, mock_get_currency_list):
        """Test validation with empty currency set"""
        mock_get_currency_list.return_value = {"USD", "EUR", "GBP"}
        currencies_to_validate = set()
        
        result = validate_currencies(currencies_to_validate)
        
        assert result == set()


class TestFreeCurrencyAPICurrencyCodes:
    """Test the FreeCurrencyAPICurrencyCodes class"""
    
    @patch('api.FreecurrencyAPI_integration.validate_currencies')
    def test_currency_codes_creation_valid(self, mock_validate):
        """Test creating currency codes with valid currencies"""
        mock_validate.return_value = {"USD", "EUR", "GBP"}
        
        currency_codes = FreeCurrencyAPICurrencyCodes(currencies={"USD", "EUR", "GBP"})
        
        assert currency_codes.currencies == {"USD", "EUR", "GBP"}
        mock_validate.assert_called_once_with({"USD", "EUR", "GBP"})
    
    @patch('api.FreecurrencyAPI_integration.validate_currencies')
    def test_currency_codes_string_representation(self, mock_validate):
        """Test string representation of currency codes"""
        mock_validate.return_value = {"USD", "EUR", "GBP"}
        
        currency_codes = FreeCurrencyAPICurrencyCodes(currencies={"USD", "EUR", "GBP"})
        result = str(currency_codes)
        
        # Since sets are unordered, we need to check all currencies are present
        assert "USD" in result
        assert "EUR" in result
        assert "GBP" in result
        assert result.count(",") == 2  # Two commas for three currencies
    
    @patch('api.FreecurrencyAPI_integration.validate_currencies')
    def test_currency_codes_validation_error(self, mock_validate):
        """Test currency codes creation with validation error"""
        mock_validate.side_effect = ValueError("Invalid currency")
        
        with pytest.raises(ValueError, match="Invalid currency"):
            FreeCurrencyAPICurrencyCodes(currencies={"USD", "INVALID"})


class TestFreeCurrencyAPI:
    """Test the FreeCurrencyAPI class"""
    
    def test_init_with_key(self):
        """Test initialization with provided API key"""
        api = FreeCurrencyAPI(key="test_key")
        assert api._key == "test_key"
    
    @patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', 'default_key')
    def test_init_without_key(self):
        """Test initialization without provided API key"""
        with patch.object(FreeCurrencyAPI, 'get_API_key', return_value='default_key'):
            api = FreeCurrencyAPI()
            assert api._key == 'default_key'
    
    def test_get_api_key_with_instance_key(self):
        """Test API key retrieval when instance has key"""
        api = FreeCurrencyAPI(key="instance_key")
        assert api.get_API_key() == "instance_key"
    
    @patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', 'file_key')
    def test_get_api_key_from_file(self):
        """Test API key retrieval from file"""
        api = FreeCurrencyAPI()
        api._key = None
        assert api.get_API_key() == 'file_key'
    
    @patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', None)
    @patch('os.environ.get')
    def test_get_api_key_from_environment(self, mock_env_get):
        """Test API key retrieval from environment variable"""
        mock_env_get.return_value = "env_key"
        api = FreeCurrencyAPI()
        api._key = None
        
        assert api.get_API_key() == "env_key"
        mock_env_get.assert_called_once_with("FREECURRENCYAPI_KEY")
    
    @patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', None)
    @patch('os.environ.get')
    def test_get_api_key_not_found(self, mock_env_get):
        """Test API key retrieval when no key is available"""
        mock_env_get.return_value = None
        api = FreeCurrencyAPI()
        api._key = None
        
        with pytest.raises(ValueError, match="The key has not been provided"):
            api.get_API_key()
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_check_status_success(self, mock_get):
        """Test successful status check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        api = FreeCurrencyAPI(key="test_key")
        result = api.check_status()
        
        assert result is True
        mock_get.assert_called_once_with(STATUS_URL, params={"apikey": "test_key"}, timeout=5)
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_check_status_rate_limit_exceeded(self, mock_get):
        """Test status check with rate limit exceeded"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        api = FreeCurrencyAPI(key="test_key")
        
        with pytest.raises(ConnectionError, match="Your API Quota has been exhausted"):
            api.check_status()
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_check_status_other_error(self, mock_get):
        """Test status check with other HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        api = FreeCurrencyAPI(key="test_key")
        
        with pytest.raises(ConnectionError, match="The API returned an 500 error"):
            api.check_status()
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_exchange_rate_data_success(self, mock_get):
        """Test successful exchange rate data retrieval"""
        # Mock status check
        status_response = Mock()
        status_response.status_code = 200
        
        # Mock exchange rate response
        exchange_response = Mock()
        exchange_response.status_code = 200
        exchange_response.json.return_value = {
            "data": {
                "EUR": 0.92,
                "GBP": 0.79,
                "JPY": 144.50
            }
        }
        
        mock_get.side_effect = [status_response, exchange_response]
        
        api = FreeCurrencyAPI(key="test_key")
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP", "JPY"})
        
        with patch.object(currencies, '__str__', return_value="EUR,GBP,JPY"):
            result = api.get_exchange_rate_data("USD", currencies)
        
        expected_data = {
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 144.50
        }
        
        assert result == expected_data
        assert mock_get.call_count == 2
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_exchange_rate_data_api_error(self, mock_get):
        """Test exchange rate data retrieval with API error"""
        # Mock status check success
        status_response = Mock()
        status_response.status_code = 200
        
        # Mock exchange rate error
        exchange_response = Mock()
        exchange_response.status_code = 400
        exchange_response.json.return_value = {"message": "Invalid base currency"}
        
        mock_get.side_effect = [status_response, exchange_response]
        
        api = FreeCurrencyAPI(key="test_key")
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP"})
        
        with pytest.raises(ConnectionError, match="The API returned an error: Invalid base currency"):
            api.get_exchange_rate_data("INVALID", currencies)
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_exchange_rate_data_status_check_fails(self, mock_get):
        """Test exchange rate data retrieval when status check fails"""
        # Mock status check failure
        status_response = Mock()
        status_response.status_code = 429
        mock_get.return_value = status_response
        
        api = FreeCurrencyAPI(key="test_key")
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP"})
        
        with pytest.raises(ConnectionError, match="Your API Quota has been exhausted"):
            api.get_exchange_rate_data("USD", currencies)
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_exchange_rate_data_timeout(self, mock_get):
        """Test exchange rate data retrieval with timeout"""
        # Mock status check success
        status_response = Mock()
        status_response.status_code = 200
        
        # Mock timeout on exchange rate request
        mock_get.side_effect = [status_response, requests.exceptions.Timeout()]
        
        api = FreeCurrencyAPI(key="test_key")
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP"})
        
        with pytest.raises(requests.exceptions.Timeout):
            api.get_exchange_rate_data("USD", currencies)
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_get_exchange_rate_data_connection_error(self, mock_get):
        """Test exchange rate data retrieval with connection error"""
        # Mock status check success
        status_response = Mock()
        status_response.status_code = 200
        
        # Mock connection error on exchange rate request
        mock_get.side_effect = [status_response, requests.exceptions.ConnectionError()]
        
        api = FreeCurrencyAPI(key="test_key")
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP"})
        
        with pytest.raises(requests.exceptions.ConnectionError):
            api.get_exchange_rate_data("USD", currencies)


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_full_workflow_success(self, mock_get):
        """Test complete workflow from initialization to data retrieval"""
        # Mock currency list response
        currency_list_response = Mock()
        currency_list_response.status_code = 200
        currency_list_response.json.return_value = {
            "data": {
                "USD": {"symbol": "$", "name": "US Dollar"},
                "EUR": {"symbol": "€", "name": "Euro"},
                "GBP": {"symbol": "£", "name": "British Pound"}
            }
        }
        
        # Mock status check response
        status_response = Mock()
        status_response.status_code = 200
        
        # Mock exchange rate response
        exchange_response = Mock()
        exchange_response.status_code = 200
        exchange_response.json.return_value = {
            "data": {
                "EUR": 0.92,
                "GBP": 0.79
            }
        }
        
        mock_get.side_effect = [currency_list_response, status_response, exchange_response]
        
        # Create API instance
        api = FreeCurrencyAPI(key="test_key")
        
        # Create validated currency codes
        currencies = FreeCurrencyAPICurrencyCodes(currencies={"EUR", "GBP"})
        
        # Get exchange rate data
        result = api.get_exchange_rate_data("USD", currencies)
        
        assert result == {"EUR": 0.92, "GBP": 0.79}
        assert mock_get.call_count == 3
    
    @patch('api.FreecurrencyAPI_integration.requests.get')
    def test_api_key_from_file_integration(self, mock_get):
        """Test integration with API key from file"""
        with patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', 'file_api_key'):
            status_response = Mock()
            status_response.status_code = 200
            mock_get.return_value = status_response
            
            api = FreeCurrencyAPI()
            result = api.check_status()
            
            assert result is True
            mock_get.assert_called_once_with(STATUS_URL, params={"apikey": "file_api_key"}, timeout=5)
    
    def test_currency_codes_inheritance(self):
        """Test that FreeCurrencyAPICurrencyCodes properly inherits from CurrencyCodes"""
        with patch('api.FreecurrencyAPI_integration.validate_currencies', return_value={"USD", "EUR"}):
            currency_codes = FreeCurrencyAPICurrencyCodes(currencies={"USD", "EUR"})
            
            assert isinstance(currency_codes, CurrencyCodes)
            assert hasattr(currency_codes, 'currencies')
            assert currency_codes.currencies == {"USD", "EUR"}


@pytest.fixture
def mock_api_key():
    """Fixture to mock API key"""
    with patch('api.FreecurrencyAPI_integration.FREECURRENCYAPI_KEY', 'test_key'):
        yield 'test_key'


@pytest.fixture
def sample_currency_codes():
    """Fixture for sample currency codes"""
    with patch('api.FreecurrencyAPI_integration.validate_currencies', return_value={"USD", "EUR", "GBP"}):
        return FreeCurrencyAPICurrencyCodes(currencies={"USD", "EUR", "GBP"})


class TestFixtures:
    """Test using fixtures"""
    
    def test_mock_api_key_fixture(self, mock_api_key):
        """Test that the mock API key fixture works"""
        assert mock_api_key == 'test_key'
    
    def test_sample_currency_codes_fixture(self, sample_currency_codes):
        """Test that the sample currency codes fixture works"""
        assert sample_currency_codes.currencies == {"USD", "EUR", "GBP"}
        assert isinstance(sample_currency_codes, FreeCurrencyAPICurrencyCodes)

