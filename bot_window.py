import math
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPalette, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton
from PyQt5.QtWidgets import*
from binance.client import Client
from bot_final import*
import threading

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox
from binance.client import Client

#with open('API.txt') as f:
with open('API_2.txt') as f:
    keys = {}
    for line in f:
        key, value = line.strip().split(':')
        keys[key] = value
api_key = keys['api_key']
api_secret = keys['api_secret']
client = Client(api_key, api_secret)


client = Client(api_key, api_secret)

def log(message):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as f:
        f.write(f"{timestamp}: {message}\n")

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

        tab_widget.addTab(self.create_tab1(), "Маркет")
        tab_widget.addTab(self.create_tab4(), "Лимит")
        tab_widget.addTab(self.create_tab3(), "Стратегия")




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
        # Create widget for Tab 2
        tab2 = QWidget()

        # Add widgets and layout for Tab 2 as desired

        return tab2

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
        self.label1 = QLabel('Select action:', tab4)
        self.label1.setGeometry(20, 20, 100, 20)

        # Create combobox for selecting action
        self.actionCombo = QComboBox(tab4)
        self.actionCombo.addItem("Buy")
        self.actionCombo.addItem("Sell")
        self.actionCombo.setGeometry(20, 40, 100, 20)

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
            action = self.actionCombo.currentText().lower()
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
        pixmap = QPixmap('bac3.jpg')
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
            thread = threading.Thread(target=create_bot(api_key,api_secret, risk_percent, take_profit,stop_loss))
            thread.start()


        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())