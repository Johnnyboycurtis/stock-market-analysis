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



class DollarCostAveraging:
    """
    Very basic buy and hold strategy Dollar Cost Averaging
    Buy and just hold
    Will always return True on decision
    """
    def __init__(self, symbol: str, monies: [int,float], income: [int,float] = None) -> None:
        self.symbol = symbol.upper()
        self.holdings = Holdings()
        self.monies = monies
        self.income = income
        self.total_monies = monies
    
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
    
    def run(self, data: [pd.DataFrame, pd.Series], date_column = 'Date'):
        if isinstance(data, pd.Series):
            data = data.to_frame(self.symbol).reset_index() # index is ideally the date
        else:
            data = data.reset_index(drop=True)

        if self.income:
            dates = data[date_column]
            income_dates = dates.groupby(by = [dates.dt.year, dates.dt.month]).max()
            self.contributions = pd.DataFrame(0, columns = ['contributions', 'available_funds'], index=dates)
            self.contributions.iloc[0] = self.monies
            self.contributions.loc[income_dates, 'contributions'] = self.income
        
        for i, row in tqdm(data.iterrows()):
            curr_date = row[date_column]
            curr_price = row[self.symbol]
            if self.income:
                idx = (curr_date == income_dates).any()
                if idx:
                    self.monies += self.income
                    self.total_monies += self.income

            if i == 0:
                self.start_price = curr_price
                self.start_date = curr_date
            # log available funds at the start of the day before purchases
            self.contributions.loc[curr_date, 'available_funds'] = self.monies
            buy, quantity = self.decision(row) # decision to purchase, and how much
            if buy:
                self.monies = self.add_position(price=curr_price, date=curr_date, quantity=quantity) # returns remaining funds
        self.end_price = curr_price
        self.end_date = curr_date

        self.performance = {"gains": self.end_price  - self.start_price, 
                            "gains %": round(self.end_price/self.start_price, 5) - 1}
        
        return None





class DollarCostAveragingBuyDrawdown:
    """
    Dollar Cost Averaging with buy the drawdown strategy

    The strategy looks for when stock prices drop below the 50-day average
    
    """
    def __init__(self, symbol: str, monies: [int,float], income: [int,float] = None) -> None:
        self.symbol = symbol.upper()
        self.holdings = Holdings()
        self.monies = monies
        self.income = income
        self.total_monies = monies
    
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
            return True, quantity #min(quantity, 4)
        
        elif ratio < 0:
            return True, min(quantity, 2)
    
        elif ratio < 3:
            # on average, I want to only buy one or two shares once a week
            # so we'll reduce chances to only buy once a week
            # using random() < 0.2
            return random() < 0.2, min(quantity, 2)
        
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
    
    def run(self, data: [pd.DataFrame, pd.Series], date_column = 'Date'):
        if isinstance(data, pd.Series):
            data = data.to_frame(self.symbol).reset_index() # index is ideally the date
        else:
            data = data.reset_index(drop=True)
        
        if self.income:
            dates = data[date_column]
            # I should be using pd.Grouper(freq="M")
            income_dates = dates.groupby(by = [dates.dt.year, dates.dt.month]).max()
            self.contributions = pd.DataFrame(0, columns = ['contributions', 'available_funds'], index=dates)
            self.contributions.iloc[0] = self.monies
            self.contributions.loc[income_dates, 'contributions'] = self.income
        
        for i, row in tqdm(data.iterrows()):
            curr_date = row[date_column]
            curr_price = row[self.symbol]

            if self.income and (curr_date == income_dates).any():
                self.monies += self.income
                self.total_monies += self.income

            if i == 0:
                self.start_price = curr_price
                self.start_date = curr_date
            # log available funds at the start of the day before purchases
            self.contributions.loc[curr_date, 'available_funds'] = self.monies
            buy, quantity = self.decision(row) # decision to purchase, and how much
            if buy:
                self.monies = self.add_position(price=curr_price, date=curr_date, quantity=quantity)
        self.end_price = curr_price
        self.end_date = curr_date
        self.performance = None # place holder

        return None




