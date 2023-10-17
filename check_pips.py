from news_trading import get_tick_size
import MetaTrader5 as mt5

mt5.initialize()
mt5.login(login="51834380", password="4wsirwes", 
            server="Alpari-MT5-Demo")

MULTIPLIER = { 
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


#[print(mt5.symbol_select(symbol, True)) for symbol in MULTIPLIER.keys()]
# print(MULTIPLIER.keys())
new_mult = {symbol:get_tick_size(symbol) for symbol in MULTIPLIER.keys()}
print(new_mult)

#get_tick_size('AUDUSD')

