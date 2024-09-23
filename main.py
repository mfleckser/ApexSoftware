import pandas as pd

import fund


if __name__ == "__main__":
    data = pd.read_csv("price_data.csv")

    apex = fund.Fund()
    apex.simulate(data)
