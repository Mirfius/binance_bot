import math

from PyQt5.QtWidgets import QMessageBox
from binance.client import Client

import time
import datetime
def log(message):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    with open("log_bot.txt", "a") as f:
        f.write(f"{timestamp}: {message}\n")


def get_balance(client):
    try:
        balance = client.futures_account_balance()
        for i in range(0, len(balance)):
            if balance[i]['asset'] == 'USDT':
                # log(balance[i])
                depozit = float(balance[i]['withdrawAvailable'])
                break
        return depozit
    except:
        print()


def get_candle_size(klines):
    candle_sizes = []
    for candle in klines:
        open_price = float(candle[1])
        close_price = float(candle[4])
        size = abs(close_price - open_price)
        candle_sizes.append(size)
    return sum(candle_sizes) / len(candle_sizes)



def close_all_positions(client):
    try:
        # Get current open positions
        positions = client.futures_position_information(symbol='BTCUSDT')

        # Close all positions
        for position in positions:
            if float(position['positionAmt']) > 0:
                # Long position

                client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET',
                                            quantity=position['positionAmt'])
            elif float(position['positionAmt']) < 0:
                # Short position

                client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET',
                                            quantity=abs(float(position['positionAmt'])))
    except:
        print(f"Error occurred: ")

def close_all_orders_and_positions(client):
    try:
        client.futures_cancel_all_open_orders(symbol='BTCUSDT')
        print("All open orders and positions on BTCUSDT futures have been closed.")
    except :
        print(f"Error occurred while closing orders/positions: ")

def get_btc_amount(client,symbol: str, usdt_amount: float) -> float:
    ticker = client.get_ticker(symbol=symbol)
    btc_price = float(ticker['lastPrice'])
    btc_amount = usdt_amount / btc_price
    rounded_number = math.ceil(btc_amount * 1000) / 1000  # округляем до 3 знаков после запятой
    return rounded_number

def open_take_stop(client,side,position,take,stop):
    ticker = client.futures_symbol_ticker(symbol="BTCUSDT")
    current_price = float(ticker['price'])
    position = str(position)
    if side == 'BUY':
        takeprice = current_price + take
        stopprice = current_price - stop

        FuturesTakeProfit = client.futures_create_order(
            symbol='BTCUSDT',
            side='SELL',
            type='TAKE_PROFIT_MARKET',
            stopPrice=takeprice,
            closePosition=True,
            quantity=position,

        )
        FuturesStopLoss = client.futures_create_order(
            symbol='BTCUSDT',
            side='SELL',
            type='STOP_MARKET',
            stopPrice=stopprice,
            closePosition=True,
            quantity=position,

        )

    else:
        takeprice = current_price - take
        stopprice = current_price + stop
        takeprice = str(int(takeprice))
        stopprice = str(int(stopprice))

        FuturesTakeProfit = client.futures_create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='TAKE_PROFIT_MARKET',
            stopPrice=takeprice,
            closePosition=True,
            quantity=position,

        )

        FuturesStopLoss = client.futures_create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='STOP_MARKET',
            stopPrice=stopprice,
            closePosition=True,
            quantity=position,

        )

    #return FuturesTakeProfit

def open_market_order_last_candle(client,klines,proc,take,stop):

    position = get_btc_amount(client,'BTCUSDT', get_balance(client)*proc)
    if position < 0.001: position = 0.001

    # Получаем значения OHLCV последней свечи
    last_candle = klines[-2]
    open_price = float(last_candle[1])
    close_price = float(last_candle[4])

    # Определяем направление последней свечи
    if close_price >= open_price:
        side = 'SELL'
    else:
        side = 'BUY'
    # Открываем рыночный ордер
    symbol = 'BTCUSDT'

    try:
        order = client.futures_create_order(symbol='BTCUSDT', type='MARKET', side=side, quantity=position)
        if order:
            #QMessageBox.information( "фьючерс", f"{symbol}: {side} {position} исполнен")
            log( f" фьючерс {symbol}: {side} {position} исполнен\n")
    except:
        log( f" фьючерс {symbol}: {side} {position} не исполнен\n")

    try:
        order =  open_take_stop(client,side, position, take, stop)
        if order:
            #QMessageBox.information( "фьючерс", f"{symbol}: {side} {position} исполнен")
            log("фьючерс стоп и тейк исполнен\n")
    except:
        QMessageBox.warning("фьючерс стоп и тейк не исполнен")





    return order

def create_bot(api_key,api_secret, proc, t,s):
    print("bot in work")
    client = Client(api_key, api_secret)
    klines = client.futures_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "10 HOUR ago UTC")

    take = get_candle_size(klines) * t
    stop = get_candle_size(klines) * s

    # close_all_orders_and_positions()
    # close_all_positions()
    while True:
        time.sleep(1)
        now = datetime.datetime.now()
        if now.minute >= 0 and now.minute <= 59:
            try:
                close_all_orders_and_positions(client)
                close_all_positions(client)
                order = open_market_order_last_candle(client,klines, proc, take, stop)

                if order:
                    QMessageBox.information( "Bot Started", "The bot has been started successfully.")
                    log("Bot Started The bot has been started successfully.\n")


            except :
                QMessageBox.warning( "Ошибка в стратегии не исполнен")

            time.sleep(60 * 55)









