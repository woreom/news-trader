import pytz
from datetime import datetime
from datetime import timedelta
from typing import List, Callable, Dict, Tuple

import numpy as np
import pandas as pd
import MetaTrader5 as mt5
import MetaTrader5 as mt5

from get_data import get_data_from_mt5
from utils import log

__SHEET__NAME__={"USD":"United States", "JPY":"Japan", "EUR":"Euro Zone", "GER":"Germany", "GBP":"United Kingdom",
 "NZD":"New Zealand", "CAD":"Canada", "CHF":"Switzerland",}

__MULTIPLIER__VALUE__ = { 
                        'AUDJPY': 0.1, 'AUDUSD': 0.00001, 'AUDCAD':0.001, 'AUDCHF': 0.001,
                        'CADCHF': 0.001, 'CADJPY': 0.1, 'CHFJPY': 0.1, 'GBPCHF': 0.001,
                        'EURAUD': 0.001, 'EURCAD': 0.001, 'EURGBP': 0.00001,
                        'EURJPY': 0.1, 'EURNZD': 0.001, 'EURUSD': 0.00001, 'EURCHF': 0.001, 
                        'GBPAUD': 0.001 , 'GBPJPY': 0.1, 'GBPUSD':0.00001, 'GBPCAD': 0.001,
                        'GBPNZD': 0.001, 
                        'NZDCAD': 0.001, 'NZDCHF': 0.001, 'NZDJPY': 0.1, 'NZDUSD': 0.001,
                        'USDCAD': 0.001, 'USDCHF': 0.001, 'USDJPY': 0.1,
                        'XAUUSD': 0.01, 
                        }


def get_tick_size(symbol: str) -> float:
    """
    Retrieves the tick size for a given symbol.

    Args:
        symbol (str): The symbol for which to retrieve the tick size.

    Returns:
        float: The tick size of the symbol.

    Raises:
        ValueError: If the symbol is not valid or not found.
    """
    mt5.symbol_select(symbol, True)
    symbol_info = mt5.symbol_info(symbol)

    if symbol_info is None:
        raise ValueError(f"Symbol '{symbol}' is not valid or not found.")

    tick_size = symbol_info.trade_tick_size
    return tick_size
def open_calc(path: str= "static/calc.xlsx", sheetname: str= "United States"):
    calc = pd.read_excel(path, sheet_name=sheetname)
    return calc


def strtotimedate(dates: List[str], _format="%d/%m/%Y_%H:%M") -> pd.DatetimeIndex:
    '''
    Converts str datetimes to DatetimeIndex
    '''

    indexes = pd.DatetimeIndex(pd.to_datetime(dates, format=_format))

    return list(indexes)
            

def price_calc(open_, pip, multiplier):
    # log(type(open_), open_)
    # log(type(pip), pip)
    # log(type(multiplier), multiplier)

    price = round((pip*multiplier)+ open_, ndigits=4)
    return price

def isfloat(num):
    try:
        float(num.strip("[ , ]"))
        return True
    except ValueError:
        return False

def get_mean_var(string:str, sign=1):
    dirty_numbers = string.split(" ")
    # log(dirty_numbers)
    mean, var = [float(test.strip("[ , ]")) for test in dirty_numbers if isfloat(test) ]
  
    return sign*mean, sign*var
    dirty_numbers = string.split(" ")
    # log(dirty_numbers)
    mean, var = [float(test.strip("[ , ]")) for test in dirty_numbers if isfloat(test) ]
  
    return sign*mean, sign*var

