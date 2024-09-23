import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class Fund:
    # quantities are USD if not specified, prices are USD/CAD
    def __init__(self, investment: float=500000):
        self.cash_usd = investment
        self.starting_capital = investment
        self.assets_cad = 0
        self.position_limit = 0.05
        self.loss_limit = 0.1


    def simulate(self, data: pd.DataFrame):
        shorting = False
        trading = True
        total_capital = []
        short_avgs = []
        long_avgs = []
        sell_dates = []
        buy_dates = []
        wins = 0
        
        dates = data["Date"]

        for date in dates:
            short_moving_avg, long_moving_avg = self.get_moving_averages(data, date)
            short_avgs.append(short_moving_avg)
            long_avgs.append(long_moving_avg)
            close_price = data[data["Date"] == date]["Close"].mean()

            if not self.at_loss_threshold(close_price) and trading:
                if not shorting and short_moving_avg > long_moving_avg:
                    quan = self.get_max_buy(close_price)
                    shorting = self.buy(quan, close_price)
                    buy_dates.append(date)
                    print(f"Trade: BUY {quan} at ${close_price:.2f} USD/CAD on {date}")
                elif shorting and short_moving_avg < long_moving_avg:
                    quan = self.assets_cad * close_price
                    shorting = not self.sell(quan, close_price)
                    sell_dates.append(date)

                    dif = close_price - data[data["Date"] == buy_dates[-1]]["Close"].mean()
                    if dif > 0:
                        wins += 100
                    print(f"Trade: SELL {quan} at ${close_price:.2f} USD/CAD on {date}")
            else:
                print(f"Exceeded loss threshold on {date}")
                trading = False

            total_capital.append(self.capital(close_price))

        # Sell remaining assets
        date = dates[len(data) - 1]
        close_price = data[data["Date"] == date]["Close"].mean()
        self.sell(self.assets_cad * close_price, close_price)
        dif = close_price - data[data["Date"] == buy_dates[-1]]["Close"].mean()
        if dif > 0:
            wins += 100
        print(f"Trade: SELL {quan} at ${close_price:.2f} USD/CAD on {date}")
        
        #Output results
        closing_balance = self.cash_usd
        print("\n\n---- Backtesting Summary ----")
        print(f"Initial Investment: ${self.starting_capital:.2f}, Closing Account Balance: ${closing_balance:.2f}")
        print(f"Total Profit/Loss: ${(closing_balance - self.starting_capital):.2f}")
        print(f"Total Trades: {len(buy_dates)}")
        print(f"Winning Percentage: {wins / len(buy_dates):.2f}%")
        print(f"Sharpe Ratio: {self.calc_sharpe_ratio((closing_balance - self.starting_capital) / self.starting_capital, np.std(total_capital)):.5f}")

        # Plotting
        fig, (ax1, ax2) = plt.subplots(2, 1)

        # Change the tick interval
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=30)) 
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=30)) 

        # Puts x-axis labels on an angle
        ax1.xaxis.set_tick_params(rotation = 30) 
        ax2.xaxis.set_tick_params(rotation = 30) 

        ax1.plot(dates, total_capital, label="Account Balance")
        ax1.plot(dates, np.full(data["Date"].shape, self.starting_capital), ":", label="Starting Equity")

        ax2.plot(dates, data["Close"], label="Closing Price")
        ax2.plot(dates, short_avgs, label="Short Term Moving Average")
        ax2.plot(dates, long_avgs, label="Long Term Moving Average")

        bottom, top = ax2.get_ylim()
        ax2.vlines(x=sell_dates, ymin=bottom, ymax=top, color="b", label="Sales")
        ax2.vlines(x=buy_dates, ymin=bottom, ymax=top, color="r", label="Buys")

        fig.autofmt_xdate()
        ax1.set_xlim([dates[0], dates[len(data) - 1]])
        ax2.set_xlim([dates[0], dates[len(data) - 1]])

        ax1.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.subplots_adjust(right=0.7)
        plt.show()


    def buy(self, quantity: float, price: float) -> bool:
        can_afford = quantity <= self.cash_usd
        exceeds_position_limit = self.assets_cad * price + quantity > (self.position_limit * self.capital(price))

        if not can_afford or exceeds_position_limit:
            return False

        self.cash_usd -= quantity
        self.assets_cad += quantity / price
        return True

    def sell(self, quantity: float, price: float) -> bool:
        can_afford = quantity / price <= self.assets_cad

        if not can_afford:
            return False

        self.cash_usd += quantity
        self.assets_cad -= quantity / price
        return True

    def capital(self, price: float) -> float:
        return self.assets_cad * price + self.cash_usd
    
    def get_max_buy(self, price: float) -> float:
        return self.position_limit * self.capital(price) - self.assets_cad * price

    def at_loss_threshold(self, price: float) -> bool:
        return self.capital(price) < self.starting_capital * (1 - self.loss_limit)
    
    def calc_sharpe_ratio(self, asset_return, stdev_asset_return) -> float:
        # All rates as of Sept. 19th 2024, the last day of data
        # in price_data.csv

        bond_rate = 0.0393
        inflation_rate = 0.025
        risk_free_rate = (1 + bond_rate) / (1 + inflation_rate)
        return (asset_return - risk_free_rate) / stdev_asset_return


    @staticmethod
    def get_moving_averages(data: pd.DataFrame, date: str, price_col: str="Close") -> tuple[float, float]:
        date_index = data[data["Date"] == date].index[0]

        short_term_start = max(date_index - 20, 0)
        long_term_start = max(date_index - 50, 0)

        short_term_prices = data[price_col][short_term_start:date_index]
        long_term_prices = data[price_col][long_term_start:date_index]

        return (short_term_prices.mean(), long_term_prices.mean())
