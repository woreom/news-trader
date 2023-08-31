## Import Libraries
from time import sleep
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

def Open_Position(trade_info):
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


    # Calculate the minimum distance between the entry price and take profit
    min_distance = np.abs(tp - entry) / 3

    # Get the current bid/ask price depending on the trade action
    if action == "Sell":
        price = mt5.symbol_info_tick(symbol).ask
    else:
        price = mt5.symbol_info_tick(symbol).bid

    # Check if the current price is within the minimum distance of the entry price
    # price < entry + min_distance and price > entry -min_distance
    if False:
        
        # Create a market order
        order_type = {'Buy': mt5.ORDER_TYPE_BUY, 'Sell': mt5.ORDER_TYPE_SELL}
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type[action],
            "price": price,
            "sl": sl,  
            "tp": tp
        }
        
    else:
        # Create a pending order
        if price > entry + min_distance:
            order_type = {"Buy": mt5.ORDER_TYPE_BUY_LIMIT, "Sell": mt5.ORDER_TYPE_SELL_STOP}
        else:
            order_type = {"Buy": mt5.ORDER_TYPE_BUY_STOP, "Sell": mt5.ORDER_TYPE_SELL_LIMIT}
            
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot,
            "type": order_type[action],
            "price": entry,
            "sl": sl,  
            "tp": tp
        }
        
    # Send the pending order to the trading server
    trade = mt5.order_send(request)
    log(trade)
    # Return information about the trade order
    return trade, request


def Close_Position(trade_order, request, action, symbol, sleep_time):
    """
    Close or remove a position in MetaTrader 5.
    
    trade_order: int, the ticket number of the trade to close or remove
    request: dict, the trade request object returned by mt5.orders_get() for the trade
    action: str, 'Close' to close the trade or 'Remove' to remove the trade
    symbol: str, the symbol of the currency pair for the trade
    sleep_time: int, the number of seconds to wait before executing the trade action
    
    """
        
    sleep(sleep_time)
    if action=='Close':
        result=mt5.Close(symbol=symbol,ticket=trade_order)
    if action=='Remove':
        if mt5.order_check(request).profit==np.double(0):
            result=mt5.order_send({"order": trade_order, "action": mt5.TRADE_ACTION_REMOVE})
        else: result=None
    log(result)
    return result


def Control_Position(initialize,  trade_info, max_pending_time=2*60, max_open_time=20*60):
    
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
    trade, request=Open_Position(trade_info)
    
    if request["action"]==mt5.TRADE_ACTION_PENDING:
        t1 = threading.Thread(target=Close_Position, args=(trade.order, request, 'Remove', trade_info['Currency'], max_pending_time))
        t1.start()
    
    t1 = threading.Thread(target=Close_Position, args=(trade.order, request,'Close', trade_info['Currency'], max_open_time))
    t1.start()
    


