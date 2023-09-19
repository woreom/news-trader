from time import sleep
from turtle import pos
import pandas as pd
from datetime import datetime, timedelta

from get_data import get_today_calendar
from strategy import Control_Position

import MetaTrader5 as mt5

from news_trading import trade_on_news, trade_i_positions_on_news
from utils import log

def news_trader(initialize, countries, symbol, timeframe, risk, timezone, num_positions=3):
    news_time = False
    positions = ()
    now = pd.Timestamp('today', tzinfo=timezone).replace(tzinfo=None)
    df = get_today_calendar(countries=countries, timezone=timezone)
    
    # get df from now
    next_news = df[df["Date_Time"] > now].iloc[0]
    news_index = df[df["Date_Time"] > now].index[0]
    
    # if it's 5min before new, place position
    diff_now_next_news = datetime.strptime(str(next_news["Date_Time"]), "%Y-%m-%d %H:%M:%S") - now.replace(tzinfo=None)
    diff_now_last_news = now.replace(tzinfo=None) - datetime.strptime(str(df["Date_Time"].iloc[news_index-1]), "%Y-%m-%d %H:%M:%S")

    if timedelta(minutes=0) <= diff_now_next_news <= timedelta(minutes=5):
        news_time = True
        log(f"country={next_news['Country']}, news={next_news['News']}, symbol= {symbol}, timeframe={timeframe}")
        
        # positions = trade_on_news(initialize=initialize,
        #                           country=next_news['Country'], news=next_news['News'],
        #                           symbol= symbol, timeframe=timeframe, risk=risk, time_open=now)
        
        positions = trade_i_positions_on_news(initialize=initialize,
                                  country=next_news['Country'], news=next_news['News'],
                                  num_positions= num_positions, risk=risk, time_open=now)
        
        for position in positions:
            Control_Position(initialize,  position[0], max_pending_time=position[0]['PendingTime'],
                            max_open_time=4*60*60)
            Control_Position(initialize,  position[1], max_pending_time=position[1]['PendingTime'],
                            max_open_time=4*60*60)
    
    # if it's news is published to 4hour return true
    # if timedelta(minutes=0) <= diff_now_last_news <= timedelta(hours=4):
    #     news_time = True
    # elif timedelta(minutes=0) <= diff_now_next_news <= timedelta(minutes=21):
    #     news_time = True
    else:
        news_time = False
        
    # else return false
    return (news_time, positions)

def is_market_open():
    mt5.initialize()
    mt5.login(login="51545562", password="zop7gsit", 
              server="Alpari-MT5-Demo")

    # get the symbol you want to check
    symbol = "EURUSD"

    # get the symbol info
    symbol_info = mt5.symbol_info(symbol)

    # check if the market is open for the symbol
    if symbol_info.time != 0:
        return True
    else:
        return False

    # shut down the connection to the MetaTrader 5 terminal
    mt5.shutdown()

def run_bot(all_countries=['United States'], symbol=None, timeframe=None, risk=100, num_positions=3):
    message = "Starting Bot ..."
    log(message)
    timezone = pytz.timezone('Asia/Tehran')

    while is_market_open():
        flag, positions = news_trader(initialize= ["51810268", "apmjgjp1", "Alpari-MT5-Demo"],
                countries= all_countries,
                symbol= symbol,
                timeframe= timeframe,
                risk= risk,
                timezone= timezone,
                num_positions= num_positions)
        # if positions != (): log(flag, positions)
        log(flag, positions)
        sleep(30)
        if flag: sleep(5*60)  

    
       
if __name__ == "__main__":
    import pytz
    
    ########## test a news right now ##########
    # flag, positions = news_trader(initialize= ["51810268", "apmjgjp1", "Alpari-MT5-Demo"],
    #             countries= ['United States'],
    #             symbol= 'EURUSD',
    #             timeframe= '4h',
    #             risk= 100,
    #             timezone= pytz.timezone('Asia/Tehran'))

    # log(positions)

    ########### test a positions #############
    # trade_on_news(initialize= ["51810268", "apmjgjp1", "Alpari-MT5-Demo"],
    #               country='United States', news='OPEC Crude Oil Production Guinea',
    #               symbol= None, timeframe=None, risk=100, time_open=0)
    
    ############ test a random news ##############
    # from news_trading import open_calc, strategy, get_tick_size
    # open_ = 0
    # risk = 100
    # time_open = datetime.now()
    # country='United States'
    # news='Dallas Fed PCE'
    # time_frame = {'30m':0.5,'1h': 1,'1.5h': 1.5, '2h': 2, '2.5h': 2.5, '3h': 3, '3.5h': 3.5, '4h': 4,
    #               '0.5':0.5, '1': 1, "1.5": 1.5, '2': 2, "2.5": 2.5, "3": 3, "3.5": 3.5, "4": 4}
    # calc_df = open_calc(path='static/MinMax Strategy Back Test.xlsx', sheetname=country)
    
    # mt5.initialize()
    # mt5.login(login="51545562", password="zop7gsit", 
    #           server="Alpari-MT5-Demo")

    # interest_rows = calc_df[calc_df['News'].str.contains(news)]
    # interest_rows.sort_values(by=['Win Rate'], ascending = False, inplace=True)
    # symbol = interest_rows["Symbol"].iloc[0]
    # timeframe = interest_rows["News"].iloc[0].split("_")[-1]
    # log(f"best symbol and timeframe by winrate: {symbol} and {timeframe}")

    # positions= strategy(df= calc_df, symbol= symbol, news=news,
    #                     open_= open_, time_open=time_open,
    #                     multiplier=get_tick_size(symbol), timeframe=time_frame[timeframe], risk=risk)
    # log(positions)

    ##### Run the bot for a day #####
    run_bot(all_countries=['United States', 'United Kingdom', 'Euro Zone',
                           'Germany', 'Switzerland', 'Canada', 
                           'Australia', 'Japan', 'New Zealand', 'China'],
                           symbol=None, timeframe=None, risk=100, num_positions=3)

    



    



