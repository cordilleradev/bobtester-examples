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

global_rsi = []
global_macd = []
global_bollinger_upper = []
global_bollinger_lower = []
global_stochastic_k = []
global_atr = []

def callback2(h : pd.DataFrame) -> bool: return True
def callback1(historical_data : pd.DataFrame) -> bool:
    if historical_data.empty:
        return False

    if len(historical_data) < 14:
        return False

    # Calculate RSI
    delta = historical_data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Calculate MACD
    ema_12 = historical_data['close'].ewm(span=12, adjust=False).mean()
    ema_26 = historical_data['close'].ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_histogram = macd - signal

    # Calculate Bollinger Bands
    sma = historical_data['close'].rolling(window=20).mean()
    std = historical_data['close'].rolling(window=20).std()
    bollinger_upper = sma + (std * 2)
    bollinger_lower = sma - (std * 2)

        # Calculate Stochastic Oscillator
    low_14 = historical_data['low'].rolling(window=14).min()
    high_14 = historical_data['high'].rolling(window=14).max()
    stochastic_k = 100 * ((historical_data['close'] - low_14) / (high_14 - low_14))

        # Calculate Average True Range (ATR)
    high_low = historical_data['high'] - historical_data['low']
    high_close = (historical_data['high'] - historical_data['close'].shift()).abs()
    low_close = (historical_data['low'] - historical_data['close'].shift()).abs()
    true_range = high_low.combine(high_close, max).combine(low_close, max)
    atr = true_range.rolling(window=14).mean()

    last_date = historical_data.iloc[-1]['date']

    global_rsi.append((last_date, rsi.iloc[-1]))
    global_macd.append((last_date, macd_histogram.iloc[-1]))
    global_bollinger_upper.append((last_date, bollinger_upper.iloc[-1]))
    global_bollinger_lower.append((last_date, bollinger_lower.iloc[-1]))
    global_stochastic_k.append((last_date, stochastic_k.iloc[-1]))
    global_atr.append((last_date, atr.iloc[-1]))

    oversold_rsi = 30
    overbought_rsi = 70
    macd_increase = macd_histogram.iloc[-1] > macd_histogram.iloc[-2]
    macd_decrease = macd_histogram.iloc[-1] < macd_histogram.iloc[-2]
    near_lower_band = (historical_data['close'].iloc[-1] < bollinger_lower.iloc[-1] * 1.05)
    near_upper_band = (historical_data['close'].iloc[-1] > bollinger_upper.iloc[-1] * 0.95)
    stochastic_low = stochastic_k.iloc[-1] < 20
    stochastic_high = stochastic_k.iloc[-1] > 80
    atr_high = atr.iloc[-1] > atr.mean()  # Consider high volatility

    # Example strategy based on the conditions
    if (rsi.iloc[-1] < oversold_rsi and macd_increase and near_lower_band) or (stochastic_low and atr_high):
        print(f"Buy signal on {last_date}")
        return True  # Adjust return value based on your strategy needs

    if (rsi.iloc[-1] > overbought_rsi and macd_decrease and near_upper_band) or (stochastic_high and atr_high):
        print(f"Sell signal on {last_date}")
        return False  # Adjust return value based on your strategy needs

    # If no conditions are met, you might want to hold or perform no action
    return False  # Default action


response = backtester.backtest(
    name="amrith",
    strategy_conditions=condition_long_condor,
    asset="eth",
    start_position=callback1,
    start_from=datetime.date.fromisoformat("2022-01-01")
)

fig1, ax = response.get_plot(
    plot_price=True,
    plot_volatility=False,
    plot_profitability=True,
    plot_fear_and_greed=False
)

print(response.return_outcome_stats())
# # Plotting the new indicators on the figure
# ax_rsi = fig1.add_subplot(511)
# ax_macd = fig1.add_subplot(512)
# ax_bollinger = fig1.add_subplot(513)
# ax_stochastic = fig1.add_subplot(514)
# ax_atr = fig1.add_subplot(515)

# # RSI
# rsi_dates, rsi_values = zip(*global_rsi)
# ax_rsi.plot(rsi_dates, rsi_values, label='RSI')
# ax_rsi.set_title('RSI')
# ax_rsi.legend()

# # MACD Histogram
# macd_dates, macd_values = zip(*global_macd)
# ax_macd.plot(macd_dates, macd_values, label='MACD Histogram')
# ax_macd.set_title('MACD Histogram')
# ax_macd.legend()

# # Bollinger Bands
# bollinger_upper_dates, bollinger_upper_values = zip(*global_bollinger_upper)
# bollinger_lower_dates, bollinger_lower_values = zip(*global_bollinger_lower)
# ax_bollinger.plot(bollinger_upper_dates, bollinger_upper_values, label='Bollinger Upper Band')
# ax_bollinger.plot(bollinger_lower_dates, bollinger_lower_values, label='Bollinger Lower Band')
# ax_bollinger.set_title('Bollinger Bands')
# ax_bollinger.legend()

# # Stochastic Oscillator
# stochastic_dates, stochastic_values = zip(*global_stochastic_k)
# ax_stochastic.plot(stochastic_dates, stochastic_values, label='%K')
# ax_stochastic.set_title('Stochastic Oscillator')
# ax_stochastic.legend()

# # ATR
# atr_dates, atr_values = zip(*global_atr)
# ax_atr.plot(atr_dates, atr_values, label='ATR')
# ax_atr.set_title('Average True Range')
# ax_atr.legend()

# fig1.tight_layout()
# # Writing the date + indicator values to a CSV file
# indicator_data = pd.DataFrame({
#     'date': rsi_dates,
#     'rsi': rsi_values,
#     'macd_histogram': macd_values,
#     'bollinger_upper': bollinger_upper_values,
#     'bollinger_lower': bollinger_lower_values,
#     'stochastic_k': stochastic_values,
#     'atr': atr_values
# })

# indicator_data = indicator_data.dropna()
# indicator_data.to_csv('indicator_values.csv', index=False)
# response.export_outcome(merged_crypto_data_path="merged.csv")

try:
    plt.show()
except KeyboardInterrupt:
    pass
