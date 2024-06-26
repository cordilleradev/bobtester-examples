import yfinance as yf
import csv
import requests
import pandas as pd
from datetime import datetime

def refresh_ohlcv_data(crypto: str, filename: str):

    if crypto not in ['btc', 'eth']:
        raise ValueError("Invalid cryptocurrency. Only 'btc' and 'eth' are supported.")

    symbol = 'BTC-USD' if crypto == 'btc' else 'ETH-USD'
    data = yf.download(symbol, period='max', interval='1d')

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'open', 'high', 'low', 'close', 'vol.'])
        for index, row in data.iterrows():
            print(index)
            writer.writerow([index.strftime('%Y-%m-%d %H:%M:%S'), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']])


def fetch_impl_volatility_data(crypto : str, filename : str):
    if crypto not in ['btc', 'eth']:
        raise ValueError("Invalid cryptocurrency. Only 'btc' and 'eth' are supported.")

    dict = {
        "eth" : "https://t3index.com/wp-content/uploads/bitvol_ETH.json",
        "btc" : "https://t3index.com/wp-content/uploads/bitvol.json"
    }

    try:
        # Fetch data from the API
        response = requests.get(dict[crypto])
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response into JSON
        data = response.json()

        # Extract the series data
        series = data['series']

        # Open the CSV file for writing
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['date', 'volatility'])

            # Write each entry to the CSV file
            for entry in series:
                date = datetime.fromtimestamp(entry[0] / 1000).strftime('%Y-%m-%d')
                volatility = entry[1]
                writer.writerow([date, volatility])

    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_fear_and_greed_data(filename: str):
    # URL to get all available historical data
    url = "https://api.alternative.me/fng/?limit=0&format=json"

    try:
        # Fetch data from the API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response into JSON
        data = response.json()

        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(data['data'])

        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='s')

        # Filter records from February 1st, 2018
        start_date = datetime(2018, 2, 1)
        df = df[df['date'] >= start_date]

        # Sort DataFrame by date
        df = df.sort_values(by='date')

        # Select relevant columns and rename if necessary
        df = df[['date', 'value']]
        df = df.rename(columns={'value': 'fear_and_greed'})
        # Saving to CSV
        df.to_csv(filename, index=False, date_format='%Y-%m-%d')

    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")







refresh_ohlcv_data("btc", "./data/bitcoin-prices.csv")
refresh_ohlcv_data("eth", "./data/ethereum-prices.csv")
fetch_fear_and_greed_data("./data/fear-and-greed-index.csv")
fetch_impl_volatility_data("btc", './data/bitcoin-volatility.csv')
fetch_impl_volatility_data("eth", './data/ethereum-volatility.csv')