def get_extra_points(df: pd.DataFrame, symbol: str, news: str, timeframe: int,
                     open_: float, time_open: pd.DatetimeIndex, multiplier: float,
                     function_over_price: Callable= lambda x: 2*x,
                     function_over_time: Callable= lambda x: x,) -> Dict[str, Tuple[pd.Timestamp]]:
    interest_row = df.loc[df["News"] == news+"_"+str(timeframe)].loc[df["Symbol"] == symbol]
    # log(interest_row.empty, end=', ')
    
    # log(news)

    positions = {"buy": {"Entry Point":None, "Estimated open position": None, "TP": None, "SL": None},
                "sell": {"Entry Point":None, "Estimated open position": None, "TP": None, "SL": None}}
    
    for position in ["buy", "sell"]:
        price_column, time_column, sign = ("Max_Open", 'Time_of_Max', 1) if position == 'sell' else ("Min_Open", 'Time_of_Min', -1)
        price_mean, price_var = get_mean_var(interest_row[price_column].iloc[0], sign)
        # log(type(open_), function_over_price(open_))

        time_mean, time_var = get_mean_var(interest_row[time_column].iloc[0])
        profit = float(interest_row["Profit"].iloc[0])
        # log(type(profit), profit)

        entry_point = price_calc(open_, function_over_price(price_mean), multiplier)
        print(f"pip {function_over_price(price_mean)}  , open {open_}, mul {multiplier}")
        # log(type(entry_point), entry_point)
        positions[position] = {'News': news, "Action": position.upper(),
                               "Currency": symbol,
                               "EntryPoint": entry_point,
                               "TakeProfit": price_calc(entry_point, function_over_price(-1*sign*profit/2), multiplier),
                               "StepLoss": price_calc(open_, function_over_price(sign*profit/2), multiplier),
                               "EntryTime": (time_open + timedelta(minutes=time_mean)),
                               "WinRate": interest_row["Win Rate"].iloc[0]}
     
    return positions

def calc_position_size(symbol, entry, sl, risk):
     
    mt5.symbol_select(symbol, True)
    symbol_info = mt5.symbol_info(symbol)
    

    tick_size = symbol_info.trade_tick_size
    tick_value = symbol_info.trade_tick_value
    
    pips_at_risk  = np.abs(entry - sl) / tick_size

    
    lot = risk / (pips_at_risk * tick_value)

    if symbol=='XAUUSD': lot/=10 
    
    return np.round(lot, 2)

def strategy(df: pd.DataFrame, symbol: str, news: str, open_: float,
             time_open: pd.DatetimeIndex, multiplier: float, timeframe: float= 4, risk: int= 100):

    # log(timeframe, end=" : ")
    positions = get_extra_points(df=df, symbol=symbol, news=news,
                                      timeframe=timeframe, open_=open_, time_open=time_open, multiplier=multiplier)
    # log()
    info = [{"News": positions['buy']["News"], "Action": "Buy", "Currency": symbol, "EntryPoint": positions['buy']["EntryPoint"],
            "TakeProfit": positions['buy']["TakeProfit"], "StepLoss": positions['buy']["StepLoss"], 
            "EntryTime": (positions['buy']["EntryTime"] + timedelta(minutes=10)).strftime("%d/%m/%Y %H:%M:%S"),
            "PendingTime": (positions['buy']["EntryTime"] - time_open),
            'RR': np.abs((positions['buy']["TakeProfit"] - positions['buy']["EntryPoint"]) / (positions['buy']["StepLoss"] - positions['buy']["EntryPoint"])),
            "WinRate": positions['buy']["WinRate"], 'PositionSize': calc_position_size(symbol, positions['buy']["EntryPoint"], positions['buy']["StepLoss"], risk),
            'Risk':risk},
            {"News": positions['sell']["News"], "Action": "Sell", "Currency": symbol, "EntryPoint": positions['sell']["EntryPoint"],
            "TakeProfit": positions['sell']["TakeProfit"], "StepLoss": positions['sell']["StepLoss"], 
            "EntryTime": (positions['sell']["EntryTime"] + timedelta(minutes=10)).strftime("%d/%m/%Y %H:%M:%S"),
            "PendingTime": (positions['sell']["EntryTime"] - time_open),
            'RR': np.abs((positions['sell']["TakeProfit"] - positions['sell']["EntryPoint"]) / (positions['sell']["StepLoss"] - positions['sell']["EntryPoint"])),
            "WinRate": positions['sell']["WinRate"], 'PositionSize': calc_position_size(symbol, positions['sell']["EntryPoint"], positions['sell']["StepLoss"], risk),
            'Risk':risk}
            ]

    return info

def trade_on_news(initialize, news, country, symbol, timeframe, risk, time_open):
    df = get_data_from_mt5(initialize, symbol, "5m")
    open_ = df.iloc[-1]["Open"]
    time_frame = {'30m':0.5,'1h': 1,'1.5h': 1.5, '2h': 2, '2.5h': 2.5, '3h': 3, '3.5h': 3.5, '4h': 4}
    calc_df = open_calc(path='static/MinMax Strategy Back Test.xlsx', sheetname=country)
    positions= strategy(df= calc_df, symbol= symbol, news=news,
                        open_= open_, time_open=time_open,
                        multiplier=get_tick_size(symbol), timeframe=time_frame[timeframe], risk=risk)
    return positions


    