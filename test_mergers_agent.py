# test_mergers.py

from mergers_agent import get_mergers_table

if __name__ == "__main__":
    market = "Plastic Market in the US"
    timeframe = "2018–2022"  # You can also try "last 5 years", "2020 to 2024", etc.

    markdown_table = get_mergers_table(market, timeframe)
    print(markdown_table)
