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

def callback(historical_data : pd.DataFrame) -> bool:
    if historical_data.empty:
        return False

    if len(historical_data) < 14:
        return False

    last_row = historical_data.iloc[-1]
    iroc_vol = historical_data['volatility'].pct_change().iloc[-1]

    return  30 < last_row['rsi'] < 70

response = backtester.backtest(
    name="amrith",
    strategy_conditions=condition_long_condor,
    asset="eth",
    start_position=callback,
    start_from=datetime.date.fromisoformat("2023-01-01")
)

print(response.return_outcome_stats())
response.export_outcome(merged_crypto_data_path="merged.csv")
response.get_plot()
try:
    plt.show()
except KeyboardInterrupt:
    pass
