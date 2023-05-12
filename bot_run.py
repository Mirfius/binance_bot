import math
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPalette, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton
from PyQt5.QtWidgets import*
from binance.client import Client

import threading
from multiprocessing import Process, freeze_support
import requests

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox
from binance.client import Client

import math

from PyQt5.QtWidgets import QMessageBox
from binance.client import Client

import time
import datetime

"""
логи
"""
def log(message):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as f:
        f.write(f"{timestamp}: {message}\n")


"""
запрашиваем баланс фьючерсного аккаунта в долларах
"""
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

"""
вычисляет среднее арифметическое размера свечей
нужно для стопов и тейков
"""
def get_candle_size(klines):
    candle_sizes = []
    for candle in klines:
        open_price = float(candle[1])
        close_price = float(candle[4])
        size = abs(close_price - open_price)
        candle_sizes.append(size)
    return sum(candle_sizes) / len(candle_sizes)


"""
закрывает все открытые позиции путем выставления противоположных
если было куплено 0.001 битка на фьючерсах, то продает 0.001
"""
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
"""
закрывает все ордера (ордер это пока не открытая позиция)

в нашем случае закрывает ранее открытые стопы и тейки
"""
def close_all_orders_and_positions(client):
    try:
        client.futures_cancel_all_open_orders(symbol='BTCUSDT')
        print("All open orders and positions on BTCUSDT futures have been closed.")
    except :
        print(f"Error occurred while closing orders/positions: ")

"""
вычисляет колво битка по колву долларов
"""
def get_btc_amount1(client,symbol: str, usdt_amount: float) -> float:
    ticker = client.get_ticker(symbol=symbol)
    btc_price = float(ticker['lastPrice'])
    btc_amount = usdt_amount / btc_price
    rounded_number = math.ceil(btc_amount * 1000) / 1000  # округляем до 3 знаков после запятой
    return rounded_number
"""
открывает стопы и тейки для открытой позиции


"""
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

"""
открывает саму нашу позицию
"""

def open_market_order_last_candle(client,klines,proc,take,stop):
    """
    вычисляем объем битка
    """

    position = get_btc_amount1(client,'BTCUSDT', get_balance(client)*proc)
    if position < 0.001: position = 0.001

    """
    смотрим на последнюю свечу, не считая текущей
    """
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
    """
    открываем ордер
    """
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


"""
основная функция, принимает api, процент риска и коэфы для стопов и тейков
"""
def create_bot(api_key,api_secret, proc, t,s):
    print("bot in work")
    """
    инициация связи с биржей
    """
    client = Client(api_key, api_secret)
    """
    запрос инфы по 10 часовым свечам
    """
    klines = client.futures_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "10 HOUR ago UTC")
    """
    вычисление стопов и тейков
    """
    take = get_candle_size(klines) * t
    stop = get_candle_size(klines) * s

    # close_all_orders_and_positions()
    # close_all_positions()
    time.sleep(1)
    now = datetime.datetime.now()
    """
    бот открывает сделку в начале каждого часа а потом спит
    """
    if now.minute >= 0 and now.minute <= 61:
        try:
            """
            закрываем ордера и позиции
            """
            close_all_orders_and_positions(client)
            close_all_positions(client)
            """
            открываем новый ордер
            """
            order = open_market_order_last_candle(client, klines, proc, take, stop)

            if order:
                QMessageBox.information("Bot Started", "The bot has been started successfully.")
                log("Bot Started The bot has been started successfully.\n")


        except:
            QMessageBox.warning("Ошибка в стратегии не исполнен")
    while False:
        time.sleep(1)
        now = datetime.datetime.now()
        """
        бот открывает сделку в начале каждого часа а потом спит
        """
        if now.minute >= 0 and now.minute <= 61:
            try:
                """
                закрываем ордера и позиции
                """
                close_all_orders_and_positions(client)
                close_all_positions(client)
                """
                открываем новый ордер
                """
                order = open_market_order_last_candle(client,klines, proc, take, stop)

                if order:
                    QMessageBox.information( "Bot Started", "The bot has been started successfully.")
                    log("Bot Started The bot has been started successfully.\n")


            except :
                QMessageBox.warning( "Ошибка в стратегии не исполнен")

            time.sleep(60 * 55)











