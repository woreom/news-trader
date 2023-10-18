## Import Libraries
import time
import pytz
from time import sleep
from datetime import datetime, timedelta
from get_data import current_time
import threading

import numpy as np
                   
import MetaTrader5 as mt5

from utils import log

def PositionSize(symbol, entry, sl, risk):
    """
     Calculate the position size based on the given trade parameters.
    
    Parameters:
    symbol: A string representing the currency symbol for which to calculate the position size.
    entry: A float representing the trade entry price.
    sl: A float representing the trade stop loss price.
    risk: A float representing the maximum amount of capital to risk in the account's base currency.
    
    Returns:
    A float representing the position size in lots.
    
    The function first selects the given symbol using `mt5.symbol_select()`,
    and retrieves the trade tick size and value information using `mt5.symbol_info()`.
    The function then retrieves the current tick information for the symbol using `mt5.symbol_info_tick()`,
    and calculates the minimum allowed distance as 5 times the tick size. 
    The function then calculates the number of ticks at risk based on the entry price and stop loss price,
    and calculates the position size in lots based on the maximum amount of capital to risk in the account's base currency.
    
    the function returns the calculated position size in lots as a float, rounded to two decimal places.
    
    Examples:
    # Calculate the position size for a trade with EURUSD
    symbol = 'EURUSD'
    entry = 1.2345
    sl = 1.2300
    risk = 1000  # Maximum amount of capital to risk is $1000
    position_size = PositionSize(symbol, entry, sl, risk)
     """
     
     
    mt5.symbol_select(symbol, True)
    symbol_info = mt5.symbol_info(symbol)
    

    tick_size = symbol_info.trade_tick_size
    tick_value = symbol_info.trade_tick_value
    
    pips_at_risk  = np.abs(entry - sl) / tick_size

    
    lot = risk / (pips_at_risk * tick_value)
    
    if symbol=='XAUUSD': lot/=10 
    
    if lot < symbol_info.volume_min : lot=symbol_info.volume_min
    elif lot > symbol_info.volume_max : lot=symbol_info.volume_max

    return np.round(lot, 2)

def Open_Position(trade_info, max_pending_time):
    """
    This function takes a dictionary with trade information,
    including the entry point, take profit, step loss, position size, currency name and action
    (buy or sell), and creates a market order or a pending order to open a position
    in the specified financial instrument.
    
    Args:
    trade_info (dict): A dictionary containing trade information, including the
    entry point, take profit, step loss, position size,currency name and action (buy or sell).
    
    Returns:
    dict: A dictionary containing information about the trade order, including the
    order ticket number, trade operation (buy or sell), and trade result (successful
    or unsuccessful).
    """
    # Retrieve the number of digits for the currency pair being traded
    symbol=trade_info['Currency']
    digit = mt5.symbol_info(symbol).digits

    # Round the trade parameters to the number of digits of the currency pair being traded
    entry = np.round(trade_info['EntryPoint'], digit)
    tp = np.round(trade_info['TakeProfit'], digit)
    sl = np.round(trade_info['StepLoss'], digit)
    action = trade_info['Action']
    lot = np.double(trade_info['PositionSize'])
    #trade_info["PendingTime"]
    expiration =  int((current_time() + timedelta(seconds=max_pending_time)).timestamp())

    order_type = {"Buy": mt5.ORDER_TYPE_BUY_LIMIT, "Sell": mt5.ORDER_TYPE_SELL_LIMIT}
    
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": order_type[action],
        "price": entry,
        "sl": sl,  
        "tp": tp,
        "type_time": mt5.ORDER_TIME_SPECIFIED,
        "expiration": expiration,
        "type_filling":mt5.ORDER_FILLING_IOC,
        "comment": f"{trade_info['News'][:3]},{trade_info['TimeFrame']},{round(trade_info['WinRate']*100, ndigits=2)}",
    }
    
    # Send the pending order to the trading server
    counter = 0
    class dummy():
        order=0
    trade= dummy()
    while trade.order == 0 and counter<=40:
        trade = mt5.order_send(request)
        #print trade retcode
        # if trade.retcode != mt5.TRADE_RETCODE_DONE:
        #     print("2. order_send failed, retcode={}".format(trade.retcode))
        sleep(1)
        counter+=1
    log(f'opend position: {trade.order}')
    # Return information about the trade order
    return trade, request


def Close_Position(trade_order, symbol, sleep_time):
    """
    Close or remove a position in MetaTrader 5.
    
    trade_order: int, the ticket number of the trade to close or remove
    request: dict, the trade request object returned by mt5.orders_get() for the trade
    action: str, 'Close' to close the trade or 'Remove' to remove the trade
    symbol: str, the symbol of the currency pair for the trade
    sleep_time: int, the number of seconds to wait before executing the trade action
    
    """

    sleep(sleep_time)
    counter = 0
    result = False
    while not result and counter<=40:
        result=mt5.Close(symbol=symbol,ticket=int(trade_order))
        result=mt5.order_send({"order": trade_order, "action": mt5.TRADE_ACTION_REMOVE})
        sleep(10)
        counter+=1

    log(f'closed position: {trade_order}')
    return result

def Control_Position(initialize, trade_info, max_pending_time, max_open_time):
    
    """
    Control the lifecycle of a position in MetaTrader 5.
    
    initialize: list, contains login, password, and server information to connect to the MT5 terminal
    trade_info: dict, contains information for the trade to open, including currency pair, trade direction, 
    lot size, stop loss, and take profit
    max_pending_time: int, the maximum time in seconds to wait for a pending order to execute
    max_open_time: int, the maximum time in seconds to keep an open trade before closing it

    """
    # Initialization
    mt5.initialize()
    mt5.login(login=initialize[0],password=initialize[1],server=initialize[2])
    
    # Open Position
    trade, request=Open_Position(trade_info=trade_info, max_pending_time=max_pending_time)
    # if request["action"]==mt5.TRADE_ACTION_PENDING:
    #     log(f"Order {trade.order} is pending for {max_pending_time}")
    #     t1 = threading.Thread(target=Close_Position, args=(trade.order, request, 'Remove', trade_info['Currency'], max_pending_time))
    #     t1.start()
    t1 = threading.Thread(target=Close_Position, args=(trade.order, trade_info['Currency'], max_open_time))
    t1.start()
    # return trade.order
    


