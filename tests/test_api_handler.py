import pytest
from api.api_handler import APIHandler

@pytest.fixture
def api_handler():
    return APIHandler()

@pytest.fixture
def sample_response():
    return {
        "base": "USD",
        "rates": {
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 144.50
        }
    }

def test_valid_response_parsing(api_handler, sample_response):
    """Test that a valid API response is correctly parsed into our internal format"""
    result = api_handler.parse_response(sample_response)
    
    # Check if all currency pairs are created (including reverse pairs)
    expected_pairs = {
        ("USD", "EUR"): 0.92,
        ("EUR", "USD"): 1/0.92,
        ("USD", "GBP"): 0.79,
        ("GBP", "USD"): 1/0.79,
        ("USD", "JPY"): 144.50,
        ("JPY", "USD"): 1/144.50,
        ("EUR", "GBP"): 0.79/0.92,
        ("GBP", "EUR"): 0.92/0.79,
        ("EUR", "JPY"): 144.50/0.92,
        ("JPY", "EUR"): 0.92/144.50,
        ("GBP", "JPY"): 144.50/0.79,
        ("JPY", "GBP"): 0.79/144.50
    }
    
    assert result == expected_pairs

def test_empty_response(api_handler):
    """Test handling of empty response"""
    empty_response = {"base": "USD", "rates": {}}
    with pytest.raises(ValueError):
        api_handler.parse_response(empty_response)

def test_missing_base_currency(api_handler):
    """Test handling of response with missing base currency"""
    invalid_response = {"rates": {"EUR": 0.92}}
    with pytest.raises(KeyError):
        api_handler.parse_response(invalid_response)

def test_invalid_rate_values(api_handler, sample_response):
    """Test handling of invalid rate values"""
    sample_response["rates"]["GBP"] = -0.79
    sample_response["rates"]["JPY"] = 0
    with pytest.raises(ValueError):
        api_handler.parse_response(sample_response)

def test_single_currency_pair(api_handler):
    """Test handling of response with only one currency pair"""
    response = {
        "base": "USD",
        "rates": {
            "EUR": 0.92
        }
    }
    result = api_handler.parse_response(response)
    
    expected_pairs = {
        ("USD", "EUR"): 0.92,
        ("EUR", "USD"): 1/0.92
    }
    assert result == expected_pairs

def test_base_currency_in_rates(api_handler):
    """Test handling of response where base currency appears in rates"""
    response = {
        "base": "USD",
        "rates": {
            "USD": 1.00,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 144.50
        }
    }
    
    with pytest.raises(KeyError):
        api_handler.parse_response(response)

def test_floating_point_precision(api_handler, sample_response  ):
    """Test handling of floating point precision in rates"""
    result = api_handler.parse_response(sample_response)
    assert result[("USD", "EUR")] == pytest.approx(0.92)
    assert result[("EUR", "USD")] == pytest.approx(1/0.92)
    assert result[("USD", "GBP")] == pytest.approx(0.79)
    assert result[("GBP", "USD")] == pytest.approx(1/0.79)
    assert result[("USD", "JPY")] == pytest.approx(144.50)
    assert result[("JPY", "USD")] == pytest.approx(1/144.50)

def test_rate_threshold_validation(api_handler):
    """Test validation of rates that are extremely small or large"""
    response = {
        "base": "USD",
        "rates": {
            "GBP": 1e-11,
            "EUR": 1e12,
            "JPY": 1e-3
        }
    }
    result = api_handler.parse_response(response)
    assert result[("USD", "GBP")] == pytest.approx(1e-11)
    assert result[("GBP", "USD")] == pytest.approx(1e11)
    assert result[("USD", "EUR")] == pytest.approx(1e12)
    assert result[("EUR", "USD")] == pytest.approx(1e-12)
    assert result[("USD", "JPY")] == pytest.approx(1e-3)
    assert result[("JPY", "USD")] == pytest.approx(1e3)

def test_duplicate_currency_handling(api_handler, sample_response):
    """Test handling of duplicate currency entries in response"""
    sample_response["rates"]["EUR"] = 0.92
    result = api_handler.parse_response(sample_response)
    assert result[("USD", "EUR")] == pytest.approx(0.92)
    assert result[("EUR", "USD")] == pytest.approx(1/0.92)

def test_case_sensitivity(api_handler):
    """Test handling of different cases in currency codes"""
    response = {
        "base": "USD",
        "rates": {
            "EuR": 0.92,
            "gbp": 0.79,
            "JPY": 144.50
        }
    }
    result = api_handler.parse_response(response)
    assert result[("USD", "EUR")] == pytest.approx(0.92)
    assert result[("EUR", "USD")] == pytest.approx(1/0.92)
    assert result[("USD", "GBP")] == pytest.approx(0.79)
    assert result[("GBP", "USD")] == pytest.approx(1/0.79)
    assert result[("USD", "JPY")] == pytest.approx(144.50)
    assert result[("JPY", "USD")] == pytest.approx(1/144.50)


def test_integer_rate_values(api_handler):
    """Test handling of integer rate values"""
    response = {
        "base": "USD",
        "rates": {
            "EUR": 1,
            "GBP": 2,
            "JPY": 3
        }
    }
    result = api_handler.parse_response(response)
    assert result[("USD", "EUR")] == pytest.approx(1.00)
    assert result[("EUR", "USD")] == pytest.approx(1.00)
    assert result[("USD", "GBP")] == pytest.approx(2.00)
    assert result[("GBP", "USD")] == pytest.approx(0.50)
    assert result[("USD", "JPY")] == pytest.approx(3.00)
    assert result[("JPY", "USD")] == pytest.approx(1/3.00)

def test_invalid_currency_codes(api_handler):
    """Test handling of invalid currency code formats"""
    response = {
        "base": "USD",
        "rates": {
            "Euro": 0.92,
            "GBP Sterling": 0.79,
            "JP243YEN": 144.50
        }
    }
    with pytest.raises(ValueError):
        api_handler.parse_response(response)

def test_missing_rates_key(api_handler):
    """Test handling of response with missing 'rates' key"""
    response = {
        "base": "USD",
        "rates": {}
    }
    with pytest.raises(ValueError):
        api_handler.parse_response(response)

def test_non_numeric_rates(api_handler):
    """Test handling of non-numeric values in rates"""
    response = {
        "base": "USD",
        "rates": {
            "EUR": "123",
            "GBP": "not a number",
            "JPY": {}
        }
    }
    with pytest.raises(ValueError):
        api_handler.parse_response(response)

def test_response_with_extra_fields(api_handler, sample_response):
    """Test handling of response with additional unexpected fields"""
    sample_response["extra1"] = "extra"
    sample_response["extra2"] = "extra"
    with pytest.raises(ValueError):
        api_handler.parse_response(sample_response)

def test_rate_calculation_consistency(api_handler, sample_response):
    """Test consistency of calculated cross-rates"""
    result = api_handler.parse_response(sample_response)
    assert result[("GBP", "EUR")] == pytest.approx(0.92/0.79)
    assert result[("EUR", "GBP")] == pytest.approx(0.79/0.92)
    assert result[("JPY", "GBP")] == pytest.approx(0.79/144.50)
    assert result[("GBP", "JPY")] == pytest.approx(144.50/0.79)
    assert result[("EUR", "JPY")] == pytest.approx(144.50/0.92)
    assert result[("JPY", "EUR")] == pytest.approx(0.92/144.50)



