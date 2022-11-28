[![PyPI version](https://badge.fury.io/py/elektra.svg)](https://badge.fury.io/py/elektra)

# Elektra

Elektra is Molecule's core framework for block logic (i.e., how to compute mwh from 5x16, 2x16, etc. blocks). It's derived from a set of logic internal to the Molecule application, and we're happy to share it with the world -- because nobody should ever have to fight with North American power blocks _ever_ again.

Elektra is in pre-release, which means that signatures may change over time as we evolve the project to 1.0. Submissions are welcome; just submit a pull request with your change.

## Installing Elektra

Either clone this repo, or use pip:

> pip3 install elektra
> 
## Using Elektra

In your python project, `import elektra` and use away. Usage examples are in `examples/examples.py`. A sample input CSV is there too. For the examples below, we will use that CSV. You can also use the table of data at the end of this file.


## Parameters

Internally, Elektra uses enums for ISO, Block, and Frequency. String inputs for these fields are converted to the enum when Elektra runs, and so must be provided in the exact format the Enum expects.

1. `iso`: permitted values are `miso`, `isone`, `ercot`, `pjm`, `spp`, `aeso`, `nyiso`, `caiso`
2. `block`: permitted values are `7x8`, `5x16`, `2x16`, `7x24`, `7x16`, `1x1`, `wrap`, `6x16`
3. `frequency`: permitted values are `daily`, `monthly`, `hourly`

## Methods

These are the primary methods available in Elektra. Other methods are available, but are undocumented.
* [create_prices](#create_prices): Creates block prices from raw LMP input
* [scrub_hourly_prices](#scrub_hourly_prices): Verifies that enough hourly LMPs are present
* [convert](#convert): Converts hours in one block, to equivalent hours in another
* [translate_blocks](#translate_blocks): Wraps [convert](#convert), and adds MW and/or MWh conversions
* [is_dst_transition](#is_dst_transition): Determines if a date is a DST changeover day


### create_prices
This method creates block prices, given hourly prices for a period of time and a handful of other parameters. A key function of this method is that it validates whether enough prices have been submitted to do the calculation. So, if the `block` is 5x16, but a price is missing for a Wednesday at 11 AM, an exception will be thrown. Daylight Savings Time is also contemplated.

The *create_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `ticker` - *string* | The ticker symbol for the power product (Molecule ticker; used for identification, not calculation)
* `node` - *string* | The node on the power grid (used for identification, not calculation)
* `iso` - *string* | The name of the Independent System Operator (ISO). CAISO is not currently supported.
* `block` - *string* | The desired power block for the output prices
* `frequency` *string* | The desired frequency for the output prices (either `daily` or `monthly`)
* `prices` *DataFrame* | A Pandas dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a single floating-point price.

#### Example
``` python
import elektra
import pandas as pd
import filecmp
import datetime as dt

flow_date = dt.datetime(2020, 10, 17)
prices = pd.read_csv('lmps.csv')

result = elektra.create_prices(flow_date, 'M.XXXX', 'INDIANA.HUB', 'miso', '2x16', 'daily', prices)
print(result)

```

### scrub_hourly_prices
This method validates that a submitted dataframe contains all the necessary hourly prices for a flow date, and returns a DataFrame with these prices. Daylight Savings Time (long-day and short-day) is contemplated.

The *scrub_hourly_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `ticker` - *string* | The ticker symbol for the power product (Molecule ticker; used for identification, not calculation)
* `node` - *string* | The node on the power grid (used for identification, not calculation)
* `iso` - *string* | The name of the Independent System Operator (ISO). CAISO is not currently supported.
* `prices` *DataFrame* | A Pandas dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a Pandas dataframe with the following columns of data:

* Hour Beginning
* Hour Ending
* Required
* Special
* Value

#### Example
``` python
import elektra
import pandas as pd
import filecmp
import datetime as dt

flow_date = dt.datetime(2020, 10, 17)
prices = pd.read_csv('lmps.csv')

result = elektra.scrub_hourly_prices(flow_date, 'M.XXXX', '116013753', 'pjm', prices)
print(result)

```


### convert
Given a flow date and an input block (i.e., 5x16), this method returns the number of hours in another block.

For example, if today is Wednesday, November 4, 2020, and I have a 7x24 block (24 hours), but I want to see how many 5x16 hours that implies -- I'll get 16. On the other hand, if today is Saturday, October 31, 2020, and I have a Wrap block (24 hours that day), that only implies 8 hours of 7x8. This is useful when trying to convert a position purchased in one block, to a volume of another block. It works in tandem with the TranslateBlocks method.

The *convert* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `input_block` -- (text: Wrap, 5x16, 2x16, 7x8, 7x16, 1x1) | The input block.
* `output_block` -- (text: Wrap, 5x16, 2x16, 7x8, 7x16, 1x1) | The block for which we want to see hours.

The response from this method is an integer, representing the number of hours in the output block.

#### Example
``` python
import elektra
import datetime as dt

flow_date = dt.datetime(2020, 10, 17)

result = elektra.convert(flow_date, '7x24', '2x16') # 16: (October 17 2020 is a Saturday, and has 16 peak hours)
result = elektra.convert(flow_date, '7x24', '5x16') # 0: (October 17 2020 is a Saturday, and has 0 weekday peak hours)
result = elektra.convert(flow_date, '5x16', '2x16') # 0: (October 17 2020 is a Saturday, and there could not be a 5x16 input block)

```

### translate_blocks
Wrapper for `convert`, which adds the ability to convert a MW position for a term block (i.e., 7x24 monthly) to another block (or blocks) for that same term (i.e., 5x16, 2x16).

The *translateBlocks* method takes the following parameters:
* `iso` - *string* | The short name of the Independent System Operator (Elektra.Iso). This is not currently used, so beware when using for CAISO.
* `mw` - *decimal* | The number of megawatts on the input block to be used for mw/mwh computation
* `frequency` - *string* | monthly, daily, or hourly. Currently only monthly is implemented.
* `contract_start` *date* | The first flow date of the block. This method will compute the last flow date.
* `in_block` - *string* | 7x24, 5x16, Wrap, 2x16, 7x8
* `out_blocks` - *string array* | accepted values include 7x24, 5x16, Wrap, 2x16, 7x8
* `out_uom` - *string* | Set to `MW` for a megawatt number. Default is `mwh`.

The response from this method is a DataFrame with the following columns:
* date (i.e., flow date)
* one column for each `out_block`, representing the number of MW or MWh for each date

#### Example
``` python
import elektra
import datetime as dt

flow_date = dt.datetime(2020, 10, 1)
result = elektra.translateBlocks('pjm', 20, 'monthly', flow_date, '7x24', ['5x16', '2x16'], 'mwh')
print(result)
```

### is_dst_transition
Responds with variables that indicate whether the input date is a DST transition day, and whether it is the _short day_ of the year (i.e., spring DST transition day) or the _long day_ of the year (fall). If the date is not the transition day, the short- and long- day returns are False.

The method takes the following parameter:
* `as_of` - *date* | The date to test

The method returns the following parameters:
* `is_tx` - *boolean* | True, if the supplied date is one of the two yearly transition days
* `short_day` - *boolean* | True, if the supplied date is the short day
* `long_day` - *boolean* | True, if the supplied date is the long day

#### Example
``` python
import elektra
import datetime as dt
flow_date = dt.datetime(2021, 3, 14)

is_tx, short_day, long_day = elektra.is_dst_transition(flow_date)
print(is_tx) # True; this is one of the transition dates
print(short_day) # True; this is the spring DST transition date
print(long_day) # False; that would be the "fall back" date
```

## Sample Data
This data is suitable for inputs to the hourly and block price converters:

| flow_date  | hour_ending | price |
|------------|-------------|-------|
| 2020-10-17 | 1.0         | 26.48 |
| 2020-10-17 | 2.0         | 20.35 |
| 2020-10-17 | 3.0         | 17.19 |
| 2020-10-17 | 4.0         | 17.16 |
| 2020-10-17 | 5.0         | 20.28 |
| 2020-10-17 | 6.0         | 34.25 |
| 2020-10-17 | 7.0         | 21.24 |
| 2020-10-17 | 8.0         | 23.67 |
| 2020-10-17 | 9.0         | 22.37 |
| 2020-10-17 | 10.0        | 20.81 |
| 2020-10-17 | 11.0        | 21.10 |
| 2020-10-17 | 12.0        | 19.28 |
| 2020-10-17 | 13.0        | 18.94 |
| 2020-10-17 | 14.0        | 18.07 |
| 2020-10-17 | 15.0        | 19.43 |
| 2020-10-17 | 16.0        | 18.94 |
| 2020-10-17 | 17.0        | 18.85 |
| 2020-10-17 | 18.0        | 22.40 |
| 2020-10-17 | 19.0        | 60.50 |
| 2020-10-17 | 20.0        | 19.12 |
| 2020-10-17 | 21.0        | 20.36 |
| 2020-10-17 | 22.0        | 19.39 |
| 2020-10-17 | 23.0        | 17.67 |
| 2020-10-17 | 24.0        | 17.55 |
