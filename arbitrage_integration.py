from api.FreecurrencyAPI_integration import FreeCurrencyAPI, get_currency_list
from graph.currency_graph import CurrencyGraph, Edge
from typing import List
from api.FreecurrencyAPI_integration import FreeCurrencyAPICurrencyCodes
from math import log
from time import sleep
import itertools
from api.scrape_google_currencies import scrape_google_currencies

from path_algorithms.bellman_ford import BellmanFord

#TODO: turn these into fastapi backend enpoints
#TODO: Create a frontend to interact with this backend (optionally passing a FreeCurrencyAPI key as a parameter, falling back to google scraping)


def create_currency_graph(currencies: List[str]) -> CurrencyGraph:
    graph = CurrencyGraph()
    all_rates = {}
    for currency in currencies:
        currencies_to_obtain = FreeCurrencyAPICurrencyCodes(currencies=currencies-{currency})
        rates = FreeCurrencyAPI().get_exchange_rate_data(currency, currencies_to_obtain)
        all_rates[currency] = rates
        sleep(10)
    
    for base_currency in all_rates.keys():
        source = base_currency
        for target in all_rates[base_currency].keys():
            if target != base_currency:
                graph.add_edge(Edge(source, target, log(all_rates[base_currency][target])))

    graph.print_graph()
    bellman_ford = BellmanFord(graph, "USD")
    result = bellman_ford.bellman_ford(graph, "USD")
    print(f"Result: {result}")
    print(f"Dist: {bellman_ford.dist}")
    print(f"Parent: {bellman_ford.parent}")


def create_currency_graph_with_google_scrape(currencies: List[str]) -> CurrencyGraph:
    graph = CurrencyGraph()
    all_rates = {}
    for currency_pair in itertools.product(currencies, currencies):
        if currency_pair[0] != currency_pair[1]:
            rate = scrape_google_currencies(currency_pair[0], currency_pair[1])
            all_rates[currency_pair] = float(rate)
    
    print(all_rates)
    graph.build_from_rates(all_rates)
    
    graph.print_graph()
    bellman_ford = BellmanFord(graph, "USD")
    result = bellman_ford.bellman_ford(graph, "USD")
    print(f"Result: {result}")
    print(f"Dist: {bellman_ford.dist}")
    print(f"Parent: {bellman_ford.parent}")

if __name__ == "__main__":
    currencies = {"USD", "EUR", "GBP", "CAD"}
    create_currency_graph_with_google_scrape(currencies)