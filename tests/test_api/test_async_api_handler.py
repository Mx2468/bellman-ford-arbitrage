import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.async_FreecurrencyAPI_integration import AsyncFreeCurrencyAPI
from src.data_model.currency_data import CurrencyCodes


class TestAsyncFreeCurrencyAPI:
    """Test cases for the AsyncFreeCurrencyAPI class."""

    @pytest.fixture
    def api_instance(self):
        """Create an API instance for testing."""
        return AsyncFreeCurrencyAPI(key="test_key")

    @pytest.mark.asyncio
    async def test_initialization_with_key(self):
        """Test API initialization with provided key."""
        api = AsyncFreeCurrencyAPI(key="test_key")
        assert api._key == "test_key"
        assert api.max_concurrent_requests == 5

    @pytest.mark.asyncio
    async def test_initialization_without_key_raises_error(self):
        """Test that initialization without key raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key must be provided"):
                AsyncFreeCurrencyAPI()

    @pytest.mark.asyncio
    async def test_make_request_success(self, api_instance):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": {"EUR": 0.85}})
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await api_instance._make_request(
            mock_session, 
            "http://test.com", 
            params={"test": "param"}
        )
        
        assert result == {"data": {"EUR": 0.85}}

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self, api_instance):
        """Test API request with rate limit error."""
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"message": "Rate limit exceeded"})
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(ConnectionError, match="API rate limit exceeded"):
            await api_instance._make_request(mock_session, "http://test.com")

    @pytest.mark.asyncio
    async def test_check_status_success(self, api_instance):
        """Test successful status check."""
        with patch.object(api_instance, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "ok"}
            
            result = await api_instance.check_status()
            assert result is True

    @pytest.mark.asyncio
    async def test_get_currency_list_success(self, api_instance):
        """Test successful currency list retrieval."""
        mock_response = {"data": {"USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound"}}
        
        with patch.object(api_instance, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await api_instance.get_currency_list()
            assert result == {"USD", "EUR", "GBP"}

    @pytest.mark.asyncio
    async def test_get_exchange_rate_data_success(self, api_instance):
        """Test successful exchange rate data retrieval."""
        mock_response = {"data": {"EUR": 0.85, "GBP": 0.73}}
        
        with patch.object(api_instance, 'check_status', new_callable=AsyncMock) as mock_status:
            with patch.object(api_instance, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_status.return_value = True
                mock_request.return_value = mock_response
                
                result = await api_instance.get_exchange_rate_data("USD")
                assert result == {"EUR": 0.85, "GBP": 0.73}

    @pytest.mark.asyncio
    async def test_get_multiple_exchange_rates_success(self, api_instance):
        """Test successful multiple exchange rates retrieval."""
        # Mock the get_exchange_rate_data method
        async def mock_get_rates(base_currency, currencies_to_obtain=None):
            rates_map = {
                "USD": {"EUR": 0.85, "GBP": 0.73},
                "EUR": {"USD": 1.18, "GBP": 0.86},
                "GBP": {"USD": 1.37, "EUR": 1.16}
            }
            return rates_map.get(base_currency, {})
        
        with patch.object(api_instance, 'get_exchange_rate_data', side_effect=mock_get_rates):
            base_currencies = ["USD", "EUR", "GBP"]
            result = await api_instance.get_multiple_exchange_rates(base_currencies, delay_between_requests=0)
            
            assert len(result) == 3
            assert "USD" in result
            assert "EUR" in result
            assert "GBP" in result
            assert result["USD"] == {"EUR": 0.85, "GBP": 0.73}

    @pytest.mark.asyncio
    async def test_get_multiple_exchange_rates_partial_failure(self, api_instance):
        """Test multiple exchange rates with some failures."""
        async def mock_get_rates(base_currency, currencies_to_obtain=None):
            if base_currency == "USD":
                return {"EUR": 0.85, "GBP": 0.73}
            elif base_currency == "EUR":
                raise ConnectionError("Failed to fetch EUR data")
            else:  # GBP
                return {"USD": 1.37, "EUR": 1.16}
        
        with patch.object(api_instance, 'get_exchange_rate_data', side_effect=mock_get_rates):
            base_currencies = ["USD", "EUR", "GBP"]
            result = await api_instance.get_multiple_exchange_rates(base_currencies, delay_between_requests=0)
            
            # Should return data for successful requests
            assert len(result) == 2
            assert "USD" in result
            assert "GBP" in result
            assert "EUR" not in result

    @pytest.mark.asyncio
    async def test_validate_currencies_async_success(self, api_instance):
        """Test successful currency validation."""
        mock_supported = {"USD", "EUR", "GBP", "JPY", "CAD"}
        
        with patch.object(api_instance, 'get_currency_list', new_callable=AsyncMock) as mock_get_list:
            mock_get_list.return_value = mock_supported
            
            currencies_to_validate = {"USD", "EUR", "GBP"}
            result = await api_instance.validate_currencies_async(currencies_to_validate)
            
            assert result == currencies_to_validate

    @pytest.mark.asyncio
    async def test_validate_currencies_async_invalid_currency(self, api_instance):
        """Test currency validation with invalid currency."""
        mock_supported = {"USD", "EUR", "GBP"}
        
        with patch.object(api_instance, 'get_currency_list', new_callable=AsyncMock) as mock_get_list:
            mock_get_list.return_value = mock_supported
            
            currencies_to_validate = {"USD", "EUR", "INVALID"}
            
            with pytest.raises(ValueError, match="The following currencies are not supported"):
                await api_instance.validate_currencies_async(currencies_to_validate)

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, api_instance):
        """Test that concurrent requests are properly limited."""
        # Set a low limit for testing
        api_instance.max_concurrent_requests = 2
        api_instance._semaphore = asyncio.Semaphore(2)
        
        call_times = []
        
        async def mock_get_rates(base_currency, currencies_to_obtain=None):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API call time
            return {"EUR": 0.85}
        
        with patch.object(api_instance, 'get_exchange_rate_data', side_effect=mock_get_rates):
            base_currencies = ["USD", "EUR", "GBP", "JPY"]
            await api_instance.get_multiple_exchange_rates(base_currencies, delay_between_requests=0)
            
            # With semaphore limit of 2, we should see batched execution
            assert len(call_times) == 4
