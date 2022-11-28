import unittest
import elektra
from datetime import datetime, timedelta
import pandas as pd

class CaisoTests(unittest.TestCase):

    def setUp(self):
        self.iso = elektra.utils.Iso('caiso')
        self.peak_block = elektra.utils.Block('6x16')
        self.wrap_block = elektra.utils.Block('wrap')
        self.weekday_dates = [datetime(2022, 11, i) for i in range(7, 12)]  # november 7-11, 2022; used for weekday tests
        self.saturday_date = datetime(2022, 11, 26) # used for saturday tests
        self.sunday_date = datetime(2022, 11, 27)   # used for sunday tests

    def make_prices_df(self, flow_date):
        '''
            function to make a dataframe of hourly prices for a single flow date
        '''

        def hour_ending(row):
            '''
                function to set the hour ending how elektra expects it, which is:
                    1...24 on normal days
                    1, 2, 4, 5...24 on the short day
                    1, 2, 2, 3...24 on the long day
            '''
            if row.hours_in_day == 24:
                return row.name + 1
            if row.hours_in_day == 23:
                #return row.name + 2 if row.name >= 2 else row.name + 1
                return row.name +1 if row.name < 2 else row.name + 2
            if row.hours_in_day == 25:
                #return row.name if row.name >= 2 else row.name + 1
                return row.name + 1 if row.name < 2 else row.name
        
        def price(row):
            '''
                simple function to create a price value
                40 + (date number / 10) + (hour number / 10)
            '''
            return 40 + (row.flow_date_time.day / 10) + (row.hour_ending / 10)

        prices = pd.DataFrame(
            data=pd.date_range(start=flow_date, end=(flow_date + timedelta(days=1)), freq='H', closed='left', tz='America/Los_Angeles'), \
            columns=['flow_date_time',]
            )
        prices.loc[:, 'hours_in_day'] = prices.index.size
        prices.loc[:, 'flow_date'] = prices.flow_date_time.dt.strftime('%Y-%m-%d')
        prices.loc[:, 'hour_ending'] = prices.apply(hour_ending, axis=1)
        prices.loc[:, 'price'] = prices.apply(price, axis=1)
        return prices.loc[:, ('flow_date', 'hour_ending', 'price')]


    def test_peak_hours_start_end(self):
        '''
            tests for verifying the first and last peak hours
        '''
        first_peak_hour, last_peak_hour = elektra.get_iso_details(iso=self.iso)

        self.assertEqual(first_peak_hour, 7)
        self.assertEqual(last_peak_hour, 22)

    
    def test_weekdays(self):
        '''
            tests for non-holiday weekdays
        '''

        # averaged prices for verification (peak, wrap)
        prices = [(42.15,41.55), (42.25,41.65), (42.35,41.75), (42.45,41.85), (42.55,41.95)]

        for w in zip(self.weekday_dates, prices):
            # weekdays are both peak and wrap
            self.assertTrue(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=w[0]), msg=f'test failed for {w[0].strftime("%m/%d/%Y")}')
            self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=w[0]), msg=f'test failed for {w[0].strftime("%m/%d/%Y")}')

            # peak hours equals 16
            peak_hours = [elektra.is_relevant_hour(block=self.peak_block, iso=self.iso, data_hour=i, flow_date=w[0]) for i in range(1,25)]
            self.assertEqual(len([h for h in peak_hours if h[0]]), 16)
            
            # wrap hours equals 8
            wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=w[0]) for i in range(1,25)]
            self.assertEqual(len([h for h in wrap_hours if h[0]]), 8)

            # create a dataframe of prices to use to to test averaging
            prices = self.make_prices_df(flow_date=w[0])

            # peak averaging
            daily_6x16_price = elektra.create_prices(w[0], ticker='', node='', iso=self.iso.value, block=self.peak_block.value, frequency='daily', input_prices=prices)
            self.assertAlmostEqual(daily_6x16_price, w[1][0], places=7, msg=f'test failed for peak {w[0].strftime("%m/%d/%Y")}')

            # wrap averaging
            daily_wrap_price = elektra.create_prices(w[0], ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
            self.assertAlmostEqual(daily_wrap_price, w[1][1], places=7, msg=f'test failed for wrap {w[0].strftime("%m/%d/%Y")}')
    
    def test_saturday(self):
        '''
            tests for a normal saturday that is not a holiday
        '''

        # saturday is a peak day
        self.assertTrue(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=self.saturday_date))

        # saturday is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=self.saturday_date))

        # peak hours equals 16
        peak_hours = [elektra.is_relevant_hour(block=self.peak_block, iso=self.iso, data_hour=i, flow_date=self.saturday_date) for i in range(1,25)]
        self.assertEqual(len([h for h in peak_hours if h[0]]), 16)

        # wrap hours equals 8
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=self.saturday_date) for i in range(1,25)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 8)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=self.saturday_date)

        # peak averaging
        daily_6x16_price = elektra.create_prices(self.saturday_date, ticker='', node='', iso=self.iso.value, block=self.peak_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_6x16_price, 44.05, places=7)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(self.saturday_date, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 43.45, places=7)

    def test_sunday(self):
        '''
            tests for a normal sunday that is not a holiday
        '''

        # sunday is not a peak day
        self.assertFalse(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=self.sunday_date))

        # sunday is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=self.sunday_date))

        # wrap hours equals 24
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=self.sunday_date) for i in range(1,25)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 24)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=self.sunday_date)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(self.sunday_date, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 43.95, places=7)

    def test_thanksgiving_2022(self):
        '''
            tests for thanksgiving, 2022 which is a simple holiday
        '''

        thanksgiving_2022 = datetime(2022, 11, 24)

        # thanksgiving is not a peak day
        self.assertFalse(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=thanksgiving_2022))

        # thanksgiving is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=thanksgiving_2022))

        # wrap hours equals 24
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=thanksgiving_2022) for i in range(1,25)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 24)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=thanksgiving_2022)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(thanksgiving_2022, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 43.65, places=7)

    def test_new_years_2022(self):
        '''
            tests for new year's day, 2022
            this one is interesting because it falls on a saturday, which is typically a peak day for caiso
        '''

        new_years_2022 = datetime(2022, 1, 1)

        # new year's day is not a peak day
        self.assertFalse(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=new_years_2022))

        # new year's day is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=new_years_2022))

        # wrap hours equals 24
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=new_years_2022) for i in range(1,25)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 24)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=new_years_2022)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(new_years_2022, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 41.35, places=7)

    def test_short_day_2022(self):
        '''
            tests for the short day in 2022, when daylight savings begins
        '''

        short_day_2022 = datetime(2022, 3, 13)

        # the short day is not a peak day
        self.assertFalse(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=short_day_2022))

        # the short day is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=short_day_2022))

        # wrap hours equals 23
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=short_day_2022) for i in range(1,25)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 23)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=short_day_2022)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(short_day_2022, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 42.5913043, places=7)

    def test_long_day_2022(self):
        '''
            tests for the long day in 2022, when daylight savings ends
        '''

        long_day_2022 = datetime(2022, 11, 6)

        # the long day is not a peak day
        self.assertFalse(elektra.is_relevant_day(block=self.peak_block, iso=self.iso, flow_date=long_day_2022))

        # the long day is a wrap day
        self.assertTrue(elektra.is_relevant_day(block=self.wrap_block, iso=self.iso, flow_date=long_day_2022))

        # wrap hours equals 25
        wrap_hours = [elektra.is_relevant_hour(block=self.wrap_block, iso=self.iso, data_hour=i, flow_date=long_day_2022) for i in range(1,26)]
        self.assertEqual(len([h for h in wrap_hours if h[0]]), 25)

        # create a dataframe of prices to use to to test averaging
        prices = self.make_prices_df(flow_date=long_day_2022)

        # wrap averaging
        daily_wrap_price = elektra.create_prices(long_day_2022, ticker='', node='', iso=self.iso.value, block=self.wrap_block.value, frequency='daily', input_prices=prices)
        self.assertAlmostEqual(daily_wrap_price, 41.808, places=7)