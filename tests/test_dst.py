import unittest
import datetime
import json
import pandas as pd
import elektra


class DstBegin2024Tests(unittest.TestCase):
    def setUp(self):
        self.flow_date = datetime.datetime(2024, 3, 10)
        self.ticker = 'E.4MYV.DADL9'
        self.node = 'ISONE MASS HUB'
        self.iso = 'isone'
        self.frequency = 'daily'
        self.consecutive_dst_begin_prices = self.get_consecutive_dst_begin_prices()

    def get_consecutive_dst_begin_prices(self):
        with open('tests/consecutive_dst_begin_data.json') as f:
            data = json.loads(f.read())
        return pd.DataFrame(data['data'])

    def test_consecutive_dst_begin_prices_2x16(self):
        p = elektra.create_prices(
            flow_date=self.flow_date,
            ticker=self.ticker,
            node=self.node,
            iso=self.iso,
            block='2x16',
            frequency=self.frequency,
            input_prices=self.consecutive_dst_begin_prices
        )
        self.assertAlmostEqual(23.928750, p, places=6)

    def test_consecutive_dst_begin_prices_7x24(self):
        p = elektra.create_prices(
            flow_date=self.flow_date,
            ticker=self.ticker,
            node=self.node,
            iso=self.iso,
            block='7x24',
            frequency=self.frequency,
            input_prices=self.consecutive_dst_begin_prices
        )
        self.assertAlmostEqual(22.250870, p, places=6)

    def test_consecutive_dst_begin_prices_wrap(self):
        p = elektra.create_prices(
            flow_date=self.flow_date,
            ticker=self.ticker,
            node=self.node,
            iso=self.iso,
            block='wrap',
            frequency=self.frequency,
            input_prices=self.consecutive_dst_begin_prices
        )
        self.assertAlmostEqual(22.250870, p, places=6)

    def test_consecutive_dst_begin_prices_7x8(self):
        p = elektra.create_prices(
            flow_date=self.flow_date,
            ticker=self.ticker,
            node=self.node,
            iso=self.iso,
            block='7x8',
            frequency=self.frequency,
            input_prices=self.consecutive_dst_begin_prices
        )
        self.assertAlmostEqual(18.415714, p, places=6)