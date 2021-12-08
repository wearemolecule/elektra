import os
import datetime as dt
import calendar
import logging

import pandas as pd
from pytz import timezone
from dateutil import tz

from elektra.exceptions import InsufficientDataError, ElektraConfigError, NoRelevantHoursTodayError
from elektra.utils import Iso, Block, Frequency, NERCHolidayCalendar

# create the logger config
log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                    format='"%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s"')


# Static holder for NERC holiday calendar
nhcal = {}


def hello():
    log.info("elektra says hi")
    return "elektra says hi"


def get_nerc_holidays(year):
    holidays = nhcal.get(year, None)
    if holidays is None:
        inst = NERCHolidayCalendar()
        holidays = inst.holidays(dt.datetime(year - 1, 12, 31), dt.datetime(year, 12, 31))
        nhcal[year] = holidays

    return holidays


def is_weekend_day(as_of):
    if as_of.weekday() < 5:
        return False
    else:
        return True


def is_offpeak_day(as_of):
    as_of = pd.to_datetime(as_of)
    if is_weekend_day(as_of):
        return True
    else:
        year_val = as_of.year
        holidays = get_nerc_holidays(year_val)
        if as_of.replace(hour=0, minute=0, second=0) in holidays:
            return True
        else:
            return False


def is_peak_day(as_of):
    return not is_offpeak_day(as_of)


def is_dst_transition(as_of):
    tz = timezone("America/Chicago")
    transition_dates = [d.date() for d in tz._utc_transition_times]

    is_tx = False
    if as_of.date() in transition_dates:
        is_tx = True
        # log.debug('DST!' + as_of.strftime("%m/%d/%Y"))

    short_day = True if (as_of.month == 3 and is_tx) else False
    long_day = True if (as_of.month == 11 and is_tx) else False

    return is_tx, short_day, long_day


def adjust_dst(as_of, mwh):
    # Is today a UTC transition date?
    is_tx, short_day, long_day = is_dst_transition(as_of)

    if short_day:
        return mwh - 1
    elif long_day:
        return mwh + 1
    else:
        return mwh


