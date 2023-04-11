import unittest
import elektra
import pandas as pd
import datetime as dt


class ElektraTests(unittest.TestCase):
  def test_hello_elektra(self):
    result = elektra.hello()
    self.assertEqual(result, 'elektra says hi')

  def test_create_price_method(self):
    # happy path test through the elektra create price method

    # create a panda from the test csv file
    prices = pd.read_csv('tests/created_prices.csv')

    # call the create prices method and compare results
    result = elektra.create_prices(dt.datetime.strptime('2020-10-17','%Y-%m-%d'),'M.P4F8', 'INDIANA.HUB', 'miso','2x16','Daily', prices)
    self.assertEqual(result,22.55625)

  def test_scrub_price_method(self):
    # happy path test through the elektra scrub price method

    # create a panda from the test csv file
    prices = pd.read_csv('tests/scrub_hourly_prices.csv')

    # call the create prices method and compare results
    result = elektra.scrub_hourly_prices(dt.datetime.strptime('2020-10-17','%Y-%m-%d'),'M.YERX', '116013753', 'pjm', prices)
    self.assertTrue(result.to_csv,'test-data/scrub_hourly_prices_result.csv')

  def test_2x16_weekday_holiday(self):
    '''
      testing convert and translate functions for output block 2x16 on a weekday that is a holiday
    '''
    test_date = dt.datetime(2023, 12, 25)
    iso = elektra.utils.Iso('pjm')    
    output_block = '2x16'
    input_blocks = ['Wrap','7x24','2x16','7x16']
    
    print() # flush
    
    for input_block in input_blocks:
      print(f'testing input block {input_block} to output block {output_block}...')
      converted_mwh = elektra.convert(test_date, input_block, output_block)
      translated_mwh = elektra.translateBlocks(iso=iso, mw=1, frequency='daily', \
        contract_start=test_date, in_block=input_block, out_blocks=[output_block,], out_uom='MWh')
          
      self.assertEqual(converted_mwh, 16)
      self.assertEqual(translated_mwh.loc[0, output_block], 16)

  def test_5x16_weekday_holiday(self):
    '''
      testing convert and translate functions for output block 5x16 on a weekday that is a holiday
    '''
    test_date = dt.datetime(2023, 12, 25)
    iso = elektra.utils.Iso('pjm')    
    output_block = '5x16'
    input_blocks = ['7x16']
    
    print() # flush
    
    for input_block in input_blocks:
      print(f'testing input block {input_block} to output block {output_block}...')
      converted_mwh = elektra.convert(test_date, input_block, output_block)
      translated_mwh = elektra.translateBlocks(iso=iso, mw=1, frequency='daily', \
        contract_start=test_date, in_block=input_block, out_blocks=[output_block,], out_uom='MWh')
          
      self.assertEqual(converted_mwh, 0)
      self.assertEqual(translated_mwh.loc[0, output_block], 0)

  def test_wrap_weekday_holiday_hourly(self):
    '''
      testing hourly convert and translate functions for output block Wrap on a weekday that is a holiday
    '''
    test_date = dt.datetime(2023, 12, 25)
    iso = elektra.utils.Iso('pjm')
    output_block = 'Wrap'
    input_block = '1x1'
    hours =  [1, 10, 23]
    
    print() # flush
    
    for hour in hours:
      print(f'testing input block {input_block} to output block {output_block} for hour {hour}...')
      test_date = test_date.replace(hour=hour)
      converted_mwh = elektra.convert(test_date, input_block, output_block)
      translated_mwh = elektra.translateBlocks(iso=iso, mw=1, frequency='daily', \
        contract_start=test_date, in_block=input_block, out_blocks=[output_block,], out_uom='MWh')
          
      self.assertEqual(converted_mwh, 1)
      self.assertEqual(translated_mwh.loc[0, output_block], 1)

  def test_wrap_weekday_hourly(self):
    '''
      testing hourly convert and translate functions for output block Wrap on a weekday
    '''
    test_date = dt.datetime(2023, 12, 26)
    iso = elektra.utils.Iso('pjm')
    output_block = 'Wrap'
    input_block = '1x1'
    peak_hours =  [10,]
    off_peak_hours =  [1, 23]
    
    print() # flush
    
    for hour in peak_hours:
      print(f'testing input block {input_block} to output block {output_block} for hour {hour}...')
      test_date = test_date.replace(hour=hour)
      converted_mwh = elektra.convert(test_date, input_block, output_block)
      translated_mwh = elektra.translateBlocks(iso=iso, mw=1, frequency='daily', \
        contract_start=test_date, in_block=input_block, out_blocks=[output_block,], out_uom='MWh')
          
      self.assertEqual(converted_mwh, 0)
      self.assertEqual(translated_mwh.loc[0, output_block], 0)

    for hour in off_peak_hours:
      print(f'testing input block {input_block} to output block {output_block} for hour {hour}...')
      test_date = test_date.replace(hour=hour)
      converted_mwh = elektra.convert(test_date, input_block, output_block)
      translated_mwh = elektra.translateBlocks(iso=iso, mw=1, frequency='daily', \
        contract_start=test_date, in_block=input_block, out_blocks=[output_block,], out_uom='MWh')
          
      self.assertEqual(converted_mwh, 1)
      self.assertEqual(translated_mwh.loc[0, output_block], 1)  

if __name__ == '__main__':
    unittest.main()