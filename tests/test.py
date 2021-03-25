import unittest
import elektra
import pandas as pd
import datetime as dt


class ElektraTests(unittest.TestCase):
  def test_hello_elektra(self):
    # simple test to verify tests are executing
    result = elektra.hello()
    self.assertEqual(result, 'elektra says hi')

  def test_create_price_method(self):
    # happy path test through the elektra create price method

    # create a panda from the test csv file
    prices = pd.read_csv('tests/created_prices.csv')

    # call the create prices method and compare results
    result = elektra.create_prices(dt.datetime.strptime('2020-10-17','%Y-%m-%d'),'M.P4F8', 'INDIANA.HUB', 'miso','2x16','Daily', prices)
    self.assertEqual(result,22.779374999999998)

  def test_scrub_price_method(self):
    # happy path test through the elektra scrub price method

    # create a panda from the test csv file
    prices = pd.read_csv('tests/scrub_hourly_prices.csv')

    # call the create prices method and compare results
    result = elektra.scrub_hourly_prices(dt.datetime.strptime('2020-10-17','%Y-%m-%d'),'M.YERX', '116013753', 'pjm', prices)
    self.assertTrue(result.to_csv,'test-data/scrub_hourly_prices_result.csv')

if __name__ == '__main__':
    unittest.main()