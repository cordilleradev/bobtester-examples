import datetime
from pandas.core.reshape.merge import merge
from bobtester.condition import Condition
import pandas as pd
import matplotlib.pyplot as plt
from bobtester.backtest import BackTester

condition_long_condor = Condition(
    open_price=0,
    period_days=30,
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

def condor_conditional(historical_data : pd.DataFrame) -> bool:

    if historical_data.empty:
        return False

    last_row = historical_data.iloc[-1]
    print(last_row['date'])
    volatility = last_row['volatility']
    fear_and_greed = last_row['fear_and_greed']
    # Calculate 14-day RSI
    delta = historical_data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]

    support = historical_data['low'].rolling(window=30).min().iloc[-1]
    resistance = historical_data['high'].rolling(window=30).max().iloc[-1]
    return  last_row['close'] < 1.1 * support and 50 <rsi < 60



response = backtester.backtest(
    name="amrith",
    strategy_conditions=condition_bull_put_spread,
    asset="btc",
    start_position=condor_conditional,
    start_from=datetime.date.fromisoformat("2023-01-01")
)

fig1, ax = response.get_plot(
    plot_price=True,
    plot_volatility=True,
    plot_profitability=True,
    plot_fear_and_greed=True
)
print(response.return_outcome_stats())
response.export_outcome(merged_crypto_data_path="merged.csv")
try:
    plt.show()
except KeyboardInterrupt:
    pass
