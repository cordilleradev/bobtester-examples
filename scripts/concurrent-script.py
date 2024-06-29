import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Callable
import pandas as pd
import gspread
from itertools import product
import time
import os
from bobtester.backtest import BackTester
from bobtester.condition import Condition
import json

# Define the trading condition using the Condition class
condition_long_condor = Condition(
    open_price=0,
    period_days=14,
    profit_below_price_factor=0.13,
    profit_above_price_factor=0.13,
    liquidate_below_price_factor=0.23,
    liquidate_above_price_factor=0.23,
)

# Set up the BackTester with paths to relevant CSV files
backtester = BackTester(
    fear_and_greed_path="./data/fear-and-greed-index.csv",
    bitcoin_prices_path="./data/bitcoin-prices.csv",
    ethereum_prices_path="./data/ethereum-prices.csv",
    bitcoin_volatility_path="./data/bitcoin-volatility.csv",
    ethereum_volatility_path="./data/ethereum-volatility.csv"
)

# Function to generate combinations of parameters
def generate_combinations(*ranges: tuple[int, int]) -> list[tuple[int, ...]]:
    return list(product(*[range(r[0], r[1]) for r in ranges]))

# Define parameter ranges
fear_and_greed_range = (5, 95)
eth_volatility = (36, 218)

# Callback function to provide as start condition for the backtest
def callback(fng_val: int, vol_val: int) -> Callable[[pd.DataFrame], bool]:
    def check_conditions(df: pd.DataFrame) -> bool:
        if df.empty:
            return False

        return (
            df['fear_and_greed'].iloc[-1] > fng_val and
            df['volatility'].iloc[-1] < vol_val
        )
    return check_conditions

# Function to run a backtest with given parameters
def run_backtest(fear_index: int, vol_index: int):
    return backtester.backtest(
        f"fng: {fear_index} - vol: {vol_index}",
        strategy_conditions=condition_long_condor,
        asset="eth",
        start_position=callback(fear_index, vol_index),
        start_from=datetime.date.fromisoformat("2020-01-01")
    )

gc_key = os.getenv('SPREADSHEET_KEY')
gc_service = os.getenv("SERVICE_JSON")
worksheet_name = os.getenv("WORKSHEET_NAME")

if not gc_key or not gc_service or not worksheet_name:
    raise ValueError("Missing environment variables for Google Sheets integration.")


if __name__ == '__main__':
    gc = gspread.service_account_from_dict(info=json.loads(gc_service))
    sh = gc.open_by_key(gc_key)
    worksheet = sh.worksheet(worksheet_name)

    def update_loading_bar(worksheet, completed_iterations, total_iterations):
        percent_complete = (completed_iterations / total_iterations) * 100
        loading_bar = "#" * int(percent_complete // 2) + "-" * (50 - int(percent_complete // 2))
        loading_message = f"Loading: [{loading_bar}] {percent_complete:.2f}%"
        worksheet.update(values=[[loading_message]], range_name='A1')

    def batch_append_rows(worksheet, rows):
        if rows:
            worksheet.append_rows(rows)
            return True
        return False

    worksheet.update(values=[["Loading: 0/0 iterations completed"]], range_name='A1')
    worksheet.update(values=[["fear_and_greed", "volatility", "percent_profitable", "total_positions", "percent_liquidated", "percent_unprofitable"]], range_name='A2')

    combinations = generate_combinations(fear_and_greed_range, eth_volatility)
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_backtest, fear_index, vol_index): (fear_index, vol_index) for fear_index, vol_index in combinations}
        total_jobs = len(futures)
        completed_jobs = 0
        batch_rows = []
        last_update_time = time.time()

        for future in as_completed(futures):
            fear_index, vol_index = futures[future]
            try:
                result = future.result()
                stats = result.return_outcome_stats()
                print(stats)
                if stats['total_positions'] > 100:
                    row = [
                        fear_index,
                        vol_index,
                        stats["percent_profitable"],
                        stats["total_positions"],
                        stats["percent_liquidated"],
                        stats["percent_unprofitable"]
                    ]
                    batch_rows.append(row)

            except Exception as e:
                print(f"Error processing combination (fng: {fear_index}, vol: {vol_index}): {e}")

            completed_jobs += 1
            current_time = time.time()
            if current_time - last_update_time > 10 or completed_jobs == total_jobs:
                if batch_append_rows(worksheet, batch_rows):
                    update_loading_bar(worksheet, completed_jobs, total_jobs)
                batch_rows = []
                last_update_time = current_time

        if batch_append_rows(worksheet, batch_rows):
            update_loading_bar(worksheet, total_jobs, total_jobs)