#with open('API.txt') as f:
with open('API.txt') as f:
    keys = {}
    for line in f:
        key, value = line.strip().split(':')
        keys[key] = value
api_key = keys['api_key']
api_secret = keys['api_secret']
client = Client(api_key, api_secret)


client = Client(api_key, api_secret)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 750, 500)
        self.setWindowTitle('Binance Trading Bot')

        self.setWindowIcon(QIcon('bac2.jpg'))

        # Create tab widget and add tabs
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_tab0(), "Инфо")
        tab_widget.addTab(self.create_tab2(), "Получить цену")
        tab_widget.addTab(self.create_tab1(), "Маркет")
        tab_widget.addTab(self.create_tab4(), "Лимит")
        tab_widget.addTab(self.create_tab3(), "Стратегия")
        tab_widget.addTab(self.create_tab5(), "Деньги")




        # Set central widget to the tab widget
        self.setCentralWidget(tab_widget)

        self.show()

    def create_tab0(self):
        # Create widget for Tab 0
        tab0 = QWidget()

        # Add background image
        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab0)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        # Create labels with information
        title = QLabel("Binance Trading Bot", tab0)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(150, 10, title.sizeHint().width(),title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)


        description = QLabel("Это бот который позволяет торговать на бирже бинанс\n"
                             "Для начала работы введите свой бинанс API в файл\n"
                             "Вы можете купить крипту или запустить прибыльную стратегию\n"
                             "Будьте осторожны\n", tab0)

        description.adjustSize()
        #description.setAlignment(Qt.AlignCenter)
        description.setFont(QFont("Arial", 12))
        description.setGeometry(50, 80, description.sizeHint().width(), description.sizeHint().height())



        description2 = QLabel("Мы будем рады получить от вас благодарность\n"
                             "Сбер: 5469400023229615\n"
                             "Bitcoin: 1JUzVi9ZMEd238vurfQ4FW9MvrAcFp9ion\n"
                             "BNB Smart Chain (BER20): 0x1490608ec546fb8f62b87802e8613eb3b9bf4064\n", tab0)

        description2.adjustSize()
        # description.setAlignment(Qt.AlignCenter)
        description2.setFont(QFont("Arial", 12))
        description2.setGeometry(50, 200, description2.sizeHint().width(), description2.sizeHint().height())


        author = QLabel("Created by Sivov Andrey, Rudneva Dariya, Korneev Aleksandr", tab0)
        author.setGeometry(50, 330, 600, 20)


        version = QLabel("Version 1.0", tab0)
        version.setGeometry(50, 350, 200, 20)
        return tab0

    def create_tab1(self):
        # Create widget for Tab 1
        tab1 = QWidget()

        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab1)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        title = QLabel("Рыночные ордера", tab1)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(150, 10, title.sizeHint().width()+150, title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)



        # Create label for "Select action:"
        self.label1 = QLabel('Select action:', tab1)
        self.label1.setGeometry(20, 20, 100, 20)

        # Create combobox for selecting action
        self.actionCombo = QComboBox(tab1)
        self.actionCombo.addItem("Buy")
        self.actionCombo.addItem("Sell")
        self.actionCombo.setGeometry(20, 40, 100, 20)

        # Create label for "Select currency:"
        self.label2 = QLabel('Select currency:', tab1)
        self.label2.setGeometry(20, 70, 100, 20)

        # Create combobox for selecting currency
        self.currencyCombo = QComboBox(tab1)
        self.fill_currency_combo()
        self.currencyCombo.setGeometry(20, 90, 100, 20)
        self.currencyCombo.activated.connect(self.update_usdt_or_btc)

        # Create label for "Enter the amount:"
        self.label3 = QLabel('Enter the amount:', tab1)
        self.label3.setGeometry(20, 120, 100, 20)

        # Create line edit for entering the amount
        self.edit = QLineEdit(tab1)
        self.edit.setGeometry(20, 140, 100, 20)

        # Create label for "in:"
        self.label4 = QLabel('in:', tab1)
        self.label4.setGeometry(130, 140, 20, 20)

        # Create combobox for selecting USDT or BTC
        self.usdt_or_btc = QComboBox(tab1)
        self.fill_usdt_or_btc()
        self.usdt_or_btc.setGeometry(150, 140, 100, 20)

        # Create button for executing the trade
        self.button = QPushButton('Execute', tab1)
        self.button.setGeometry(20, 170, 100, 20)
        self.button.clicked.connect(self.execute_trade)

        # Set the layout for the widget
        tab1.setLayout(QVBoxLayout())

        return tab1



    def fill_currency_combo(self):
        popular_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'UNI', 'SOL', 'LTC']
        for currency in popular_currencies:
            self.currencyCombo.addItem(currency)

    def fill_usdt_or_btc(self):
        self.usdt_or_btc.addItem("USDT")
        self.usdt_or_btc.addItem("BTC")

    def update_usdt_or_btc(self):
        self.usdt_or_btc.clear()
        self.usdt_or_btc.addItem("USDT")
        selected_currency = self.currencyCombo.currentText()
        self.usdt_or_btc.addItem(selected_currency)

    def get_btc_amount(self,symbol: str, usdt_amount: float) -> float:
        ticker = client.get_ticker(symbol=symbol)
        btc_price = float(ticker['lastPrice'])
        btc_amount = usdt_amount / btc_price
        rounded_number = math.ceil(btc_amount * 1000) / 1000  # округляем до 3 знаков после запятой
        return rounded_number


    def market_order(self, symbol, side, quantity):
        print("order  ",symbol, side, quantity)
        """
        Sells or buys a given quantity of a given symbol on the market at the current market price.
        :param symbol: The trading symbol (e.g. 'BTCUSDT')
        :param side: The direction of the trade (e.g. 'BUY' or 'SELL')
        :param quantity: The quantity of the symbol to trade (e.g. 0.1)
        :return: The resulting order object
        """

        if quantity <= 0:
            raise ValueError("Invalid quantity. Must be positive.")


        try:
            order =1
            order = client.order_market_buy(symbol=symbol,quantity=quantity) if side == 'buy' else client.order_market_sell(symbol=symbol, quantity=quantity)
            if order:
                log(f"{symbol}: {side} {quantity} успешно исполнен\n")
                QMessageBox.information(self, "исполнено", f"{symbol}: {side} {quantity} исполнен")
        except:
            log(f"{symbol}: {side} {quantity} не исполнен\n")
            QMessageBox.warning(self, "Ошибка", f"{symbol}: {side} {quantity} не исполнен")

        #order = client.order_market_buy(symbol=symbol, quantity=quantity) if side == 'buy' else client.order_market_sell(symbol=symbol, quantity=quantity)

        #return order

    def execute_trade(self):
        try:
            action = self.actionCombo.currentText().lower()
            currency = self.currencyCombo.currentText()
            currency += "USDT"
            chose_currency = self.usdt_or_btc.currentText().lower()
            amount = self.edit.text()
            amount = float(amount)
            if chose_currency == "usdt":
                amount = self.get_btc_amount(currency, amount)
            self.market_order(currency, action, amount)
            self.update_usdt_or_btc()
        except:
            log(f"ошибка в запросе ордера\n")
            QMessageBox.warning(self, "Ошибка", f"ошибка в запросе ордера")


    def create_tab2(self):
        tab2 = QWidget()

        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab2)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        title = QLabel("Получить актуальную цену", tab2)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(100, 10, title.sizeHint().width() , title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)

        # Create label for "Select currency:"
        self.labelt2 = QLabel('Select currency:', tab2)
        self.labelt2.setGeometry(20, 70, 100, 20)

        # создаем виджет для выбора криптовалюты
        self.currencyCombot2 = QComboBox(tab2)
        self.fill_currency_combot2()
        self.currencyCombot2.setGeometry(20, 90, 100, 20)

        # добавьте другие криптовалюты по вашему желанию



        # Create button for executing the trade
        self.buttont2 = QPushButton('Получить', tab2)
        self.buttont2.setGeometry(20, 120, 100, 20)
        self.buttont2.clicked.connect(self.execute_t2)

        self.amount_field = QLineEdit(tab2)
        self.amount_field.setGeometry(20, 150, 250, 20)

        # устанавливаем созданный макет на вторую вкладку
        tab2.setLayout(QVBoxLayout())
        return tab2

    def fill_currency_combot2(self):
        popular_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'UNI', 'SOL', 'LTC']
        for currency in popular_currencies:
            self.currencyCombot2.addItem(currency)
    def get_current_price(self, symbol):
        # получаем данные о текущей цене выбранной криптовалюты

        ticker = client.get_ticker(symbol=symbol)
        price = ticker['lastPrice']

        # выводим текущую цену на метке
        self.amount_field.setText(f"Текущая цена: {price} USDT")

    def execute_t2(self):
        try:

            currency = self.currencyCombot2.currentText()
            currency += "USDT"
            self.get_current_price(currency)


        except:
            log(f"ошибка в запросе ордера\n")
            QMessageBox.warning(self, "Ошибка", f"ошибка в запросе ордера")

    def create_tab4(self):
        # Create widget for Tab 1
        tab4 = QWidget()

        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab4)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        title = QLabel("Лимитные ордера", tab4)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(150, 10, title.sizeHint().width() + 150, title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)

        # Create label for "Select action:"
        self.labelt41 = QLabel('Select action:', tab4)
        self.labelt41.setGeometry(20, 20, 100, 20)

        # Create combobox for selecting action
        self.actionCombot4 = QComboBox(tab4)
        self.actionCombot4.addItem("Buy")
        self.actionCombot4.addItem("Sell")
        self.actionCombot4.setGeometry(20, 40, 100, 20)

        # Create label for "Select currency:"
        self.label2 = QLabel('Select currency:', tab4)
        self.label2.setGeometry(20, 70, 100, 20)

        # Create combobox for selecting currency
        self.currencyCombo = QComboBox(tab4)
        self.fill_currency_combo()
        self.currencyCombo.setGeometry(20, 90, 100, 20)
        self.currencyCombo.activated.connect(self.update_usdt_or_btc2)

        self.label5 = QLabel('price:', tab4)
        self.label5.setGeometry(20, 120, 100, 20)

        # Create line edit for entering the amount
        self.edit42 = QLineEdit(tab4)
        self.edit42.setGeometry(20, 140, 100, 20)

        # Create label for "Enter the amount:"
        self.label3 = QLabel('Enter the amount:', tab4)
        self.label3.setGeometry(20, 170, 100, 20)

        # Create line edit for entering the amount
        self.edit41 = QLineEdit(tab4)
        self.edit41.setGeometry(20, 190, 100, 20)



        # Create label for "in:"
        self.label4 = QLabel('in:', tab4)
        self.label4.setGeometry(130, 190, 20, 20)

        # Create combobox for selecting USDT or BTC
        self.usdt_or_btc = QComboBox(tab4)
        self.fill_usdt_or_btc()
        self.usdt_or_btc.setGeometry(150, 190, 100, 20)

        # Create button for executing the trade
        self.button = QPushButton('Execute', tab4)
        self.button.setGeometry(20, 240, 100, 20)
        self.button.clicked.connect(self.execute_trade2)

        # Set the layout for the widget
        tab4.setLayout(QVBoxLayout())

        return tab4



    def fill_currency_combo2(self):
        popular_currencies = ['BTC', 'ETH', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT', 'UNI', 'SOL', 'LTC']
        for currency in popular_currencies:
            self.currencyCombo.addItem(currency)

    def fill_usdt_or_btc2(self):
        self.usdt_or_btc.addItem("USDT")
        self.usdt_or_btc.addItem("BTC")

    def update_usdt_or_btc2(self):
        self.usdt_or_btc.clear()
        self.usdt_or_btc.addItem("USDT")
        selected_currency = self.currencyCombo.currentText()
        self.usdt_or_btc.addItem(selected_currency)



    def get_btc_amount2(self,symbol: str, usdt_amount: float) -> float:
        ticker = client.get_ticker(symbol=symbol)
        btc_price = float(ticker['lastPrice'])
        btc_amount = usdt_amount / btc_price
        rounded_number = math.ceil(btc_amount * 1000) / 1000  # округляем до 3 знаков после запятой
        return rounded_number

    def get_price(self,symbol: str) -> float:
        ticker = client.get_ticker(symbol=symbol)
        btc_price = float(ticker['lastPrice'])

        return btc_price


    def market_order2(self, symbol, side, quantity,price):
        print("order  ",symbol, side, quantity, price)
        if quantity <= 0:
            raise ValueError("Invalid quantity. Must be positive.")
        try:
            order =1
            order = client.order_limit_buy(symbol=symbol,quantity=quantity, price=str(price)) if side == 'buy' else client.order_limit_sell(symbol=symbol, quantity=quantity , price=str(price))
            if order:
                log(f"{symbol}: {side} {quantity} {price} успешно исполнен\n")
                QMessageBox.information(self, "исполнено", f"{symbol}: {side} {quantity} {price} исполнен")
        except:
            log(f"{symbol}: {side} {quantity} {price} не исполнен\n")
            QMessageBox.warning(self, "Ошибка", f"{symbol}: {side} {quantity} {price} не исполнен")

        #order = client.order_market_buy(symbol=symbol, quantity=quantity) if side == 'buy' else client.order_market_sell(symbol=symbol, quantity=quantity)

        #return order

    def execute_trade2(self):
        try:
            action = self.actionCombot4.currentText().lower()
            currency = self.currencyCombo.currentText()
            currency += "USDT"
            chose_currency = self.usdt_or_btc.currentText().lower()
            amount = float(self.edit41.text())
            if chose_currency == "usdt":
                amount = self.get_btc_amount2(currency, amount)


            price= self.edit42.text()

            # Check if user input is valid
            try:
                # Convert input values to floats
                price = float(price)
                now_price =self.get_price(currency)


                # Check if input values are within valid ranges
                if action =="buy" and price > now_price:
                    raise ValueError("Неправильная цена покупки")
                if action =="sell" and price < now_price:
                    raise ValueError("Неправильная цена продажи")
                self.market_order2(currency, action, amount, price)
                self.update_usdt_or_btc2()
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))

        except:
            log(f"ошибка в запросе ордера\n")
            QMessageBox.warning(self, "Ошибка", f"ошибка в запросе ордера")



    def create_tab3(self):
        # Create widget for Tab 3
        tab3 = QWidget()
        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab3)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        title = QLabel("Торговый бот", tab3)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(450, 10, title.sizeHint().width() , title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)

        label = QLabel(tab3)
        pixmap = QPixmap('bac4.png')
        label.setPixmap(pixmap)
        label.setGeometry(450, 50, pixmap.width(), pixmap.height())


        # Create labels for user inputs
        risk_label = QLabel('Risk Percentage (0.01-1):', tab3)
        risk_label.setGeometry(20, 20, 200, 20)
        tp_label = QLabel('Take Profit (0.1-5):', tab3)
        tp_label.setGeometry(20, 60, 200, 20)
        sl_label = QLabel('Stop Loss (0.1-5):', tab3)
        sl_label.setGeometry(20, 100, 200, 20)

        # Create line edits for user inputs
        self.risk_input = QLineEdit(tab3)
        self.risk_input.setGeometry(200, 20, 100, 20)
        self.tp_input = QLineEdit(tab3)
        self.tp_input.setGeometry(200, 60, 100, 20)
        self.sl_input = QLineEdit(tab3)
        self.sl_input.setGeometry(200, 100, 100, 20)

        # Create button for starting the bot
        start_button = QPushButton('Start Bot', tab3)
        start_button.setGeometry(20, 140, 100, 30)

        # Connect button to function that starts the bot
        start_button.clicked.connect(self.start_bot)

        description2 = QLabel("Бот работает, открывая сделки каждый час\n"
                              "не выключайте программу\n"
                              "вибирайте разумный риск (% от депа)\n"
                              "удачи!!!\n", tab3)

        description2.adjustSize()
        # description.setAlignment(Qt.AlignCenter)
        description2.setFont(QFont("Arial", 12))
        description2.setGeometry(20, 200, description2.sizeHint().width(), description2.sizeHint().height())

        return tab3

    def start_bot(self):
        # Get user input from Tab 3
        risk_percent = self.risk_input.text()
        take_profit = self.tp_input.text()
        stop_loss = self.sl_input.text()

        # Check if user input is valid
        try:
            # Convert input values to floats
            risk_percent = float(risk_percent)
            take_profit = float(take_profit)
            stop_loss = float(stop_loss)

            # Check if input values are within valid ranges
            if risk_percent < 0.01 or risk_percent > 1.0:
                raise ValueError("Risk percentage must be between 0.01 and 1.0")
            if take_profit < 0.1 or take_profit > 5.0:
                raise ValueError("Take profit must be between 0.1 and 5.0")
            if stop_loss < 0.1 or stop_loss > 5.0:
                raise ValueError("Stop loss must be between 0.1 and 5.0")


            QMessageBox.information(self, "Bot Started", "The bot has been started successfully.")


            # создаем новый поток для запуска функции my_function
            #create_bot(api_key,api_secret, risk_percent, take_profit,stop_loss)

            #freeze_support()
            #print("Processes started")
            #p = Process(target=create_bot, args=(api_key,api_secret, risk_percent, take_profit,stop_loss))
            #p.start()
            #print("Processes ended")
            try:
                create_bot(api_key,api_secret, risk_percent, take_profit,stop_loss)
            except:
                print("бот не запустился")


        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def create_tab5(self):
        # Create widget for Tab 0
        tab5 = QWidget()

        # Add background image
        background = QPixmap("bac1.jpg")
        background_label = QLabel(tab5)
        background_label.setPixmap(background)
        background_label.resize(background.width(), background.height())

        # Create labels with information
        title = QLabel("Хотите получить больше прибыли?", tab5)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.adjustSize()
        title.setGeometry(150, 10, title.sizeHint().width(),title.sizeHint().height())
        title.setAlignment(Qt.AlignCenter)


        description = QLabel("И так, вы уже убедились в качественной работе нашего бота\n"
                             "Хотите начать зарабатывать на binans?\n"
                             "Наша команда готова вам помочь\n"
                             "Просто свяжитесь с нашим специалистом\n", tab5)

        description.adjustSize()

        description.setFont(QFont("Arial", 12))
        description.setGeometry(50, 80, description.sizeHint().width(), description.sizeHint().height())



        description2 = QLabel("email: matrixsiv2@yandex.ru\n"
                             "Telegram: @morfius_21\n", tab5)

        description2.adjustSize()
        # description.setAlignment(Qt.AlignCenter)
        description2.setFont(QFont("Arial", 12))
        description2.setGeometry(50, 200, description2.sizeHint().width(), description2.sizeHint().height())


        author = QLabel("Не упусти свой шанс!!!!!!!", tab5)
        author.setGeometry(50, 330, 600, 20)

        return tab5



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())