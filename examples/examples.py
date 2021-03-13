import elektra
import pandas as pd
import filecmp
import datetime as dt

flow_date = dt.datetime(2020, 10, 17)

### Create Prices (make a daily from lmps)
print('\n\n--- Create Block Prices ---')
prices = pd.read_csv('lmps.csv')

result = elektra.create_prices(flow_date, 'M.P4F8', 'INDIANA.HUB', 'miso', '2x16', 'daily', prices)
print(result)

#### Scrub Hourly Prices (make sure there are enough houlies)
print('\n\n--- Scrub Hourly Prices ---')
result = elektra.scrub_hourly_prices(flow_date,'M.YERX', '116013753', 'pjm', prices)
print(result)

### Convert 
print('\n\n--- Convert Blocks ---')
result = elektra.convert(flow_date, '7x24', '2x16') # 16: (October 17 2020 is a Saturday, and has 16 peak hours)
print(result)

result = elektra.convert(flow_date, '7x24', '5x16') # 0: (October 17 2020 is a Saturday, and has 0 weekday peak hours)
print(result)

result = elektra.convert(flow_date, '5x16', '2x16') # 0: (October 17 2020 is a Saturday, and there could not be a 5x16 input block)
print(result)

### Translate Blocks
print('\n\n--- Translate Blocks ---')
flow_date = dt.datetime(2020, 10, 1)
result = elektra.translateBlocks('pjm', 20, 'monthly', flow_date, '7x24', ['5x16', '2x16'], 'mwh')
print(result)

### Is DST Transition?
print('\n\n--- DST Transition ---')
flow_date = dt.datetime(2021, 3, 14)

is_tx, short_day, long_day = elektra.is_dst_transition(flow_date)
print(is_tx) # True; this is one of the transition dates
print(short_day) # True; this is the sprint DST transition date
print(long_day) # False; that would be the "fall back" date