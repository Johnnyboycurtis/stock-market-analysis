import pandas as pd
pd.set_option('display.max_columns', None)

import datetime as dt
import yfinance as yf



def load_ticker_symbols(filename = "stock-list.txt"):
    with open(filename) as openfile:
        data = []
        for line in openfile:
            data.append(line.strip())
    return data


def query_stock_prices(tickers, start_date=None, end_date=None):
    if end_date is None:
        end_date = dt.datetime.now().date() + dt.timedelta(days=1)
    if start_date is None:
        start_date = end_date - dt.timedelta(days=200)

    prices = yf.download(tickers, start_date, end_date)['Close']
    return prices


def demo():
    print("Running Tutorial -- Fetching VOO")
    # Define a start date and End Date
    start = dt.datetime(2023, 10,1)
    end =  dt.datetime(2024,1,5)

    # Read Stock Price Data 
    voo_df = yf.download(['VOO'], start , end)

    print(voo_df.tail(10))

    voo_path = "data/voo-stock-price.csv"
    voo_df.to_csv(voo_path)
    print(f"Saved results to {voo_path}")


