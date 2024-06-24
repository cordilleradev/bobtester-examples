import datetime
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd
from bobtester.backtest import BackTester
from bobtester.condition import Condition

# Setup basic logging configuration
logging.basicConfig(filename='backtest_errors.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# BackTester instance with preloaded data
b = BackTester(
    fear_and_greed_path="./data/fear-and-greed-index.csv",
    bitcoin_prices_path="./data/bitcoin-prices.csv",
    ethereum_prices_path="./data/ethereum-prices.csv",
    bitcoin_volatility_path="./data/bitcoin-volatility.csv",
    ethereum_volatility_path="./data/ethereum-volatility.csv"
)

# Define the condition for the strategy
condition_long_condor = Condition(
    open_price=158.43,
    period_days=14,
    profit_below_price_factor=0.1,
    profit_above_price_factor=0.1,
    liquidate_below_price_factor=0.2,
    liquidate_above_price_factor=0.2,
)

class CallbackManager:
    def __init__(self, vol: float, fear_and_greed: float) -> None:
        self.vol = vol
        self.fear_and_greed = fear_and_greed

    def callback(self, df: pd.DataFrame) -> bool:
        if df.empty:
            return False
        volatility = df.iloc[-1]['volatility']
        fear = df.iloc[-1]['fear_and_greed']
        return volatility < self.vol and fear < self.fear_and_greed

def backtest_and_return_stats(vol, fear_and_greed, asset):
    manager = CallbackManager(vol, fear_and_greed)
    try:
        response = b.backtest(
            name="googus",
            strategy_conditions=condition_long_condor,
            asset=asset,
            start_position=manager.callback,
            start_from=datetime.date.fromisoformat("2020-01-01")
        )
        stats = response.return_outcome_stats()
        stats['volatility'] = vol
        stats['fear_and_greed'] = fear_and_greed
        stats['asset'] = asset
        return stats
    except Exception as e:
        logging.error(f"Error in backtest vol={vol}, fear_and_greed={fear_and_greed}, asset={asset}: {str(e)}", exc_info=True)
        return {"error": str(e), "volatility": vol, "fear_and_greed": fear_and_greed, "asset": asset}

def run_backtest(asset, fg_bounds, vol_bounds, filename):
    # Create a list of (vol, fear_and_greed, asset) tuples for the specified ranges
    combinations = [(vol, fg, asset) for vol in range(vol_bounds[0], vol_bounds[1] + 1) for fg in range(fg_bounds[0], fg_bounds[1] + 1)]

    # Execute backtests across different volatility, fear_and_greed indices, and assets
    outcomes = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(backtest_and_return_stats, vol, fg, asset) for vol, fg, asset in combinations]
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                result = future.result()
                if "error" not in result:
                    outcomes.append(result)
                else:
                    logging.error(f"Failed backtest logged with details: vol={result['volatility']}, fear_and_greed={result['fear_and_greed']}, asset={result['asset']}: {result['error']}")
            except Exception as e:
                logging.error(f"Exception while retrieving result: {e}", exc_info=True)

    df = pd.DataFrame(outcomes)

    # Save the DataFrame to a CSV file
    df.to_csv(filename, index=False)

if __name__ == "__main__":
# Example usage
    run_backtest(
        asset="btc",
        fg_bounds=(5, 95),
        vol_bounds=(36, 191),
        filename='btc_outcomes.csv'
    )

    run_backtest(
        asset="eth",
        fg_bounds=(5,95),
        vol_bounds=(34,217),
        filename="eth_outcomes.csv"
    )