def convert(flow_dt, input_block, output_block):
    # Is today a weekend or NERC holiday?
    is_peak = not is_offpeak_day(flow_dt)

    # Is today just a weekend?
    is_weekend = (is_weekend_day(flow_dt))
    log.debug("Flow Date: {0}, Input Block: {1}, Output Block: {2}".format(flow_dt, input_block, output_block))

    mwh = 0
    # 5x16
    if input_block == '5x16' and output_block in ['5x16', '7x24']:
        mwh = 16 if is_peak else 0
    elif input_block == '5x16' and output_block in ['2x16', '7x8', 'Wrap']:
        mwh = 0
    # Wrap
    elif input_block == 'Wrap' and output_block in ['Wrap', '7x24']:
        mwh = 8 if is_peak else adjust_dst(flow_dt, 24)  # DST Check
    elif input_block == 'Wrap' and output_block == '5x16':
        mwh = 0
    elif input_block == 'Wrap' and output_block == '7x8':
        mwh = 8 if is_peak else adjust_dst(flow_dt, 8)  # DST Check
    elif input_block == 'Wrap' and output_block == '2x16':
        mwh = 16 if is_weekend else 0
    # 7x24
    elif input_block == '7x24' and output_block == '7x24':
        mwh = adjust_dst(flow_dt, 24)  # DST Check
    elif input_block == '7x24' and output_block == '5x16':
        mwh = 16 if is_peak else 0
    elif input_block == '7x24' and output_block == '2x16':
        mwh = 16 if is_weekend else 0
    elif input_block == '7x24' and output_block == '7x8':
        mwh = adjust_dst(flow_dt, 8) if not is_peak else 8  # DST Check
    elif input_block == '7x24' and output_block == 'Wrap':
        mwh = adjust_dst(flow_dt, 24) if is_weekend else 8  # DST Check
    # 2x16
    elif input_block == '2x16' and output_block in ['5x16', '7x8']:
        mwh = 0
    elif input_block == '2x16' and output_block in ['Wrap', '2x16', '7x24']:
        mwh = 16 if is_weekend else 0
    # 7x8
    elif input_block == '7x8' and output_block in ['5x16', '2x16']:
        mwh = 0
    elif input_block == '7x8' and output_block in ['7x8', 'Wrap']:
        mwh = adjust_dst(flow_dt, 8)  # DST Check
    elif input_block == '1x1' and output_block == '7x24':
        mwh = 1
    elif input_block == '1x1' and output_block == '5x16':
        mwh = 1 if (is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == '2x16':
        mwh = 1 if (not is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == 'Wrap' and is_weekend:
        mwh = 1 if (not is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == 'Wrap' and not is_weekend:
        mwh = 1 if (not is_peak and ((flow_dt.hour < 7) or (flow_dt.hour > 22))) else 0  # No DST check, right?
    elif input_block == '1x1' and output_block == '7x8':
        mwh = 1 if (not is_peak and ((flow_dt.hour < 7) or (flow_dt.hour > 22))) else 0  # No DST check, right?
    elif input_block == '7x16' and output_block == '5x16':
        mwh = 16 if not is_weekend else 0
    elif input_block == '7x16' and output_block in ['2x16', 'Wrap']:
        mwh = 16 if is_weekend else 0
    elif input_block == '7x16' and output_block == '7x24':
        mwh = 16
    elif input_block == '7x16' and output_block == '7x8':
        mwh = 0
    else:
        log.info('Input Block: {0}, Output Block: {1}'.format(input_block, output_block))
        raise ElektraConfigError('Conversion Not Supported!')

    return mwh
    # Is today a weekend or NERC holiday?
    is_peak = not is_offpeak_day(flow_dt)

    # Is today just a weekend?
    is_weekend = (is_weekend_day(flow_dt))

    mwh = 0
    # 5x16
    if input_block == '5x16' and output_block in ['5x16', '7x24']:
        mwh = 16 if is_peak else 0
    elif input_block == '5x16' and output_block in ['2x16', '7x8', 'Wrap']:
        mwh = 0
    # Wrap
    elif input_block == 'Wrap' and output_block in ['Wrap', '7x24']:
        mwh = 8 if is_peak else adjust_dst(flow_dt, 24)  # DST Check
    elif input_block == 'Wrap' and output_block == '5x16':
        mwh = 0
    elif input_block == 'Wrap' and output_block == '7x8':
        mwh = 0 if is_peak else adjust_dst(flow_dt, 8)  # DST Check
    elif input_block == 'Wrap' and output_block == '2x16':
        mwh = 16 if is_weekend else 0
    # 7x24
    elif input_block == '7x24' and output_block == '7x24':
        mwh = adjust_dst(flow_dt, 24)  # DST Check
    elif input_block == '7x24' and output_block == '5x16':
        mwh = 16 if is_peak else 0
    elif input_block == '7x24' and output_block == '2x16':
        mwh = 16 if is_weekend else 0
    elif input_block == '7x24' and output_block == '7x8':
        mwh = adjust_dst(flow_dt, 8) if not is_peak else 0  # DST Check
    elif input_block == '7x24' and output_block == 'Wrap':
        mwh = adjust_dst(flow_dt, 24) if is_weekend else 8  # DST Check
    # 2x16
    elif input_block == '2x16' and output_block in ['5x16', '7x8']:
        mwh = 0
    elif input_block == '2x16' and output_block in ['Wrap', '2x16', '7x24']:
        mwh = 16 if is_weekend else 0
    # 7x8
    elif input_block == '7x8' and output_block in ['5x16', '2x16']:
        mwh = 0
    elif input_block == '7x8' and output_block in ['7x8', 'Wrap']:
        mwh = adjust_dst(flow_dt, 8)  # DST Check
    elif input_block == '1x1' and output_block == '7x24':
        mwh = 1
    elif input_block == '1x1' and output_block == '5x16':
        mwh = 1 if (is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == '2x16':
        mwh = 1 if (not is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == 'Wrap' and is_weekend:
        mwh = 1 if (not is_peak and (7 <= flow_dt.hour <= 22)) else 0
    elif input_block == '1x1' and output_block == 'Wrap' and not is_weekend:
        mwh = 1 if (not is_peak and ((flow_dt.hour < 7) or (flow_dt.hour > 22))) else 0  # No DST check, right?
    elif input_block == '1x1' and output_block == '7x8':
        mwh = 1 if (not is_peak and ((flow_dt.hour < 7) or (flow_dt.hour > 22))) else 0  # No DST check, right?
    elif input_block == '7x16' and output_block == '5x16':
        mwh = 16 if not is_weekend else 0
    elif input_block == '7x16' and output_block in ['2x16', 'Wrap']:
        mwh = 16 if is_weekend else 0
    elif input_block == '7x16' and output_block == '7x24':
        mwh = 16
    elif input_block == '7x16' and output_block == '7x8':
        mwh = 0
    else:
        log.info('Input Block: {0}, Output Block: {1}'.format(input_block, output_block))
        raise ElektraConfigError('Conversion Not Supported!')

    return mwh


def translateBlocks(iso, mw, frequency, contract_start, in_block, out_blocks, out_uom):
    # Blocks are: 7x24, 5x16, Wrap, 2x16, 7x8
    # Frequency is a stub: monthly, daily, hourly
    # ISO is a stub; CAISO includes Saturdays (or Sundays) in Peak, but others should be the same

    # Given frequency and contract_start, come up with a date range
    if frequency == "monthly":
        ldom = calendar.monthrange(contract_start.year, contract_start.month)[1]
        contract_end = dt.datetime(contract_start.year, contract_start.month, ldom)
    else:
        contract_end = contract_start
        log.debug('Contract Start: {0}, Contract End: {1}'.format(contract_start, contract_end))

    # Create empty output dataframe. Columns: Date, mwh for each element in out_blocks
    df = pd.DataFrame({'date': pd.date_range(start=contract_start, end=contract_end)})
    # df.set_index('date')
    for out_block in out_blocks:
        pd.DataFrame.insert(df, len(df.columns), out_block, 0.0, allow_duplicates=True)

    # Loop through each date and determine how many hours in each block
    for index, row in df.iterrows():
        log.debug('MW: {0}'.format(mw))
        for out_block in out_blocks:
            calc_value = convert(row['date'], in_block, out_block)
            log.debug('Calc_value: {0}'.format(calc_value))
            calc_value = (calc_value / calc_value) if ((calc_value != 0) and (out_uom == 'MW')) else calc_value
            value = calc_value * mw
            log.debug('Date: {0}, in_block: {1}, out_block: {2}, calc_value: {3}, value: {4}, inputmw: {5}'.format(
                row['date'], in_block, out_block, calc_value, value, mw))
            df.at[index, out_block] = value

    return df

def _merge_two_blocks(month, blk_0_price, blk_1_price, from_blocks, iso):
    '''Helper for merge_block_prices'''
    df = translateBlocks(iso, 1, 'monthly', pd.to_datetime(month), '7x24', from_blocks, 'mwh')
    blk_0_hrs = df[from_blocks[0]].sum()
    blk_1_hrs = df[from_blocks[1]].sum()
    total_px = (blk_0_price * blk_0_hrs + blk_1_price * blk_1_hrs) / (blk_0_hrs + blk_1_hrs)
    return total_px

def merge_block_prices(df, iso='pjm', to_block='7x24' ):
    '''
    Returns: a df with a strip of translated prices, weighted-averaged on the number of block-hours in the months
    Input: a dataframe with strips of block pricing, plus iso and desired final block type

    Example Input df:
    Index      | 5x16  | Wrap
    2021-12-01 | 73.35 ! 60.95
    2022-01-01 | 91.85 | 68.10

    Returns:
    Index      | 5x16  | Wrap  | Total
    2021-12-01 | 73.35 ! 60.95 | 67.0866
    2022-01-01 | 91.85 | 68.10 | 78.8258
    '''
    from_blocks = df.columns.to_list()
    df['Total'] = df.apply(lambda row: _merge_two_blocks(
                        row.name, row[from_blocks[0]], row[from_blocks[1]], from_blocks, iso), axis=1
                        )
    return df
  
def get_blocks(as_of):
    """
        returns a list of blocks that are relevant for a given date

    holidays = ['01/01/2019','05/27/2019','07/04/2019','09/02/2019','11/28/2019','12/25/2019']
    weekends = [5,6]
    if (as_of.weekday() in weekends) or (as_of.strftime('%m/%d/%Y') in holidays):
    """
    nerc = HolidayCalendar('nerc') #TODO: Unresolved reference
    if not nerc.is_business_day(as_of):
        # return ['off_peak_weekends', 'atc']
        return ['off_peak_weekends', 'atc', 'off_peak_all', 'on_peak_all']
    else:
        # return ['on_peak_weekdays','off_peak_weekdays','atc']
        return ['on_peak_weekdays', 'off_peak_weekdays', 'atc', 'off_peak_all', 'on_peak_all']


def get_iso_details(iso):
    if iso in [Iso.AESO, Iso.ISONE, Iso.NYISO, Iso.PJM, Iso.MISO]:
        first_peak_he = 8
        last_peak_he = 23
    elif iso in [Iso.ERCOT, Iso.SPP]:
        first_peak_he = 7
        last_peak_he = 22
    else:
        raise ElektraConfigError('Invalid ISO:' + iso)

    return first_peak_he, last_peak_he


def get_required_hours(block, as_of):
    if block in [Block._7x24]:
        required_marks = 24 + dst_hour(as_of)
    elif block in [Block.Wrap]:
        if not is_offpeak_day(as_of):
            required_marks = 16
        else:
            required_marks = 8 + dst_hour(as_of)
    elif block in [Block._5x16, Block._7x8, Block._7x16]:
        if block in [Block._5x16, Block._7x16]:
            required_marks = 16
        else:
            required_marks = 8 + dst_hour(as_of)
    else:
        raise ElektraConfigError('Block not found: {0}'.format(block))
    # df_iso_details = pd.DataFrame(details)
    return required_marks


def dst_hour(as_of):
    try:
        cst = tz.gettz('America/Chicago')
        d1 = dt.datetime(as_of.year, as_of.month, as_of.day, tzinfo=cst)
        d2 = d1 + dt.timedelta(days=1)
        return d1.dst().seconds / 3600 - d2.dst().seconds / 3600
    except:
        return 0


def is_relevant_hour(block, iso, data_hour, flow_date):
    first_peak, last_peak = get_iso_details(iso)
    ret = False
    special = None

    if block in [Block._5x16, Block._7x16, Block._2x16]:
        if first_peak <= data_hour <= last_peak:
            ret = True
    elif block in [Block._7x24, Block._1x1]:
        ret = True
    elif block in [Block.Wrap]:
        if is_offpeak_day(flow_date):
            ret = True
        elif (data_hour < first_peak) or (data_hour > last_peak):
            ret = True
    elif block in [Block._7x8]:
        if (data_hour < first_peak) or (data_hour > last_peak):
            ret = True

    # Check DST Craziness, for hours that would otherwise be relevant
    if ret:
        is_tx, short_day, long_day = is_dst_transition(flow_date)  # Look for DST Weirdness
        if is_tx and short_day and data_hour == 3:
            log.info('Short Day: {0}, Short Hour: {1}'.format(flow_date.strftime('%Y-%m-%d'), data_hour))
            ret = False
        elif is_tx and long_day and data_hour == 2:
            log.info('Long Day: {0}, Long Hour: {1}'.format(flow_date.strftime('%Y-%m-%d'), data_hour))
            ret = True
            special = 'long'

    return ret, special


def is_relevant_day(block, iso, flow_date):
    if block in [Block._5x16] and is_peak_day(flow_date):
        return True
    elif block in [Block._7x8, Block._7x16, Block._7x24, Block.Wrap]:
        return True
    elif block in [Block._2x16] and is_offpeak_day(flow_date):
        return True
    else:
        return False


def ldom(flow_date):
    day = calendar.monthrange(flow_date.year, flow_date.month)[1]
    ldom = dt.datetime(year=flow_date.year, month=flow_date.month, day=day)
    return ldom


def fdom(flow_date):
    return dt.datetime(year=flow_date.year, month=flow_date.month, day=1)


def fhod(flow_date):
    return dt.datetime(year=flow_date.year, month=flow_date.month, day=flow_date.day, hour=0)


def lhod(flow_date):
    return dt.datetime(year=flow_date.year, month=flow_date.month, day=flow_date.day, hour=23)


def create_prices(flow_date, ticker, node, iso, block, frequency, input_prices):
    # Input_prices will need: flow_date, hour_beginning, and price
    log.info('--- I am Elektra. ---')
    log.debug(input_prices)
    if input_prices.empty:
        raise InsufficientDataError(
            'input_prices is empty. This method expects a DataFrame with 3 columns: flow_date (string in YYYY-MM-DD '
            'format), hour_ending (number), and price (number)')

    # Translate input values to Enums
    iso = Iso(iso.lower())
    block = Block(block.lower())
    frequency = Frequency(frequency.lower())

    # Build a calendar of the dates and hours that we'll need (note this is hour-beginning)
    if frequency == Frequency.Monthly:
        start_dt = fhod(fdom(flow_date))
        end_dt = lhod(ldom(flow_date))
    else:
        start_dt = fhod(flow_date)
        end_dt = lhod(flow_date)

    hours = pd.date_range(start=start_dt, end=end_dt, closed=None, normalize=False, freq='H')
    log.debug(hours.format(formatter=lambda x: x.strftime('%Y-%m-%d  %H:%M')))

    # Mark Required Hours
    df = pd.DataFrame()
    for dh in hours:
        he = dh.hour + 1
        # if(ticker == 'M.HB8G'):
        #   import pdb; pdb.set_trace()
        rlv_day = is_relevant_day(block, iso, dh)  # Look for relevant days (use hour-beginning)
        rlv_hr, special = is_relevant_hour(block, iso, he, dh)  # Look for relevant hours (use hour-ending)
        log.debug('Date: {0} - Relevant Day? {1} | Relevant Hour? {2}'.format(dh, rlv_day, rlv_hr))

        if rlv_day and rlv_hr:
            df = df.append({'DHB': dh, 'HE': he, 'Required': True, 'Value': None, 'Special': special},
                           ignore_index=True)
            log.debug('I am relevant: {0} HE {1}'.format(dh.strftime('%Y-%m-%d'), he))

    # Fill required hours table with data. Barf if we're missing something.
    # Nice-to-have: Fill it backwards (because it's more likely we won't have the ending settles)
    # df.to_csv('outputs/required - '+ticker+'.csv')
    for index, row in df.iterrows():

        test_date = row['DHB'].date()
        hour_ending = row['HE']

        expected = 2 if (row['Special'] is not None) else 1  # We always expect 1 row of LMP data, except for long hour
        # if((frequency == Frequency.Daily) and test_date.day == 1):
        #       import pdb; pdb.set_trace()

        raw = input_prices[
            input_prices.flow_date.eq(test_date.strftime('%Y-%m-%d')) & input_prices.hour_ending.eq(hour_ending)]
        x = raw['price'].to_list()  # Get array of prices from query (usually 1 row)

        if len(raw) != expected:
            raise InsufficientDataError(
                'Incorrect number of prices for {3}/{7}: {4} {5} {6} {0} HE {1}. Expected: {8}; Got: {2}. Stopping.'.format(
                    test_date.strftime('%Y-%m-%d'), str(hour_ending), len(raw), ticker, iso, block, frequency, node,
                    expected))
        else:
            # Update the value
            df.at[index, 'Value'] = x[0]
            # Add second value, as HE25, for the long hour
            if expected == 2:
                df = df.append(
                    {'DHB': row['DHB'], 'HE': 25, 'Required': True, 'Value': x[1], 'Special': row['Special']},
                    ignore_index=True)

    if df.empty:
        raise NoRelevantHoursTodayError(
            'No relevant hours on {0} for ticker {1}.'.format(flow_date.strftime('%Y-%m-%d'), ticker))

    # TODO: Check math
    # Average the data by relevant period (which is already established)
    price = df['Value'].astype('float64').mean()

    log.info(
        'Flow Date: {0} Ticker: {1}, Block: {2}, Frequency: {3}, ISO: {4} >> {5}'.format(flow_date, ticker, block.value,
                                                                                         frequency.value, iso.value,
                                                                                         price))
    log.info('--- Elektra Processing Complete. ---')
    return price


def scrub_hourly_prices(flow_date, ticker, node, iso, input_prices):
    # Input_prices will need: flow_date, hour_beginning, and price
    log.info('--- I am Elektra. ---')
    log.debug(input_prices)
    if input_prices.empty:
        raise InsufficientDataError(
            'input_prices is empty. This method expects a DataFrame with 3 columns: flow_date (string in YYYY-MM-DD format), hour_ending (number), and price (number)')

    # Translate input values to Enums
    iso = Iso(iso.lower())
    frequency = Frequency.Hourly
    block = Block._1x1

    # Build a calendar of the hours today
    start_dt = fhod(flow_date)
    end_dt = lhod(flow_date)

    hours = pd.date_range(start=start_dt, end=end_dt, closed=None, normalize=False, freq='H')

    # Mark Required Hours
    df = pd.DataFrame()
    for dh in hours:
        he = dh.hour + 1
        rlv_hr, special = is_relevant_hour(block, iso, he, dh)  # Look for relevant hours (use hour-ending)
        log.debug('Date: {0} - | Relevant Hour? {1}'.format(dh, rlv_hr))

        if rlv_hr:
            df = df.append({'DHB': dh, 'HE': he, 'Required': True, 'Value': None, 'Special': special},
                           ignore_index=True)
            log.debug('I am relevant: {0} HE {1}'.format(dh.strftime('%Y-%m-%d'), he))

    # Fill required hours table with data. Barf if we're missing something.
    # Nice-to-have: Fill it backwards (because it's more likely we won't have the ending settles)
    # df.to_csv('outputs/required - '+ticker+'.csv')
    for index, row in df.iterrows():

        test_date = row['DHB'].date()
        hour_ending = row['HE']

        expected = 2 if (row['Special'] is not None) else 1  # We always expect 1 row of LMP data, except for long hour
        # if((frequency == Frequency.Daily) and test_date.day == 1):
        #       import pdb; pdb.set_trace()

        raw = input_prices[
            input_prices.flow_date.eq(test_date.strftime('%Y-%m-%d')) & input_prices.hour_ending.eq(hour_ending)]
        x = raw['price'].to_list()  # Get array of prices from query (usually 1 row)

        if len(raw) != expected:
            raise InsufficientDataError(
                'Incorrect number of prices for {3}/{7}: {4} {5} {6} {0} HE {1}. Expected: {8}; Got: {2}. Stopping.'.format(
                    test_date.strftime('%Y-%m-%d'), str(hour_ending), len(raw), ticker, iso, block, frequency, node,
                    expected))
        else:
            # Update the value
            df.at[index, 'Value'] = x[0]
            # Add second value, as HE25, for the long hour
            if expected == 2:
                df = df.append(
                    {'DHB': row['DHB'], 'HE': 25, 'Required': True, 'Value': x[1], 'Special': row['Special']},
                    ignore_index=True)

    # Return Output Dataframe Directly
    price = df
    log.info(
        'Flow Date: {0} Ticker: {1}, Block: {2}, Frequency: {3}, ISO: {4} >> Hourly Prices'.format(flow_date, ticker,
                                                                                                   block.value,
                                                                                                   frequency.value,
                                                                                                   iso.value))
    log.info('--- Elektra Processing Complete. ---')
    return price
