import pandas as pd
from datetime import datetime, timedelta

from get_data import get_today_calendar
from strategy import Control_Position

from news_trading import trade_on_news
from utils import log

def news_trader(initialize, countries, symbol, timeframe, risk, timezone):
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
        positions = trade_on_news(initialize=initialize,
                                  country=next_news['Country'], news=next_news['News'],
                                  symbol= symbol, timeframe=timeframe, risk=risk, time_open=now)
        
        Control_Position(initialize,  positions[0], max_pending_time=positions[0]['PendingTime'].total_seconds(),
                          max_open_time=4*60*60)
        Control_Position(initialize,  positions[1], max_pending_time=positions[1]['PendingTime'].total_seconds(),
                          max_open_time=4*60*60)
    
    # if it's news is published to 4hour return true
    if timedelta(minutes=0) <= diff_now_last_news <= timedelta(hours=4):
        news_time = True
    elif timedelta(minutes=0) <= diff_now_next_news <= timedelta(minutes=21):
        news_time = True
    else:
        news_time = False
        
    # else return false
    return (news_time, positions)


if __name__ == "__main__":
    import pytz
    
    flag, positions = news_trader(initialize= ["51810268", "apmjgjp1", "Alpari-MT5-Demo"],
                countries= ['United States'],
                symbol= 'EURUSD',
                timeframe= '4h',
                risk= 100,
                timezone= pytz.timezone('Asia/Tehran'))

    
    log(positions)

    



    



