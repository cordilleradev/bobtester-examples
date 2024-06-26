import datetime
from pandas.core.reshape.merge import merge
from bobtester.condition import Condition
import pandas as pd
import matplotlib.pyplot as plt
from bobtester.backtest import BackTester

condition_long_condor = Condition(
    open_price=0,
    period_days=14,
    profit_below_price_factor=0.13,
    profit_above_price_factor=0.13,
    liquidate_below_price_factor=0.23,
    liquidate_above_price_factor=0.23,
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

def callback2(h : pd.DataFrame) -> bool: return True
def callback1(historical_data : pd.DataFrame) -> bool:
    if historical_data.empty:
        return False

    if len(historical_data) < 14:
        return False


    return True


response = backtester.backtest(
    name="amrith",
    strategy_conditions=condition_long_condor,
    asset="btc",
    start_position=callback1,
    start_from=datetime.date.fromisoformat("2020-01-01")
)

fig1, ax = response.get_plot(
    plot_price=False,
    plot_volatility=False,
    plot_profitability=True,
    plot_fear_and_greed=False
)
print(response.return_outcome_stats())

try:
    plt.show()
except KeyboardInterrupt:
    pass
