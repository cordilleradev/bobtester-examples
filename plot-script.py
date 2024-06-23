import datetime
from pandas.core.reshape.merge import merge
from bobtester.logic.condition import Condition
import pandas as pd
import matplotlib.pyplot as plt
from bobtester.logic.backtest import BackTester



def callback(historical_data : pd.DataFrame) -> bool:
    volatility = historical_data.iloc[-1]['volatility']
    fear_and_greed = historical_data.iloc[-1]['fear_and_greed']
    print(fear_and_greed, volatility)
    return fear_and_greed < 70 and volatility < 90


condition_long_condor = Condition(
    open_price=0,
    period_days=14,
    profit_below_price_factor=0.1,
    profit_above_price_factor=0.1,
    liquidate_below_price_factor=0.2,
    liquidate_above_price_factor=0.2,
)

condition_bull_put_spread = Condition(
    open_price=0,
    period_days=7,
    profit_below_price_factor=0.025,
    liquidate_below_price_factor=0.04,
)

condition_bear_call_spread = Condition(
    open_price=0,
    period_days=7,
    profit_above_price_factor=0.025,
    liquidate_above_price_factor=0.04
)

backtester = BackTester(
    fear_and_greed_path="./data/fear-and-greed-index.csv",
    bitcoin_prices_path="./data/bitcoin-prices.csv",
    ethereum_prices_path="./data/ethereum-prices.csv",
    bitcoin_volatility_path="./data/bitcoin-volatility.csv",
    ethereum_volatility_path="./data/ethereum-volatility.csv"
)

response = backtester.backtest(
    name="amrith",
    strategy_conditions=condition_long_condor,
    asset="eth",
    start_position=callback,
    start_from=datetime.date.fromisoformat("2020-01-01")
)


response.get_plot()
plt.show()
