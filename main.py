import os
import time
import ccxt
import ta
import pandas as pd

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PAIR = os.getenv("PAIR", "DOGE5L/USDT")
STAKE_AMOUNT = float(os.getenv("STAKE_AMOUNT", "100"))
PROFIT_TARGET = float(os.getenv("PROFIT_TARGET", "0.04"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

exchange = ccxt.gate({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

def fetch_data():
    ohlcv = exchange.fetch_ohlcv(PAIR, timeframe='5m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def add_indicators(df):
    df['EMA9'] = ta.trend.ema_indicator(df['close'], window=9)
    df['EMA21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    return df

def check_signals(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    buy = (
        prev['EMA9'] < prev['EMA21'] and
        last['EMA9'] > last['EMA21'] and
        last['RSI'] > 50
    )
    sell = (
        prev['EMA9'] > prev['EMA21'] and
        last['EMA9'] < last['EMA21']
    )
    return buy, sell

def place_order(side):
    if DRY_RUN:
        print(f"[DRY RUN] Would place {side} order for {STAKE_AMOUNT} {PAIR}")
        return
    order = exchange.create_market_order(PAIR, side, STAKE_AMOUNT)
    print(f"{side.upper()} order placed:", order)

def main():
    bought_price = None
    while True:
        try:
            df = fetch_data()
            df = add_indicators(df)
            buy, sell = check_signals(df)

            ticker = exchange.fetch_ticker(PAIR)
            current_price = ticker['last']

            if buy and not bought_price:
                place_order('buy')
                bought_price = current_price

            elif bought_price:
                gain = (current_price - bought_price) / bought_price
                if gain >= PROFIT_TARGET or sell:
                    place_order('sell')
                    bought_price = None

            print(f"[{PAIR}] Price: {current_price}, Bought at: {bought_price}")
            time.sleep(60)

        except Exception as e:
            print("Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()
