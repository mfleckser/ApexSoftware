import pandas as pd
import yfinance as yf


def get_prices(ticker: str="CADUSD=X", period: str="1y"):
    # fetch data
    tkr = yf.Ticker(ticker)
    data = tkr.history(period=period).dropna()

    # clean/format data
    data = data.drop(columns=["Volume", "Dividends", "Stock Splits"])
    data.index = pd.to_datetime(data.index).date
    data.index.name = "Date"

    # save to csv
    data.to_csv("price_data.csv")


if __name__ == "__main__":
    get_prices()