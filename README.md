# 📈 News Trader  

A trading bot that leverages news sentiment analysis to execute trades in financial markets. This bot processes real-time news data, analyzes sentiment, and makes automated trading decisions based on predefined strategies.  


# Troubleshoting
Here are some comment errors and solutions
## Error 1
```
File "main.py", line 69, in is_market_open
    if symbol_info.time != 0:
AttributeError: 'NoneType' object has no attribute 'time'
```
This error happens because your MetaTrader 5 is not connected to the internet, simply rescan networks or create a new account in order to get reconnected.

## Error 2
```
  File "news_trading.py", line 107, in get_extra_points
    price_mean, price_var = get_mean_var(interest_row[price_column].iloc[0], sign)
  File "pandas\core\indexing.py", line 1103, in __getitem__      
    return self._getitem_axis(maybe_callable, axis=axis)
  File "pandas\core\indexing.py", line 1656, in _getitem_axis    
    self._validate_integer(key, axis)
  File "pandas\core\indexing.py", line 1589, in _validate_integer
    raise IndexError("single positional indexer is out-of-bounds")
IndexError: single positional indexer is out-of-bounds
```
The name of the news is not in the MinMax Strategy, this is usually because of white spaces clean your excel your News column using TRIM()
