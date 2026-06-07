#https://www.google.com/finance/quote/{currency_code_1}-{currency_code_2}
#look for class =YMlKec fxKbKc and get the text

import requests

#TODO: Use pydantic models to validate the inputs
#TODO: Use asyncio to launch all the requests in parallel
#TODO: Use random user agents with each request

# Start of Selection
def scrape_google_currencies(currency_code_1, currency_code_2):
    import re
    url = f"https://www.google.com/finance/quote/{currency_code_1}-{currency_code_2}"
    response = requests.get(url)
    match = re.search(r'<div[^>]*class="[^"]*YMlKec fxKbKc[^"]*"[^>]*>([^<]+)</div>', response.text)
    if match:
        return match.group(1).strip()
    return None

if __name__ == "__main__":
    print(scrape_google_currencies("USD", "EUR"))
    print(scrape_google_currencies("EUR", "USD"))