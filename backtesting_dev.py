import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from random import random
from tqdm import tqdm


class Position:
    def __init__(self, symbol: str, price: float, quantity: int, date: datetime.date) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.date = date

    def to_dict(self):
        return {'symbol': self.symbol, 'price': self.price, 'quantity': self.quantity, 'date': self.date}
    
    def __repr__(self) -> str:
        return f"[{self.symbol}] {self.quantity} @ price {self.price:.2f}"



class Holdings:
    def __init__(self, positions=None) -> None:
        if positions:
            self.positions = list(positions)
        else:
            self.positions = []

    def add_position(self, positions):
        if isinstance(positions, list):
            self.positions.extend(positions)
        else:
            self.positions.append(positions)

    def to_pandas(self):
        data = [pos.to_dict() for pos in self.positions]
        return pd.DataFrame(data)
    
    def __repr__(self) -> str:
        holdings_dict = {}
        for pos in self.positions:
            count = 0
            if pos.symbol in holdings_dict:
                count = holdings_dict[pos.symbol]
            count += 1
            holdings_dict[pos.symbol] = count
            
        return str(holdings_dict)



class BuyAndHoldStrategySignal:
    """
    Very basic buy and hold strategy
    Buy and just hold
    Will always return True on decision
    """
    def __init__(self, symbol: str, monies: [int,float], income = '') -> None:
        self.symbol = symbol.upper()
        self.holdings = Holdings()
        self.monies = monies
    
    def decision(self, data):
        # buy and hold strategy
        price = data[self.symbol]
        quantity = self.monies // price
        _buy = self.monies > price
        return _buy, quantity
    
    def add_position(self, price, date, quantity, monies=None):
        if not monies:
            monies = self.monies
        remainder = monies - (price*quantity)
        if quantity:
            position = Position(self.symbol, price=price, quantity=quantity, date=date)
            self.holdings.add_position(positions=[position])
        return remainder
    
    def run(self, data, date_column = 'Date'):
        if isinstance(data, pd.Series):
            data = data.to_frame(self.symbol).reset_index() # index is ideally the date
        
        for i, row in tqdm(data.iterrows()):
            curr_date = row[date_column]
            curr_price = row[self.symbol]
            if i == 0:
                self.start_price = curr_price
                self.start_date = curr_date
            buy, quantity = self.decision(row)
            if buy:
                self.monies = self.add_position(price=curr_price, date=curr_date, quantity=quantity) # returns remaining funds
        self.end_price = curr_price
        self.end_date = curr_date

        self.performance = {"gains": self.end_price  - self.start_price, 
                            "gains %": round(self.end_price/self.start_price, 5) - 1}
        
        return None





class BuyAndHoldDrawDownStrategySignal:
    def __init__(self, symbol: str, monies: [int,float]) -> None:
        self.symbol = symbol.upper()
        self.holdings = Holdings()
        self.monies = monies
    
    def decision(self, data):
        # features should be a dataframe
        price = data[self.symbol]
        ma_price = data['sma_50']
        monies = self.monies

        ratio = 100*(price / ma_price - 1) # if below 0 buy tons
        quantity = monies//price

        if not len(self.holdings.positions):
            return True, 10


        if ratio < -5:
            return True, min(quantity, 4)
        
        elif ratio < 0:
            return True, min(quantity, 2)
    
        elif ratio < 3:
            return random() < 0.2, min(quantity, 1)
        
        else:
            return False, 0
        
    
    def add_position(self, price, date, quantity, monies=None):
        if not monies:
            monies = self.monies
        remainder = monies - (price*quantity)
        if quantity:
            position = Position(self.symbol, price=price, quantity=quantity, date=date)
            self.holdings.add_position(positions=[position])
        return remainder
    
    def run(self, data, date_column = 'Date'):
        if isinstance(data, pd.Series):
            data = data.to_frame(self.symbol).reset_index() # index is ideally the date
        
        for i, row in tqdm(data.iterrows()):
            date = row[date_column]
            price = row[self.symbol]
            if i == 0:
                self.start_price = price
                self.start_date = date
            buy, quantity = self.decision(row)
            if buy:
                self.monies = self.add_position(price=price, date=date, quantity=quantity)
        self.end_price = price
        self.end_date = date
        self.performance = None # place holder

        return None




